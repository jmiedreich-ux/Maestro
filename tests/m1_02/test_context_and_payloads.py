from __future__ import annotations

import copy
import unittest

from maestro.operational_state import (
    InvalidRecord,
    OperationalStateStore,
    SensitiveMaterialRejected,
    canonical_digest,
    canonical_json,
    context_policy_digest,
    preferred_measurement,
    validate_context_policy,
    validate_cost_measurement,
    validate_measurement,
    validate_payload,
)


NOW = "2026-09-02T12:00:00.000000Z"


def measurement(value, quality="RuntimeReported", confidence="Exact", source="runtime"):
    return {
        "value": value,
        "quality": quality,
        "confidence": confidence,
        "source_reference": source,
        "observed_at": NOW,
    }


class ContextPolicyTests(unittest.TestCase):
    def test_both_representative_policies_digest_arithmetic_and_fit(self) -> None:
        developer = {
            "minimum_context_tokens": 32768,
            "output_reserve_tokens": 8192,
            "warning_remaining_tokens": 16384,
            "checkpoint_remaining_tokens": 12288,
            "stop_remaining_tokens": 8192,
        }
        distinct = {
            "minimum_context_tokens": 24576,
            "output_reserve_tokens": 4096,
            "warning_remaining_tokens": 12288,
            "checkpoint_remaining_tokens": 8192,
            "stop_remaining_tokens": 4096,
        }
        self.assertEqual(
            validate_context_policy(developer, configured_context_limit=40960, starting_input_tokens=32768),
            developer,
        )
        self.assertEqual(
            validate_context_policy(distinct, configured_context_limit=28672, starting_input_tokens=24576),
            distinct,
        )
        self.assertEqual(len(context_policy_digest(developer)), 64)
        self.assertNotEqual(context_policy_digest(developer), context_policy_digest(distinct))

    def test_policy_shape_order_configured_sum_and_starting_fit_are_closed(self) -> None:
        policy = {
            "minimum_context_tokens": 32768,
            "output_reserve_tokens": 8192,
            "warning_remaining_tokens": 16384,
            "checkpoint_remaining_tokens": 12288,
            "stop_remaining_tokens": 8192,
        }
        invalid = []
        extra = {**policy, "default": 1}
        invalid.append((extra, 40960, 1))
        unordered = {**policy, "checkpoint_remaining_tokens": 16384}
        invalid.append((unordered, 40960, 1))
        invalid.append((policy, 40959, 1))
        invalid.append((policy, 40960, 32769))
        for value, configured, start in invalid:
            with self.subTest(value=value, configured=configured, start=start), self.assertRaises(InvalidRecord):
                validate_context_policy(value, configured_context_limit=configured, starting_input_tokens=start)


class PayloadTests(unittest.TestCase):
    def test_every_closed_payload_variant_accepts_exact_fields(self) -> None:
        payloads = [
            {"kind": "state", "entity_type": "Packet", "entity_id": "packet-1", "state": "Planned", "version": 1},
            {"kind": "claim", "packet_id": "packet-1", "lease_id": "lease-1", "lock_ids": ["lock-a", "lock-b"]},
            {"kind": "reference", "provider": "secret-provider", "reference_name": "GITHUB_APP_PRIVATE_KEY"},
            {"kind": "evidence-reference", "evidence_id": "evidence-1", "digest": "a" * 64, "source_reference": "source-1"},
            {"kind": "measurement-reference", "record_id": "usage-1", "measurement_kind": "tokens"},
            {"kind": "redacted-text", "text": "the password gate passed", "redaction_status": "Redacted", "redaction_receipt_reference": "receipt-1"},
            {"kind": "notification", "event_id": 1, "audience": "ProjectArchitect", "severity": "ActionNeeded", "subject_reference": "packet-1", "evidence_references": ["evidence-1"], "next_action_reference": "review"},
            {"kind": "reason", "reason_code": "WAITING", "detail_reference": None},
        ]
        for payload in payloads:
            with self.subTest(kind=payload["kind"]):
                self.assertEqual(validate_payload(payload), payload)
                self.assertEqual(len(canonical_digest(payload)), 64)

    def test_arbitrary_roots_extra_raw_fields_and_unsorted_sets_are_rejected(self) -> None:
        invalid = [
            [],
            {"kind": "unknown"},
            {"kind": "reason", "reason_code": "X", "detail_reference": None, "trace": "raw"},
            {"kind": "claim", "packet_id": "p", "lease_id": "l", "lock_ids": ["z", "a"]},
            {"kind": "redacted-text", "text": "x", "redaction_status": "NotRequired", "redaction_receipt_reference": "r"},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(InvalidRecord):
                validate_payload(payload)  # type: ignore[arg-type]

    def test_json_size_float_control_and_timestamp_boundaries_are_rejected(self) -> None:
        with self.assertRaises(InvalidRecord):
            canonical_json({"value": float("nan")})
        self.assertEqual(canonical_json({"value": 1.5}), '{"value":1.5}')
        with self.assertRaises(InvalidRecord):
            validate_payload({
                "kind": "redacted-text", "text": "x" * (1024 * 1024),
                "redaction_status": "Redacted", "redaction_receipt_reference": "receipt",
            })
        with self.assertRaises(InvalidRecord):
            validate_payload({
                "kind": "state", "entity_type": "Packet", "entity_id": "bad\x00id",
                "state": "Planned", "version": 1,
            })
        invalid_time = measurement(1)
        invalid_time["observed_at"] = "2026-09-02T12:00:00Z"
        with self.assertRaises(InvalidRecord):
            validate_measurement(invalid_time)

    def test_reference_grammar_rejects_common_value_carriers_without_prose_heuristics(self) -> None:
        for reference in (
            "ghp_abcdefghijklmnopqrstuvwxyz", "github_pat_value", "xoxb-value",
            "Bearer value", "session=cookie", "-----BEGIN_PRIVATE_KEY",
        ):
            with self.subTest(reference=reference), self.assertRaises(SensitiveMaterialRejected):
                validate_payload({"kind": "reference", "provider": "slack", "reference_name": reference})
        accepted = validate_payload({
            "kind": "redacted-text",
            "text": "token key password are ordinary redacted prose words",
            "redaction_status": "Redacted",
            "redaction_receipt_reference": "receipt-2",
        })
        self.assertEqual(accepted["text"], "token key password are ordinary redacted prose words")


class MeasurementTests(unittest.TestCase):
    def test_token_measurement_quality_source_and_runtime_precedence(self) -> None:
        runtime = measurement(100)
        self.assertEqual(validate_measurement(runtime), runtime)
        unavailable = measurement(None, "Unavailable", "Unavailable", None)
        self.assertEqual(validate_measurement(unavailable), unavailable)
        estimated = measurement(99, "Estimated", "Medium", "estimator")
        with self.assertRaises(InvalidRecord):
            preferred_measurement(runtime, estimated)
        self.assertEqual(preferred_measurement(estimated, runtime), runtime)

        invalid = copy.deepcopy(unavailable)
        invalid["value"] = 0
        with self.assertRaises(InvalidRecord):
            validate_measurement(invalid)
        invalid = measurement(2, "TokenizerCounted", "Low", "tokenizer:model")
        with self.assertRaises(InvalidRecord):
            validate_measurement(invalid)

    def test_cost_shapes_keep_unknown_and_not_billed_distinct_from_zero(self) -> None:
        values = [
            {"status": "Billed", "amount": "1.25", "currency": "USD", "quality": "ProviderReported", "confidence": "Exact", "source_reference": "provider-bill", "observed_at": NOW},
            {"status": "Estimated", "amount": "0", "currency": "USD", "quality": "Estimated", "confidence": "Medium", "source_reference": "estimate", "observed_at": NOW},
            {"status": "NotBilled", "amount": None, "currency": None, "quality": "RuntimeReported", "confidence": "Exact", "source_reference": "local-runtime", "observed_at": NOW},
            {"status": "Unknown", "amount": None, "currency": None, "quality": "Unavailable", "confidence": "Unavailable", "source_reference": None, "observed_at": NOW},
        ]
        for value in values:
            self.assertEqual(validate_cost_measurement(value), value)
        changed = dict(values[-1], amount="0")
        with self.assertRaises(InvalidRecord):
            validate_cost_measurement(changed)
        noncanonical = dict(values[0], amount="1.250")
        with self.assertRaises(InvalidRecord):
            validate_cost_measurement(noncanonical)

    def test_allowance_and_exact_decimal_reconciliation_validation(self) -> None:
        unavailable = {
            "allowance_observation_id": "allowance-unavailable", "provider": "openai",
            "account_reference": "account-ref", "native_window_type": "weekly-native",
            "used_value": None, "remaining_value": None, "native_unit": None, "reset_at": None,
            "precision": "Unavailable", "measurement_quality": "Unavailable",
            "freshness": "Unavailable", "observed_at": NOW,
        }
        self.assertEqual(OperationalStateStore._allowance(unavailable), unavailable)
        with self.assertRaises(InvalidRecord):
            OperationalStateStore._allowance(dict(unavailable, remaining_value="0"))

        balanced = {
            "usage_reconciliation_id": "recon-1", "allowance_observation_id": "allowance-1",
            "window_change_value": "10.5", "tracked_controlled_value": "4",
            "registered_coarse_value": "5", "unattributed_value": "1.5",
            "native_unit": "requests", "measurement_quality": "Exact", "observed_at": NOW,
        }
        self.assertEqual(OperationalStateStore._reconciliation(balanced), balanced)
        with self.assertRaises(InvalidRecord):
            OperationalStateStore._reconciliation(dict(balanced, unattributed_value="1.4"))


if __name__ == "__main__":
    unittest.main()
