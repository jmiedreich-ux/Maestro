from __future__ import annotations

import unittest
from unittest import mock

from maestro.real_discovery import fetch_real_process_file, fetch_real_repository_metadata


class FetchRealRepositoryMetadataTests(unittest.TestCase):
    def test_returns_only_the_two_fields_a1_needs_by_real_key_name(self):
        with mock.patch("maestro.real_discovery.fetch_repository_metadata") as fetch:
            fetch.return_value = {
                "full_name": "jmiedreich-ux/Foundry",
                "default_branch": "main",
                "private": False,
                "archived": False,
            }
            result = fetch_real_repository_metadata("token", "jmiedreich-ux", "Foundry")
        self.assertEqual(
            result, {"repository_identifier": "jmiedreich-ux/Foundry", "default_branch": "main"}
        )
        fetch.assert_called_once_with("token", "jmiedreich-ux", "Foundry")


class FetchRealProcessFileTests(unittest.TestCase):
    def test_returns_the_real_file_content_verbatim(self):
        with mock.patch("maestro.real_discovery.fetch_file_content") as fetch:
            fetch.return_value = "# Foundry Development Instructions\n"
            result = fetch_real_process_file("token", "jmiedreich-ux", "Foundry", "main")
        self.assertEqual(result, "# Foundry Development Instructions\n")
        fetch.assert_called_once_with("token", "jmiedreich-ux", "Foundry", "AGENTS.md", "main")

    def test_returns_none_without_inventing_placeholder_content(self):
        with mock.patch("maestro.real_discovery.fetch_file_content") as fetch:
            fetch.return_value = None
            result = fetch_real_process_file("token", "jmiedreich-ux", "SomeOtherProject", "main")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
