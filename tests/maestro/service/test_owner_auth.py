from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from maestro.foundation import Command, Database, Event, StorageSettings
from maestro.service import (
    AuthenticationConfigurationError,
    CredentialProtectionError,
    HTTPRejection,
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    owner_authorization_header,
    token_digest,
)


FIRST_TOKEN = "1" * 64
REPLACEMENT_TOKEN = "2" * 64


def settings(token: str, owner_id: str = "owner-local") -> OwnerAuthenticationSettings:
    return OwnerAuthenticationSettings(owner_id=owner_id, token_sha256=token_digest(token))


def bearer(token: str) -> str:
    return f"Bearer {token}"


class OwnerAuthenticationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.authenticator = OwnerAuthenticator(settings(FIRST_TOKEN))

    def test_verified_owner_overrides_body_identity_at_real_persistence_boundary(self) -> None:
        body = {"actor_id": "spoofed-owner", "value": "saved"}
        actor = self.authenticator.authenticate_write(bearer(FIRST_TOKEN))

        with tempfile.TemporaryDirectory() as temporary:
            database = Database(StorageSettings(path=Path(temporary) / "maestro.sqlite3"))
            command = Command(
                request_id="request-one",
                operation="sample.write",
                actor_id=actor.actor_id,
                entity_id="sample-one",
                expected_version=0,
                content_digest=hashlib.sha256(b"sample-body").hexdigest(),
            )
            event = Event(
                schema_version=1,
                event_id="event-one",
                occurred_at="2026-09-17T12:34:56.000000Z",
                type="sample.saved",
                data={"value": body["value"]},
            )
            database.commit_command(command, event, lambda transaction, version: version)

            self.authenticator.replace_settings(settings(REPLACEMENT_TOKEN, "owner-local"))
            with self.assertRaises(HTTPRejection) as rejected:
                self.authenticator.authenticate_read(bearer(FIRST_TOKEN))
            replacement_actor = self.authenticator.authenticate_write(
                bearer(REPLACEMENT_TOKEN)
            )

            with database.read_connection() as connection:
                saved_actor = connection.execute(
                    "SELECT actor_id FROM request_receipts WHERE request_id = ?",
                    ("request-one",),
                ).fetchone()[0]
                saved_event = connection.execute(
                    "SELECT data_json FROM outbox_events WHERE event_id = ?",
                    ("event-one",),
                ).fetchone()[0]

        self.assertEqual("owner-local", saved_actor)
        self.assertNotEqual(body["actor_id"], saved_actor)
        self.assertEqual(401, rejected.exception.status_code)
        self.assertEqual(actor, replacement_actor)
        self.assertNotIn(FIRST_TOKEN, repr(actor))
        self.assertNotIn(FIRST_TOKEN, repr(command))
        self.assertNotIn(FIRST_TOKEN, saved_event)

    def test_missing_malformed_and_wrong_tokens_are_401_without_secret_output(self) -> None:
        supplied = (None, "", "Basic abc", "Bearer NOT-HEX", bearer(REPLACEMENT_TOKEN))
        for authorization in supplied:
            with self.subTest(authorization=authorization):
                with self.assertRaises(HTTPRejection) as rejected:
                    self.authenticator.authenticate_read(authorization)
                error = rejected.exception
                rendered = json.dumps(error.as_body()) + repr(error) + json.dumps(dict(error.headers))
                self.assertEqual(401, error.status_code)
                self.assertEqual("Bearer", error.headers["WWW-Authenticate"])
                self.assertNotIn(FIRST_TOKEN, rendered)
                self.assertNotIn(REPLACEMENT_TOKEN, rendered)

    def test_valid_credential_with_wrong_authority_is_403(self) -> None:
        with self.assertRaises(HTTPRejection) as rejected:
            self.authenticator.authenticate(
                bearer(FIRST_TOKEN), required_authority="MaestroDeveloper"
            )

        self.assertEqual(403, rejected.exception.status_code)
        self.assertEqual({}, dict(rejected.exception.headers))
        self.assertNotIn(FIRST_TOKEN, repr(rejected.exception))

    def test_reads_and_writes_are_both_protected(self) -> None:
        read_actor = self.authenticator.authenticate_read(bearer(FIRST_TOKEN))
        write_actor = self.authenticator.authenticate_write(bearer(FIRST_TOKEN))
        self.assertEqual(read_actor, write_actor)

        for operation in (
            self.authenticator.authenticate_read,
            self.authenticator.authenticate_write,
        ):
            with self.assertRaises(HTTPRejection) as rejected:
                operation(None)
            self.assertEqual(401, rejected.exception.status_code)

    def test_redirect_and_other_origins_never_receive_owner_header(self) -> None:
        configured = "http://127.0.0.1:8787"
        direct = owner_authorization_header(
            FIRST_TOKEN,
            destination="http://127.0.0.1:8787/api/v1/projects",
            configured_service_url=configured,
        )
        self.assertEqual(bearer(FIRST_TOKEN), direct["Authorization"])

        unsafe = (
            {
                "destination": "http://127.0.0.1:8787/api/v1/projects",
                "redirected": True,
            },
            {"destination": "http://localhost:8787/api/v1/projects"},
            {"destination": "https://127.0.0.1:8787/api/v1/projects"},
            {"destination": "http://example.test:8787/api/v1/projects"},
        )
        for case in unsafe:
            with self.subTest(case=case):
                with self.assertRaises(CredentialProtectionError) as rejected:
                    owner_authorization_header(
                        FIRST_TOKEN,
                        configured_service_url=configured,
                        **case,
                    )
                self.assertNotIn(FIRST_TOKEN, repr(rejected.exception))

    def test_configuration_rejects_noncanonical_values(self) -> None:
        with self.assertRaises(AuthenticationConfigurationError):
            OwnerAuthenticationSettings.from_mapping(
                {"id": "owner-local", "token_sha256": "not-a-digest"}
            )
        with self.assertRaises(AuthenticationConfigurationError):
            OwnerAuthenticationSettings.from_mapping(
                {
                    "id": "owner-local",
                    "token_sha256": token_digest(FIRST_TOKEN),
                    "plaintext_token": FIRST_TOKEN,
                }
            )


if __name__ == "__main__":
    unittest.main()
