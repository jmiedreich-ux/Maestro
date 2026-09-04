from __future__ import annotations

import copy
import json
import math
import re
import unittest

from maestro import operational_state as state
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


class ClosedValidatorManifestTests(unittest.TestCase):
    def assert_closed_error(self, error_type, message, command):
        with self.assertRaisesRegex(error_type, f"^{re.escape(message)}$"):
            command()

    def test_ar_p04_app_v01_through_v16_positive_negative_and_canonical_edges(self) -> None:
        self.assertEqual(state._closed_mapping({"a": 1}, {"a"}, "value"), {"a": 1})
        self.assert_closed_error(InvalidRecord, "value has an invalid closed shape", lambda: state._closed_mapping({"a": 1, "b": 2}, {"a"}, "value"))

        self.assertEqual(state._text("é" * 256, "field"), "é" * 256)
        self.assert_closed_error(InvalidRecord, "field must be non-empty UTF-8 text up to 512 bytes", lambda: state._text("x" * 513, "field"))
        self.assert_closed_error(InvalidRecord, "field contains a control character", lambda: state._text("bad\x00", "field"))
        self.assertIsNone(state._optional_text(None, "field"))
        self.assert_closed_error(InvalidRecord, "field must be non-empty UTF-8 text up to 512 bytes", lambda: state._optional_text("", "field"))

        self.assertEqual(state._commit("a" * 40, "commit"), "a" * 40)
        self.assert_closed_error(InvalidRecord, "commit must be a lowercase full Git commit", lambda: state._commit("A" * 40, "commit"))
        self.assertEqual(state._digest("a" * 64, "digest"), "a" * 64)
        self.assert_closed_error(InvalidRecord, "digest must be a lowercase SHA-256 digest", lambda: state._digest("A" * 64, "digest"))

        self.assertEqual(state._provider("openai-api"), "openai-api")
        self.assert_closed_error(state.SensitiveMaterialRejected, "provider must match the closed non-secret grammar", lambda: state._provider("OpenAI"))
        self.assertEqual(state._reference_name("GITHUB_APP_PRIVATE_KEY"), "GITHUB_APP_PRIVATE_KEY")
        self.assert_closed_error(state.SensitiveMaterialRejected, "reference_name must match the closed non-secret grammar", lambda: state._reference_name("ghp_secret-carrier"))

        self.assertEqual(state._timestamp(NOW, "time"), NOW)
        self.assert_closed_error(InvalidRecord, "time must be a canonical UTC timestamp", lambda: state._timestamp("2026-09-02T12:00:00Z", "time"))
        self.assertIsNone(state._optional_timestamp(None, "time"))
        self.assert_closed_error(InvalidRecord, "time must be a valid UTC timestamp", lambda: state._optional_timestamp("2026-99-99T12:00:00.000000Z", "time"))

        self.assertEqual(state._positive_int(1, "count"), 1)
        self.assert_closed_error(InvalidRecord, "count must be a positive integer", lambda: state._positive_int(True, "count"))
        self.assertEqual(state._nonnegative_int(0, "count"), 0)
        self.assert_closed_error(InvalidRecord, "count must be a non-negative integer", lambda: state._nonnegative_int(False, "count"))
        self.assertEqual(state._sorted_unique_text(["a", "b"], "items"), ["a", "b"])
        self.assert_closed_error(InvalidRecord, "items must be sorted and unique", lambda: state._sorted_unique_text(["b", "a"], "items"))

        canonical = {"array": [1, True, None], "object": {"é": 1}}
        self.assertEqual(canonical_json(canonical), '{"array":[1,true,null],"object":{"é":1}}')
        json_failures = (
            ("JSON root has the wrong type", lambda: state.canonical_json([], root_type=dict), InvalidRecord),
            ("JSON object keys must be strings", lambda: state.canonical_json({1: "bad"}), InvalidRecord),
            ("unsupported JSON value type", lambda: state.canonical_json({"value": object()}), InvalidRecord),
            ("NaN and infinity are not canonical operational facts", lambda: state.canonical_json({"value": math.inf}), InvalidRecord),
            ("structured sensitive/raw field is rejected", lambda: state.canonical_json({"secret": "x"}), state.SensitiveMaterialRejected),
            ("value is not canonical JSON", lambda: state.canonical_json({"value": "\ud800"}), InvalidRecord),
            ("canonical JSON exceeds the one MiB row limit", lambda: state.canonical_json({"value": "x" * (1024 * 1024)}), InvalidRecord),
        )
        for message, command, error_type in json_failures:
            with self.subTest(case="APP-V13", message=message):
                self.assert_closed_error(error_type, message, command)
        self.assertEqual(state._json_object({"a": 1}, "object"), {"a": 1})
        self.assert_closed_error(InvalidRecord, "object must be an object", lambda: state._json_object([], "object"))
        self.assertEqual(state._decimal_text("0", "decimal"), "0")
        self.assertEqual(state._decimal_text("1.25", "decimal"), "1.25")
        self.assert_closed_error(InvalidRecord, "decimal is not normalized", lambda: state._decimal_text("1.250", "decimal"))

        policy = {
            "minimum_context_tokens": 32768, "output_reserve_tokens": 8192,
            "warning_remaining_tokens": 16384, "checkpoint_remaining_tokens": 12288,
            "stop_remaining_tokens": 8192,
        }
        self.assertEqual(validate_context_policy(policy, configured_context_limit=40960, starting_input_tokens=32768), policy)
        policy_failures = (
            (dict(policy, extra=1), 40960, 32768, "context policy has an invalid closed shape"),
            (dict(policy, stop_remaining_tokens=0), 40960, 32768, "stop_remaining_tokens must be a positive integer"),
            (dict(policy, checkpoint_remaining_tokens=16384), 40960, 32768, "context policy thresholds are not strictly ordered"),
            (policy, 40959, 32768, "configured context limit does not satisfy the materialized policy"),
            (policy, 40960, 32769, "starting input plus output reserve does not fit"),
        )
        for value, configured, starting, message in policy_failures:
            with self.subTest(case="APP-V16", message=message):
                self.assert_closed_error(InvalidRecord, message, lambda value=value, configured=configured, starting=starting: validate_context_policy(value, configured_context_limit=configured, starting_input_tokens=starting))

    def test_ar_p04_app_v17_through_v22_positive_negative_and_canonical_edges(self) -> None:
        payloads = (
            {"kind": "state", "entity_type": "Packet", "entity_id": "packet-1", "state": "Planned", "version": 1},
            {"kind": "claim", "packet_id": "packet-1", "lease_id": "lease-1", "lock_ids": ["lock-a"]},
            {"kind": "reference", "provider": "openai", "reference_name": "API_KEY_REFERENCE"},
            {"kind": "evidence-reference", "evidence_id": "evidence-1", "digest": "a" * 64, "source_reference": None},
            {"kind": "measurement-reference", "record_id": "usage-1", "measurement_kind": "tokens"},
            {"kind": "redacted-text", "text": "safe", "redaction_status": "Redacted", "redaction_receipt_reference": "receipt-1"},
            {"kind": "notification", "event_id": 1, "audience": "ProjectArchitect", "severity": "ActionNeeded", "subject_reference": "packet-1", "evidence_references": [], "next_action_reference": "review"},
            {"kind": "reason", "reason_code": "READY", "detail_reference": None},
        )
        for payload in payloads:
            with self.subTest(case="APP-V17", kind=payload["kind"]):
                self.assertEqual(validate_payload(payload), payload)
                self.assertEqual(json.loads(canonical_json(payload)), payload)
        self.assert_closed_error(InvalidRecord, "reason payload has an invalid closed shape", lambda: validate_payload({**payloads[-1], "extra": True}))

        exact = measurement(0)
        unavailable = measurement(None, "Unavailable", "Unavailable", None)
        self.assertEqual(validate_measurement(exact), exact)
        self.assertEqual(validate_measurement(unavailable), unavailable)
        self.assert_closed_error(InvalidRecord, "unavailable measurement must retain null value/source", lambda: validate_measurement(dict(unavailable, value=0)))
        self.assert_closed_error(InvalidRecord, "reported/tokenizer measurement requires exact or high confidence", lambda: validate_measurement(measurement(1, "TokenizerCounted", "Low", "tokenizer")))

        costs = (
            {"status": "Billed", "amount": "1.25", "currency": "USD", "quality": "ProviderReported", "confidence": "Exact", "source_reference": "bill", "observed_at": NOW},
            {"status": "Estimated", "amount": "0", "currency": "USD", "quality": "Estimated", "confidence": "Medium", "source_reference": "estimate", "observed_at": NOW},
            {"status": "NotBilled", "amount": None, "currency": None, "quality": "RuntimeReported", "confidence": "High", "source_reference": "runtime", "observed_at": NOW},
            {"status": "Unknown", "amount": None, "currency": None, "quality": "Unavailable", "confidence": "Unavailable", "source_reference": None, "observed_at": NOW},
        )
        for cost in costs:
            self.assertEqual(validate_cost_measurement(cost), cost)
        self.assert_closed_error(InvalidRecord, "unknown cost retains no amount, currency, or source", lambda: validate_cost_measurement(dict(costs[-1], amount="0")))

        estimated = measurement(1, "Estimated", "Medium", "estimate")
        runtime = measurement(2)
        self.assertEqual(preferred_measurement(estimated, runtime), runtime)
        self.assert_closed_error(InvalidRecord, "lower-quality measurement cannot replace the retained value", lambda: preferred_measurement(runtime, estimated))
        tokens = {name: measurement(index) for index, name in enumerate(("input", "output", "cached_input", "reasoning", "total"), start=1)}
        self.assertEqual(state._token_measurements(tokens), {name: tokens[name] for name in sorted(tokens)})
        self.assert_closed_error(InvalidRecord, "token measurements has an invalid closed shape", lambda: state._token_measurements({name: value for name, value in tokens.items() if name != "total"}))

        actor = {"actor_type": "Developer", "actor_id": "developer-1", "correlation_id": "correlation-1", "causation_event_id": 1}
        self.assertEqual(state._actor(actor), actor)
        self.assert_closed_error(InvalidRecord, "actor has an invalid closed shape", lambda: state._actor({**actor, "extra": True}))
        self.assert_closed_error(InvalidRecord, "causation_event_id must be a positive integer", lambda: state._actor(dict(actor, causation_event_id=0)))


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

    def test_runtime_precedes_tokenizer_and_estimate_for_every_token_category(self) -> None:
        for index, category in enumerate(
            ("input", "output", "cached_input", "reasoning", "total"), start=1
        ):
            runtime = measurement(index * 100, "RuntimeReported", "Exact", "runtime:counters")
            tokenizer = measurement(
                index * 90, "TokenizerCounted", "High", "tokenizer:gpt-5"
            )
            estimated = measurement(
                index * 80, "Estimated", "Medium", "estimate:bounded"
            )
            with self.subTest(category=category, quality="TokenizerCounted"):
                self.assertEqual(validate_measurement(tokenizer), tokenizer)
                self.assertEqual(preferred_measurement(tokenizer, runtime), runtime)
                with self.assertRaises(InvalidRecord):
                    preferred_measurement(runtime, tokenizer)
            with self.subTest(category=category, quality="Estimated"):
                self.assertEqual(validate_measurement(estimated), estimated)
                self.assertEqual(preferred_measurement(estimated, runtime), runtime)
                with self.assertRaises(InvalidRecord):
                    preferred_measurement(runtime, estimated)
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
