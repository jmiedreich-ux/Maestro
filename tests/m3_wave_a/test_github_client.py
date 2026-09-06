from __future__ import annotations

import base64
import json
import unittest
import urllib.error
from io import BytesIO
from unittest import mock

from maestro.github_client import (
    GitHubAppCredentials,
    GitHubClientError,
    fetch_file_content,
    fetch_installation_token,
    fetch_repository_metadata,
)

# A real (throwaway, test-only) RSA key pair, generated once for this test
# module so fetch_installation_token exercises real RS256 signing rather
# than a mocked jwt.encode call. Not used for anything but these tests.
_REAL_TEST_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAjL9sbo4mXc2QSUcAZ1JLJ7BGB0dTBREg8nwQD8IJu5wWiQye
cp9dn85kqk/uoVN5s/XshMxfk4iuHrMe6p4qko1wtEceP41cur1GIlTXCNpB7zbD
tNdmE4qQbDRZFHglQ5tlb1O5pfG+P0qDIjfjaKmEdwYY62HRvxrS6HoWy23zv7/q
Wl+lIgHT9iW3qPW4pX+XHOpeGHCoS0EDrqixKyDXBQ2m0xR2EA3fZisM5s1ZdnpF
ngI4MBNsiXIPrrZbyHC/UuR+/TIw7aygvWE6W+fY2Fx5TyM6Q38lvBWRmtVw3nml
SYgwYHOuolzKwBJ24LQTXNJEgC1+PeAED1bmIQIDAQABAoIBAAqbrOUCQsMEKNFV
ECM5cR+rKgQHbKrvmQ+dqSo+4jPpNkubD2AtQcW3LSAnCSHQpFYbfXme279HaHQ4
5OYjCKtmDK4RxCZfFbOfa2dQBKsOpDSO6J47M97aLTtykJo52fkn/7Ot2Eq5FzE3
AP41vyaWzDyaUYuAImpob6gE963aXY0lesYE7VZ2wyk/beZmAwZMuMKPM517igzY
VNUP5f4vYF9zBvoJICjgkAXzAoz+OqZ+NP5yPrDIKTcdILvOLCnHr7TKJ7ZaJASB
9u6ke8xBkgMFc57oj77f1WbcbcZBuz+VUlRwvzAGlQsT1ZOdnhMVxi8w5dserXQM
M0NRTKECgYEAvgHlJ0j/DTJIMqbN+Ma5lxMCKu7VmJNYjUG0jqEFLzf2S0iBIfE6
/yjMATLqRlaC0h2xuZHeXT1O1wi5iQ33LL3fm7in9hMunC7Oo5Llel/6SETPI1Iy
hxjvReuabFMAEl662Htd1vUOUTBIpww9f/UeJWR7xZTFmtyE9KKGSLkCgYEAvaG1
+AkF02NEukOgCWuHiydgXtHomxcBYLLtAH/n0BnPYQOb6mHiDsGycQ08crUMRuNn
AlW44ISx3+LqVvNP8EFUgIecn0bylqfOFMSEluyymPe1uk6BtEIJHAcDDiFTXE5T
FPYEOUxqT5l5PwSYKVZov4+KCRBUtVidaKT+BKkCgYEAskbu7oxUGtqp2TSfH6O9
8Nz59LSBHxZpSKh0tDqqtaIpanuOBf3kYBK0Tw+ptvNm7aTE45vU6uEiPyrFgq3i
1E0XKHH6zi0zV4GnitzCia7SE8rUG4z9MbsYjh9AlhDOiW3unD4sTwtBMrY+BNa8
QXoIngcJBtrPCb2M1khD/KkCgYA+7NFITB4txgwBTv1lAtSIfXmCHV91T036u4Tf
nJHcwSPKinsLbI2p3eaLkxvS6Hb5cu40nSNrBT1NEKw4TCbjj5otyFJVnCJVkbtV
stxYhJTDI7ee6fwqR5tkPINsBez2fVseYoCGTvAcF85e9fRUC0NZBZWFanDheFVL
ayyLeQKBgBxUfwop66pv5Q9yBWahqSp+AJlBROwlsISMQTSgI23A2F7Yykrrom6s
qzra4bPwrLxW8HORI1d7U2tb0JFlddPyuP0Rr+XZSyCr0m9I0QP03aS+0WKUFOkC
MajsXUdYnpH2fRxmy1b9LkqOKcxxCDI4mKBC/3dOsRVwbwpNuvoe
-----END RSA PRIVATE KEY-----"""


def _fake_http_response(payload: dict) -> mock.MagicMock:
    response = mock.MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class FetchInstallationTokenTests(unittest.TestCase):
    def test_returns_the_real_token_field_from_a_successful_exchange(self):
        credentials = GitHubAppCredentials(
            app_id="4746601", installation_id="157167451", private_key_pem=_REAL_TEST_KEY
        )
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_http_response(
                {"token": "ghs_realtoken123", "expires_at": "2026-09-06T16:50:07Z"}
            )
            token = fetch_installation_token(credentials, now=1_800_000_000)
        self.assertEqual(token, "ghs_realtoken123")
        called_request = urlopen.call_args[0][0]
        self.assertEqual(
            called_request.full_url,
            "https://api.github.com/app/installations/157167451/access_tokens",
        )
        self.assertTrue(called_request.headers["Authorization"].startswith("Bearer "))

    def test_raises_when_the_response_has_no_real_token_field(self):
        credentials = GitHubAppCredentials(
            app_id="4746601", installation_id="157167451", private_key_pem=_REAL_TEST_KEY
        )
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_http_response({"unexpected": "shape"})
            with self.assertRaises(GitHubClientError):
                fetch_installation_token(credentials, now=1_800_000_000)


class FetchRepositoryMetadataTests(unittest.TestCase):
    def test_returns_the_real_metadata_object(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_http_response(
                {"full_name": "jmiedreich-ux/Foundry", "default_branch": "main", "private": False}
            )
            metadata = fetch_repository_metadata("ghs_token", "jmiedreich-ux", "Foundry")
        self.assertEqual(metadata["full_name"], "jmiedreich-ux/Foundry")
        self.assertEqual(metadata["default_branch"], "main")


class FetchFileContentTests(unittest.TestCase):
    def test_decodes_real_base64_file_content(self):
        real_text = "# Foundry Development Instructions\n"
        encoded = base64.b64encode(real_text.encode("utf-8")).decode("ascii")
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_http_response({"encoding": "base64", "content": encoded})
            content = fetch_file_content(
                "ghs_token", "jmiedreich-ux", "Foundry", "AGENTS.md", "main"
            )
        self.assertEqual(content, real_text)

    def test_returns_none_for_a_real_404(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.HTTPError(
                "url", 404, "Not Found", {}, BytesIO(b'{"message":"Not Found"}')
            )
            content = fetch_file_content(
                "ghs_token", "jmiedreich-ux", "Foundry", "does/not/exist.md", "main"
            )
        self.assertIsNone(content)

    def test_raises_on_a_real_non_404_error(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.HTTPError(
                "url", 403, "Forbidden", {}, BytesIO(b'{"message":"Forbidden"}')
            )
            with self.assertRaises(GitHubClientError):
                fetch_file_content(
                    "ghs_token", "jmiedreich-ux", "Foundry", "AGENTS.md", "main"
                )

    def test_raises_on_an_unexpected_response_shape(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = _fake_http_response({"type": "dir"})
            with self.assertRaises(GitHubClientError):
                fetch_file_content(
                    "ghs_token", "jmiedreich-ux", "Foundry", "docs", "main"
                )


if __name__ == "__main__":
    unittest.main()
