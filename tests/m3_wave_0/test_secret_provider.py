from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.secrets import (
    PROVIDER_NAME,
    LocalFileSecretProvider,
    SecretProviderError,
    secret_reference_observation,
)


class Runtime:
    """Matches tests/m1_02/test_schema_and_records.py's own helper exactly,
    so this slice's tests share the same real-var/-directory discipline."""

    def __init__(self):
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = Path(self._temporary.name) / "runtime"

    def config(self):
        return RuntimeConfig(self.path)

    def close(self):
        self._temporary.cleanup()


class LocalFileSecretProviderTests(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()
        self.provider = LocalFileSecretProvider(self.runtime.config())

    def tearDown(self):
        self.runtime.close()

    def test_store_then_resolve_round_trips_the_real_value(self):
        self.provider.store("GITHUB_APP_PRIVATE_KEY", "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n")
        self.assertEqual(
            self.provider.resolve("GITHUB_APP_PRIVATE_KEY"),
            "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n",
        )

    def test_stored_file_is_mode_0600_on_disk(self):
        self.provider.store("GITHUB_APP_PRIVATE_KEY", "secret-value")
        secret_path = self.runtime.path / "secrets" / "GITHUB_APP_PRIVATE_KEY"
        self.assertTrue(secret_path.is_file())
        mode_bits = stat.S_IMODE(secret_path.stat().st_mode)
        self.assertEqual(mode_bits, 0o600)

    def test_resolve_missing_reference_raises(self):
        with self.assertRaises(SecretProviderError):
            self.provider.resolve("NEVER_STORED")

    def test_store_rejects_reference_name_outside_closed_grammar(self):
        with self.assertRaises(SecretProviderError):
            self.provider.store("lowercase-not-allowed", "value")

    def test_store_rejects_empty_value(self):
        with self.assertRaises(SecretProviderError):
            self.provider.store("SOME_REFERENCE", "")

    def test_resolve_refuses_a_symlinked_secret_file(self):
        secrets_dir = self.runtime.path / "secrets"
        secrets_dir.mkdir(parents=True)
        real_target = self.runtime.path.parent / "outside-secret.txt"
        real_target.write_text("exfiltrated")
        (secrets_dir / "SYMLINKED_REFERENCE").symlink_to(real_target)
        with self.assertRaises(SecretProviderError):
            self.provider.resolve("SYMLINKED_REFERENCE")

    def test_resolve_refuses_a_secret_file_with_loosened_permissions(self):
        self.provider.store("LOOSENED_REFERENCE", "value")
        secret_path = self.runtime.path / "secrets" / "LOOSENED_REFERENCE"
        os.chmod(secret_path, 0o644)
        with self.assertRaises(SecretProviderError):
            self.provider.resolve("LOOSENED_REFERENCE")

    def test_store_overwrites_an_existing_reference_for_rotation(self):
        self.provider.store("ROTATING_REFERENCE", "old-value")
        self.provider.store("ROTATING_REFERENCE", "new-value")
        self.assertEqual(self.provider.resolve("ROTATING_REFERENCE"), "new-value")

    def test_store_overwrite_restores_mode_0600_even_if_it_had_been_loosened(self):
        self.provider.store("RESTORED_REFERENCE", "old-value")
        secret_path = self.runtime.path / "secrets" / "RESTORED_REFERENCE"
        os.chmod(secret_path, 0o644)
        self.provider.store("RESTORED_REFERENCE", "new-value")
        mode_bits = stat.S_IMODE(secret_path.stat().st_mode)
        self.assertEqual(mode_bits, 0o600)


class SecretReferenceObservationBuilderTests(unittest.TestCase):
    def test_builds_the_exact_row_shape_record_secret_reference_expects(self):
        row = secret_reference_observation(
            secret_reference_observation_id="secret-observation-1",
            project_id="project-1",
            binding_id="binding-1",
            reference_name="GITHUB_APP_PRIVATE_KEY",
            owner_reference="owner-policy-1",
            observed_at="2026-09-06T12:00:00.000000Z",
        )
        self.assertEqual(
            row,
            {
                "secret_reference_observation_id": "secret-observation-1",
                "project_id": "project-1",
                "binding_id": "binding-1",
                "provider": PROVIDER_NAME,
                "reference_name": "GITHUB_APP_PRIVATE_KEY",
                "owner_reference": "owner-policy-1",
                "rotation_at": None,
                "expires_at": None,
                "status": "Active",
                "observed_at": "2026-09-06T12:00:00.000000Z",
            },
        )


if __name__ == "__main__":
    unittest.main()
