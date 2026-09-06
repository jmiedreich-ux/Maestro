from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.operational_state import Actor, OperationalStateStore
from maestro.secrets import LocalFileSecretProvider, secret_reference_observation


class Runtime:
    def __init__(self):
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = Path(self._temporary.name) / "runtime"

    def config(self):
        return RuntimeConfig(self.path)

    def close(self):
        self._temporary.cleanup()


ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
NOW = "2026-09-06T12:00:00.000000Z"


class SecretProviderWiredToOperationalStateTests(unittest.TestCase):
    """Proves W0.1 actually closes the loop the M3 Decision Fidelity check
    found open: a real value stored by LocalFileSecretProvider, observed
    for real through OperationalStateStore.record_secret_reference — the
    already-existing, previously-uncalled M1 command."""

    def setUp(self):
        self.runtime = Runtime()
        self.store = OperationalStateStore(self.runtime.config())
        self.store.health()
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO projects(project_id,repository_identity,default_branch,adapter_version,process_version,registration_state) "
                "VALUES ('project-foundry','jmiedreich-ux/Foundry','main','adapter-v1','process-v1','Candidate')"
            )
            connection.execute(
                "INSERT INTO project_bindings(binding_id,project_id,binding_revision,source_commit,manifest_digest,"
                "adapter_version,process_version,authority_reference,merge_policy,acceptance_authority,"
                "merge_execution_authority,merge_delegation_reference,binding_json,state,activated_at,superseded_at,created_at) "
                "VALUES ('binding-foundry','project-foundry','revision-1','" + "a" * 40 + "','" + "a" * 64 + "',"
                "'adapter-v1','process-v1','authority-1','no-automatic-merge','ProjectArchitect',"
                "'OwnerPerformed',NULL,'{}','Candidate',NULL,NULL,'" + NOW + "')"
            )
            connection.commit()
        self.provider = LocalFileSecretProvider(self.runtime.config())

    def tearDown(self):
        self.runtime.close()

    def test_stored_secret_is_recorded_as_an_active_observation(self):
        self.provider.store("GITHUB_APP_PRIVATE_KEY", "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n")

        observation = secret_reference_observation(
            secret_reference_observation_id="secret-observation-foundry-1",
            project_id="project-foundry",
            binding_id="binding-foundry",
            reference_name="GITHUB_APP_PRIVATE_KEY",
            owner_reference="foundry-github-app-4746601",
            observed_at=NOW,
        )
        recorded = self.store.record_secret_reference(
            observation, "command-secret-foundry-1", ACTOR, NOW
        )

        self.assertEqual(recorded["status"], "Active")
        self.assertEqual(recorded["provider"], "local-file")
        # The database only ever holds the reference, never the value.
        self.assertNotIn("-----BEGIN RSA PRIVATE KEY-----", str(recorded))

        # And the real value is genuinely retrievable through the provider,
        # by the same reference_name the observation recorded.
        self.assertEqual(
            self.provider.resolve(recorded["reference_name"]),
            "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n",
        )


if __name__ == "__main__":
    unittest.main()
