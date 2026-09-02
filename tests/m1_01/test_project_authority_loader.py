from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing

from maestro.git_repository import GitRepositoryError
from maestro.project_authority import ProjectAuthorityLoader
from maestro.project_manifest import ProjectManifestError
from support import (
    RuntimeDirectory,
    TemporaryProjectRepository,
    complete_manifest,
    dump_manifest,
    repository_snapshot,
    run_git,
)


def registration_counts(database_path) -> tuple[int, int, int]:
    with closing(sqlite3.connect(database_path)) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("projects", "project_registration_runs", "events")
        )


class ProjectAuthorityLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = TemporaryProjectRepository()
        self.runtime = RuntimeDirectory()

    def tearDown(self) -> None:
        self.runtime.close()
        self.repository.close()

    def loader(self) -> ProjectAuthorityLoader:
        return ProjectAuthorityLoader(self.runtime.foundation())

    def database_counts(self) -> tuple[int, int, int]:
        return registration_counts(self.runtime.path / "maestro.sqlite3")

    def test_complete_real_repository_records_one_candidate_run_event_without_mutation(self) -> None:
        before = repository_snapshot(self.repository.path)
        result = self.loader().load(
            self.repository.path, self.repository.commit, "owner/example-project"
        )
        after = repository_snapshot(self.repository.path)

        self.assertEqual(result.disposition, "Reviewable")
        self.assertEqual(result.source_commit, self.repository.commit)
        self.assertEqual(result.summary, {"confirmed": 40, "missing": 0, "conflicting": 0})
        self.assertEqual([item.path for item in result.authority_files], [
            "docs/architecture/project-foundation.md",
            "docs/planning/work-graph.yaml",
            "ai/handoffs/current.md",
            "AGENTS.md",
        ])
        self.assertEqual(self.database_counts(), (1, 1, 1))
        self.assertEqual(before, after)

        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            project = connection.execute(
                "SELECT registration_state, active_binding_revision FROM projects"
            ).fetchone()
        self.assertEqual(project, ("Candidate", None))

    def test_pinned_commit_ignores_later_committed_staged_and_uncommitted_changes(self) -> None:
        pinned = self.repository.commit
        first = self.loader().load(self.repository.path, pinned, "owner/example-project")

        (self.repository.path / "docs/architecture/project-foundation.md").write_text(
            "# Later committed architecture\n", encoding="utf-8"
        )
        self.repository.commit_all("later commit")
        (self.repository.path / "docs/planning/work-graph.yaml").write_text(
            "nodes: [staged]\n", encoding="utf-8"
        )
        run_git(self.repository.path, "add", "docs/planning/work-graph.yaml")
        (self.repository.path / "AGENTS.md").write_text("# Uncommitted rules\n", encoding="utf-8")
        before = repository_snapshot(self.repository.path)

        second = self.loader().load(self.repository.path, pinned, "owner/example-project")

        self.assertEqual(second, first)
        self.assertEqual(repository_snapshot(self.repository.path), before)
        self.assertEqual(self.database_counts(), (1, 1, 1))

    def test_missing_authority_blob_records_blocked_run_and_event_without_project(self) -> None:
        run_git(self.repository.path, "rm", "ai/handoffs/current.md")
        commit = self.repository.commit_all("remove handoff")
        before = repository_snapshot(self.repository.path)

        result = self.loader().load(self.repository.path, commit, "owner/example-project")

        self.assertEqual(result.disposition, "Blocked")
        missing = [fact.dotted_path for fact in result.facts if fact.status == "missing"]
        self.assertEqual(missing, ["authority_files.ai/handoffs/current.md"])
        self.assertEqual(self.database_counts(), (0, 1, 1))
        self.assertEqual(repository_snapshot(self.repository.path), before)

    def test_missing_manifest_leaf_records_exact_blocked_fact_without_default(self) -> None:
        manifest = complete_manifest()
        del manifest["operations"]["notification_policy"]
        self.repository.write_manifest(manifest)
        commit = self.repository.commit_all("omit notification policy")

        result = self.loader().load(self.repository.path, commit, "owner/example-project")

        matching = [
            fact for fact in result.facts
            if fact.dotted_path == "operations.notification_policy"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].status, "missing")
        self.assertEqual(result.disposition, "Blocked")
        self.assertNotIn("notification_policy", result.normalized_manifest["operations"])
        self.assertEqual(self.database_counts(), (0, 1, 1))

    def test_repository_identity_and_default_branch_conflicts_are_blocked(self) -> None:
        identity_result = self.loader().load(
            self.repository.path, self.repository.commit, "different/repository"
        )
        self.assertEqual(identity_result.disposition, "Blocked")
        identity_fact = next(
            fact for fact in identity_result.facts if fact.dotted_path == "identity.repository"
        )
        self.assertEqual(identity_fact.status, "conflicting")

        other = TemporaryProjectRepository()
        other_runtime = RuntimeDirectory()
        try:
            run_git(other.path, "branch", "divergent", other.commit)
            manifest = complete_manifest()
            manifest["identity"]["default_branch"] = "divergent"
            other.write_manifest(manifest)
            commit = other.commit_all("declare non-containing branch")
            result = ProjectAuthorityLoader(other_runtime.foundation()).load(
                other.path, commit, "owner/example-project"
            )
            fact = next(f for f in result.facts if f.dotted_path == "identity.default_branch")
            self.assertEqual(result.disposition, "Blocked")
            self.assertEqual(fact.status, "conflicting")
        finally:
            other_runtime.close()
            other.close()

    def test_invalid_missing_symbolic_abbreviated_and_noncommit_revisions_do_not_mutate(self) -> None:
        blob = run_git(self.repository.path, "rev-parse", "HEAD:AGENTS.md").stdout.strip()
        tree = run_git(self.repository.path, "rev-parse", "HEAD^{tree}").stdout.strip()
        run_git(self.repository.path, "tag", "-a", "authority-tag", "-m", "tag")
        tag = run_git(self.repository.path, "rev-parse", "authority-tag^{tag}").stdout.strip()
        invalid = [
            "main", self.repository.commit[:12], "not-a-revision", "0" * 40,
            blob, tree, tag,
        ]
        before = repository_snapshot(self.repository.path)
        for revision in invalid:
            with self.subTest(revision=revision), self.assertRaises(GitRepositoryError):
                self.loader().load(self.repository.path, revision, "owner/example-project")
            self.assertFalse((self.runtime.path / "maestro.sqlite3").exists())
            self.assertEqual(repository_snapshot(self.repository.path), before)

    def test_malformed_manifest_failure_classes_do_not_create_database_or_mutate_repository(self) -> None:
        malformed = [
            b"schema_version: 1\nschema_version: 1\n",
            b"schema_version: 1\nidentity: &i {}\nauthority: *i\n",
            b"schema_version: 1\nidentity: &i {}\nauthority:\n  <<: *i\n",
            b"schema_version: !custom 1\n",
            dump_manifest({**complete_manifest(), "unknown": "field"}),
        ]
        invalid_manifest = complete_manifest()
        invalid_manifest["schema_version"] = "1"
        malformed.append(dump_manifest(invalid_manifest))
        for path in ("/absolute", "../traversal", ".git/config"):
            invalid_manifest = complete_manifest()
            invalid_manifest["authority"]["handoff_path"] = path
            malformed.append(dump_manifest(invalid_manifest))
        for field in ("architecture_paths", "plan_paths"):
            invalid_manifest = complete_manifest()
            invalid_manifest["authority"][field] = []
            malformed.append(dump_manifest(invalid_manifest))
        invalid_manifest = complete_manifest()
        invalid_manifest["routing"]["worker_routes"] = ["cloud", "cloud"]
        malformed.append(dump_manifest(invalid_manifest))
        invalid_manifest = complete_manifest()
        invalid_manifest["exceptions"] = {"disposition": "declared", "items": []}
        malformed.append(dump_manifest(invalid_manifest))
        invalid_manifest = complete_manifest()
        invalid_manifest["operations"]["secret_references"] = ["ghp_credential_payload"]
        malformed.append(dump_manifest(invalid_manifest))
        invalid_manifest = complete_manifest()
        invalid_manifest["operations"]["secret_values"] = ["not-allowed"]
        malformed.append(dump_manifest(invalid_manifest))
        for raw in malformed:
            repository = TemporaryProjectRepository()
            runtime = RuntimeDirectory()
            try:
                repository.write_manifest(raw)
                commit = repository.commit_all("malformed manifest")
                before = repository_snapshot(repository.path)
                with self.assertRaises(ProjectManifestError):
                    ProjectAuthorityLoader(runtime.foundation()).load(
                        repository.path, commit, "owner/example-project"
                    )
                self.assertFalse((runtime.path / "maestro.sqlite3").exists())
                self.assertEqual(repository_snapshot(repository.path), before)
            finally:
                runtime.close()
                repository.close()

    def test_project_architect_is_reviewable_and_owner_is_reserved_blocked(self) -> None:
        valid = complete_manifest()
        valid["operations"]["secret_references"] = ["GITHUB_APP_PRIVATE_KEY", "SLACK_BOT_TOKEN"]
        self.repository.write_manifest(valid)
        commit = self.repository.commit_all("declare secret references")
        result = self.loader().load(self.repository.path, commit, "owner/example-project")
        self.assertEqual(result.disposition, "Reviewable")
        self.assertEqual(self.database_counts(), (1, 1, 1))

        owner_repository = TemporaryProjectRepository()
        owner_runtime = RuntimeDirectory()
        try:
            owner_manifest = complete_manifest()
            owner_manifest["delivery"]["acceptance_authority"] = "owner"
            owner_repository.write_manifest(owner_manifest)
            owner_commit = owner_repository.commit_all("reserve owner acceptance")
            owner_result = ProjectAuthorityLoader(owner_runtime.foundation()).load(
                owner_repository.path, owner_commit, "owner/example-project"
            )
            owner_fact = next(
                fact for fact in owner_result.facts
                if fact.dotted_path == "delivery.acceptance_authority"
            )
            self.assertEqual(owner_result.disposition, "Blocked")
            self.assertEqual(owner_fact.status, "conflicting")
            self.assertEqual(owner_fact.observed_value, "owner")
            self.assertIn("reserved material return", owner_fact.reason)
            self.assertEqual(
                registration_counts(owner_runtime.path / "maestro.sqlite3"),
                (0, 1, 1),
            )
        finally:
            owner_runtime.close()
            owner_repository.close()

    def test_unrecognized_acceptance_authorities_fail_before_persistence(self) -> None:
        rejected = (
            "unrecognized-approver",
            "",
            "Project-Architect",
            " project-architect",
            "project-architect ",
            None,
            False,
            1,
            ["project-architect"],
            {"authority": "project-architect"},
        )
        for authority in rejected:
            repository = TemporaryProjectRepository()
            runtime = RuntimeDirectory()
            try:
                manifest = complete_manifest()
                manifest["delivery"]["acceptance_authority"] = authority
                repository.write_manifest(manifest)
                commit = repository.commit_all("invalid acceptance authority")
                before = repository_snapshot(repository.path)

                with self.subTest(authority=authority), self.assertRaises(ProjectManifestError):
                    ProjectAuthorityLoader(runtime.foundation()).load(
                        repository.path, commit, "owner/example-project"
                    )

                self.assertFalse((runtime.path / "maestro.sqlite3").exists())
                self.assertEqual(repository_snapshot(repository.path), before)
                runtime.foundation().health()
                self.assertEqual(
                    registration_counts(runtime.path / "maestro.sqlite3"),
                    (0, 0, 0),
                )
            finally:
                runtime.close()
                repository.close()

    def test_git_symlink_submodule_nonblob_and_per_blob_overflow_are_rejected_read_only(self) -> None:
        builders = [self._symlink_repository, self._submodule_repository,
                    self._tree_repository, self._oversized_repository]
        for builder in builders:
            repository = builder()
            runtime = RuntimeDirectory()
            try:
                before = repository_snapshot(repository.path)
                with self.subTest(builder=builder.__name__), self.assertRaises(GitRepositoryError):
                    ProjectAuthorityLoader(runtime.foundation()).load(
                        repository.path, repository.commit, "owner/example-project"
                    )
                self.assertFalse((runtime.path / "maestro.sqlite3").exists())
                self.assertEqual(repository_snapshot(repository.path), before)
            finally:
                runtime.close()
                repository.close()

    def test_total_authority_payload_overflow_is_rejected_before_mutation(self) -> None:
        repository = TemporaryProjectRepository()
        runtime = RuntimeDirectory()
        try:
            manifest = complete_manifest()
            paths = [f"authority/file-{index}.bin" for index in range(9)]
            manifest["authority"]["architecture_paths"] = paths
            for path in paths:
                target = repository.path / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"x" * (2 * 1024 * 1024))
            repository.write_manifest(manifest)
            commit = repository.commit_all("large authority set")
            before = repository_snapshot(repository.path)
            with self.assertRaises(GitRepositoryError):
                ProjectAuthorityLoader(runtime.foundation()).load(
                    repository.path, commit, "owner/example-project"
                )
            self.assertFalse((runtime.path / "maestro.sqlite3").exists())
            self.assertEqual(repository_snapshot(repository.path), before)
        finally:
            runtime.close()
            repository.close()

    @staticmethod
    def _symlink_repository() -> TemporaryProjectRepository:
        repository = TemporaryProjectRepository()
        target = repository.path / "ai/handoffs/current.md"
        target.unlink()
        target.symlink_to("../../AGENTS.md")
        repository.commit_all("symlink authority")
        return repository

    @staticmethod
    def _submodule_repository() -> TemporaryProjectRepository:
        repository = TemporaryProjectRepository()
        manifest = complete_manifest()
        manifest["authority"]["architecture_paths"] = ["vendor/module"]
        repository.write_manifest(manifest)
        run_git(repository.path, "add", "maestro.project.yaml")
        run_git(
            repository.path, "update-index", "--add", "--cacheinfo",
            f"160000,{repository.commit},vendor/module",
        )
        run_git(repository.path, "commit", "-m", "submodule authority")
        return repository

    @staticmethod
    def _tree_repository() -> TemporaryProjectRepository:
        repository = TemporaryProjectRepository()
        manifest = complete_manifest()
        manifest["authority"]["architecture_paths"] = ["docs"]
        repository.write_manifest(manifest)
        repository.commit_all("tree authority")
        return repository

    @staticmethod
    def _oversized_repository() -> TemporaryProjectRepository:
        repository = TemporaryProjectRepository()
        manifest = complete_manifest()
        manifest["authority"]["architecture_paths"] = ["authority/large.bin"]
        target = repository.path / "authority/large.bin"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
        repository.write_manifest(manifest)
        repository.commit_all("oversized authority")
        return repository


if __name__ == "__main__":
    unittest.main()
