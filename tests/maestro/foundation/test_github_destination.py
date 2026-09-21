from __future__ import annotations

import unittest

from maestro.foundation.credentials import (
    AuthorizedRepository,
    GitHubAppCredential,
    RepositoryCredentialError,
    ServiceGitTransport,
)
from maestro.foundation.github_destination import (
    BranchPolicyObservation,
    GitHubAppDestinationProfile,
    GitHubDestinationAuthorizationError,
    GitHubDestinationProvider,
    GitHubInstallationToken,
)


class GitHubDestinationProviderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = GitHubAppDestinationProfile(
            profile_name="maestro-coordinator",
            binding_id="maestro-project",
            credential=GitHubAppCredential("github-app-maestro-coordinator"),
            app_id=101,
            installation_id=202,
            app_slug="maestro-coordinator",
            allowed_repositories=("owner/project",),
            allowed_branches=("maestro-m3-authorized", "maestro-m3-protected"),
        )
        self.api = _FixtureGitHubApi(self.profile)
        self.provider = GitHubDestinationProvider(self.profile, self.api)
        self.authorization = AuthorizedRepository(
            binding_id="maestro-project",
            repository="owner/project",
            branch="maestro-m3-authorized",
            profile_name="maestro-coordinator",
            credential_reference="github-app-maestro-coordinator",
        )

    def test_allowed_result_is_bound_fresh_and_persists_only_non_secret_evidence(self) -> None:
        result = self.provider.authorize("OWNER/PROJECT", "maestro-m3-authorized", now=1000)

        self.assertEqual("allowed", result.decision)
        self.provider.require_fresh_match(result, self.authorization, now=1020)
        durable = result.durable_record()
        self.assertEqual("owner/project", durable["snapshot"]["repository"])
        self.assertEqual("maestro-m3-authorized", durable["snapshot"]["branch"])
        self.assertEqual("a" * 40, result.destination_head)
        self.assertNotIn("fixture-installation-token", repr(durable))
        self.assertNotIn("fixture-installation-token", repr(result))
        self.assertEqual(6, len(durable["evidence_hashes"]))

    def test_wrong_app_or_installation_and_missing_permissions_are_blocked(self) -> None:
        self.api.app = {"id": 999, "slug": self.profile.app_slug}
        self.assertEqual("blocked", self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000).decision)

        self.api.app = {"id": self.profile.app_id, "slug": self.profile.app_slug}
        self.api.installation = {"id": 999, "app_id": self.profile.app_id}
        self.assertEqual("blocked", self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000).decision)

        self.api.installation = {"id": self.profile.installation_id, "app_id": self.profile.app_id}
        self.api.permissions = {"contents": "read", "administration": "read"}
        self.assertEqual("blocked", self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000).decision)
        self.api.permissions = {"contents": "write", "administration": "none"}
        self.assertEqual("blocked", self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000).decision)

    def test_configured_branch_pattern_authorizes_only_matching_exact_branches(self) -> None:
        profile = GitHubAppDestinationProfile(
            profile_name="maestro-coordinator",
            binding_id="maestro-project",
            credential=GitHubAppCredential("github-app-maestro-coordinator"),
            app_id=101,
            installation_id=202,
            app_slug="maestro-coordinator",
            allowed_repositories=("owner/project",),
            allowed_branches=("release/*",),
        )
        provider = GitHubDestinationProvider(profile, _FixtureGitHubApi(profile))

        self.assertEqual(
            "allowed",
            provider.authorize("owner/project", "release/2026-09", now=1000).decision,
        )
        self.assertEqual(
            "blocked",
            provider.authorize("owner/project", "main", now=1000).decision,
        )

    def test_protected_or_ruleset_branch_and_unavailable_provider_fail_closed(self) -> None:
        self.api.policy = BranchPolicyObservation(True, ())
        self.assertEqual("blocked", self.provider.authorize("owner/project", "maestro-m3-protected", now=1000).decision)

        self.api.policy = BranchPolicyObservation(False, ({"id": 1, "name": "guard"},))
        self.assertEqual("blocked", self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000).decision)

        self.api.failure = RepositoryCredentialError("private key unavailable")
        self.assertEqual("unverifiable", self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000).decision)

    def test_stale_or_changed_result_cannot_bind_a_service_transport(self) -> None:
        result = self.provider.authorize("owner/project", "maestro-m3-authorized", now=1000)
        with self.assertRaises(GitHubDestinationAuthorizationError):
            self.provider.require_fresh_match(result, self.authorization, now=1061)
        wrong_branch = AuthorizedRepository(
            binding_id=self.authorization.binding_id,
            repository=self.authorization.repository,
            branch="maestro-m3-protected",
            profile_name=self.authorization.profile_name,
            credential_reference=self.authorization.credential_reference,
        )
        with self.assertRaises(GitHubDestinationAuthorizationError):
            self.provider.require_fresh_match(result, wrong_branch, now=1001)
        with self.assertRaises(GitHubDestinationAuthorizationError):
            self.provider.bind_transport(result, _NoRouteTransport(), self.authorization, now=1061)


class _FixtureGitHubApi:
    """Controlled component input; live GitHub binding remains external QA."""

    def __init__(self, profile: GitHubAppDestinationProfile) -> None:
        self.profile = profile
        self.app = {"id": profile.app_id, "slug": profile.app_slug}
        self.installation = {"id": profile.installation_id, "app_id": profile.app_id}
        self.permissions = {"contents": "write", "administration": "read"}
        self.policy = BranchPolicyObservation(False, ())
        self.failure: Exception | None = None

    def _check(self) -> None:
        if self.failure is not None:
            raise self.failure

    def app_identity(self, profile):
        self._check()
        return self.app

    def installation_identity(self, profile):
        self._check()
        return self.installation

    def installation_token(self, profile):
        self._check()
        return GitHubInstallationToken("fixture-installation-token", self.permissions, 4_102_444_800, profile.api_base_url)

    def repository_identity(self, token, repository):
        self._check()
        return {"id": 1, "full_name": repository}

    def branch_identity(self, token, repository, branch):
        self._check()
        return {"name": branch, "commit": {"sha": "a" * 40}}

    def branch_policy(self, token, repository, branch):
        self._check()
        return self.policy


class _NoRouteTransport(ServiceGitTransport):
    """Only used to prove stale evidence is rejected before a route is touched."""

    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
