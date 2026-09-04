from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from maestro.review_readiness import (
    MAX_CAPTURE_BYTES,
    REQUEST_SCHEMA,
    RESULT_SCHEMA,
    RequestError,
    ResultError,
    canonical_json,
    evaluate_review_readiness,
    parse_request,
    result_exit_code,
    validate_result,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class GitCandidate:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.git("init", "-q")
        self.git("config", "user.email", "maestro@example.test")
        self.git("config", "user.name", "Maestro Test")
        self.write("candidate.txt", "base\n")
        self.git("add", "candidate.txt")
        self.git("commit", "-qm", "base")
        self.base = self.sha("HEAD")
        self.write("candidate.txt", "candidate\n")
        self.git("add", "candidate.txt")
        self.git("commit", "-qm", "candidate")
        self.head = self.sha("HEAD")

    def close(self) -> None:
        self._temporary.cleanup()

    def git(self, *args: str, check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def sha(self, revision: str) -> str:
        return self.git("rev-parse", revision).stdout.decode().strip()

    def write(self, path: str, content: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def request(self, **updates: object) -> dict[str, object]:
        request: dict[str, object] = {
            "schema": REQUEST_SCHEMA,
            "slice_id": "MB-SLICE-TEST-01",
            "review_kind": "IndependentImplementation",
            "repository": str(self.root),
            "base": self.base,
            "head": self.head,
            "allowed_paths": ["candidate.txt"],
            "validation_commands": [{"check_id": "validation", "argv": [sys.executable, "-c", "pass"]}],
            "reconstruction_commands": [{"check_id": "reconstruction", "argv": [sys.executable, "-c", "pass"]}],
            "timeout_seconds": 2,
        }
        request.update(updates)
        return request

    def evaluate(self, request: dict[str, object] | None = None, callback=None):  # type: ignore[no-untyped-def]
        return evaluate_review_readiness(canonical_json(request or self.request()), callback)


class ReviewReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = GitCandidate()

    def tearDown(self) -> None:
        self.candidate.close()

    def assert_codes(self, result: dict[str, object], *codes: str) -> None:
        self.assertEqual([item["code"] for item in result["blockers"]], list(codes))  # type: ignore[index]

    def test_01_valid_candidate_records_checked_out_head_before_and_after(self) -> None:
        result = self.candidate.evaluate()
        self.assertTrue(result["ready"])
        self.assertEqual(result["resolved_head"], self.candidate.head)
        self.assertEqual(result["checked_out_head_before"], self.candidate.head)
        self.assertEqual(result["checked_out_head_after"], self.candidate.head)
        self.assertEqual(result["changed_paths"], ["candidate.txt"])
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["schema"], RESULT_SCHEMA)
        self.assertEqual(result_exit_code(result), 0)
        validate_result(result)

    def test_02_requested_head_not_checked_out_blocks_before_commands_and_callback(self) -> None:
        self.candidate.git("checkout", "-q", self.candidate.base)
        calls = 0

        def callback() -> None:
            nonlocal calls
            calls += 1

        result = self.candidate.evaluate(callback=callback)
        self.assert_codes(result, "HEAD_NOT_CHECKED_OUT_BEFORE", "HEAD_NOT_CHECKED_OUT_AFTER")
        self.assertEqual(result["checked_out_head_before"], self.candidate.base)
        self.assertTrue(all(check["outcome"] == "Skipped" for check in result["checks"]))  # type: ignore[union-attr]
        self.assertEqual(calls, 0)
        self.assertEqual(result["callback"]["outcome"], "Suppressed")  # type: ignore[index]

    def test_03_command_that_changes_head_is_blocked_after_commands(self) -> None:
        command = ["git", "checkout", "-q", self.candidate.base]
        request = self.candidate.request(
            validation_commands=[{"check_id": "move-head", "argv": command}]
        )
        result = self.candidate.evaluate(request)
        self.assert_codes(result, "HEAD_NOT_CHECKED_OUT_AFTER")
        self.assertTrue(result["clean_after"])
        self.assertEqual(result["checked_out_head_after"], self.candidate.base)

    def test_04_base_equals_head_is_blocked(self) -> None:
        request = self.candidate.request(base=self.candidate.head)
        result = self.candidate.evaluate(request)
        self.assert_codes(result, "EMPTY_COMMIT_RANGE", "EMPTY_CHANGED_PATHS")
        self.assertFalse(result["ready"])
        self.assertEqual(result_exit_code(result), 2)

    def test_05_nonexistent_base_and_head_are_separately_blocked(self) -> None:
        missing = "0" * 40
        base_result = self.candidate.evaluate(self.candidate.request(base=missing))
        head_result = self.candidate.evaluate(self.candidate.request(head=missing))
        self.assertIn("BASE_NOT_COMMIT", [b["code"] for b in base_result["blockers"]])  # type: ignore[index]
        self.assertIn("HEAD_NOT_COMMIT", [b["code"] for b in head_result["blockers"]])  # type: ignore[index]

        invalid_repository = self.candidate.evaluate(
            self.candidate.request(repository=str(self.candidate.root / "missing"))
        )
        self.assert_codes(invalid_repository, "REPOSITORY_INVALID")
        self.assertTrue(all(check["skip_reason"] == "RepositoryInvalid" for check in invalid_repository["checks"]))  # type: ignore[union-attr]

        nul_repository = self.candidate.evaluate(
            self.candidate.request(repository=f"{self.candidate.root}\0invalid")
        )
        self.assert_codes(nul_repository, "REPOSITORY_INVALID")
        self.assertEqual(result_exit_code(nul_repository), 2)
        validate_result(nul_repository)

    def test_06_noncommit_objects_are_blocked(self) -> None:
        blob = self.candidate.git("hash-object", "-w", "--stdin", input_bytes=b"blob").stdout.decode().strip()
        tree = self.candidate.git("rev-parse", "HEAD^{tree}").stdout.decode().strip()
        self.candidate.git("tag", "-a", "blob-tag", blob, "-m", "blob tag")
        for field, value, code in (
            ("base", blob, "BASE_NOT_COMMIT"),
            ("head", tree, "HEAD_NOT_COMMIT"),
            ("head", "blob-tag", "HEAD_NOT_COMMIT"),
        ):
            with self.subTest(field=field, value=value):
                result = self.candidate.evaluate(self.candidate.request(**{field: value}))
                self.assertIn(code, [b["code"] for b in result["blockers"]])  # type: ignore[index]

    def test_07_commit_range_with_no_file_diff_is_blocked(self) -> None:
        self.candidate.git("commit", "--allow-empty", "-qm", "empty")
        empty_head = self.candidate.sha("HEAD")
        request = self.candidate.request(base=self.candidate.head, head=empty_head)
        result = self.candidate.evaluate(request)
        self.assert_codes(result, "EMPTY_CHANGED_PATHS")

    def test_08_staged_unstaged_and_untracked_paths_are_separately_blocked(self) -> None:
        mutations = (
            ("staged.txt", lambda: (self.candidate.write("staged.txt", "x"), self.candidate.git("add", "staged.txt"))),
            ("candidate.txt", lambda: self.candidate.write("candidate.txt", "dirty")),
            ("untracked.txt", lambda: self.candidate.write("untracked.txt", "x")),
        )
        for expected_path, mutate in mutations:
            with self.subTest(path=expected_path):
                fresh = GitCandidate()
                old = self.candidate
                self.candidate = fresh
                try:
                    mutate = (
                        (lambda: (fresh.write("staged.txt", "x"), fresh.git("add", "staged.txt")))
                        if expected_path == "staged.txt"
                        else (lambda: fresh.write(expected_path, "dirty"))
                    )
                    mutate()
                    result = fresh.evaluate()
                    self.assertIn("DIRTY_BEFORE", [b["code"] for b in result["blockers"]])  # type: ignore[index]
                    self.assertIn(expected_path, result["blockers"][[b["code"] for b in result["blockers"]].index("DIRTY_BEFORE")]["detail"])  # type: ignore[index]
                finally:
                    fresh.close()
                    self.candidate = old

    def test_09_exact_file_rule_rejects_descendant_and_prefix_collision(self) -> None:
        valid = self.candidate.evaluate()
        self.assertTrue(valid["ready"])
        for changed in ("candidate.txt/child", "candidate.txt-more"):
            fresh = GitCandidate()
            try:
                if changed == "candidate.txt/child":
                    (fresh.root / "candidate.txt").unlink()
                fresh.write(changed, "x")
                fresh.git("add", "-A")
                fresh.git("commit", "-qm", changed)
                result = fresh.evaluate(fresh.request(base=fresh.head, head=fresh.sha("HEAD")))
                self.assertIn("PATH_NOT_ALLOWED", [b["code"] for b in result["blockers"]])  # type: ignore[index]
            finally:
                fresh.close()

    def test_10_directory_rule_has_complete_boundary(self) -> None:
        for changed, ready in (("src/a/file", True), ("src/ab/file", False)):
            fresh = GitCandidate()
            try:
                base = fresh.sha("HEAD")
                fresh.write(changed, "x")
                fresh.git("add", changed)
                fresh.git("commit", "-qm", changed)
                request = fresh.request(base=base, head=fresh.sha("HEAD"), allowed_paths=["src/a/"])
                result = fresh.evaluate(request)
                self.assertEqual(result["ready"], ready)
                self.assertEqual("PATH_NOT_ALLOWED" in [b["code"] for b in result["blockers"]], not ready)  # type: ignore[index]
            finally:
                fresh.close()

    def test_11_every_malformed_allowed_path_form_is_rejected(self) -> None:
        invalid = ["", ".", "..", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a//"]
        for path in invalid:
            with self.subTest(path=path):
                result = self.candidate.evaluate(self.candidate.request(allowed_paths=[path]))
                self.assert_codes(result, "MALFORMED_REQUEST")

    def test_12_validation_failure_records_exit_and_later_checks_run(self) -> None:
        commands = [
            {"check_id": "fails", "argv": [sys.executable, "-c", "import sys; sys.exit(7)"]},
            {"check_id": "later", "argv": [sys.executable, "-c", "print('ran')"]},
        ]
        result = self.candidate.evaluate(self.candidate.request(validation_commands=commands))
        self.assert_codes(result, "VALIDATION_FAILED")
        self.assertEqual(result["checks"][0]["exit_code"], 7)  # type: ignore[index]
        self.assertEqual(result["checks"][1]["outcome"], "Passed")  # type: ignore[index]
        self.assertEqual(result["blockers"][0]["detail"], "validation check fails exited 7")  # type: ignore[index]

    def test_13_reconstruction_failure_is_blocked(self) -> None:
        commands = [{"check_id": "digest", "argv": [sys.executable, "-c", "import sys; sys.exit(4)"]}]
        result = self.candidate.evaluate(self.candidate.request(reconstruction_commands=commands))
        self.assert_codes(result, "RECONSTRUCTION_FAILED")
        self.assertEqual(result["checks"][-1]["exit_code"], 4)  # type: ignore[index]

    def test_14_validation_and_reconstruction_timeouts_are_classified_and_bounded(self) -> None:
        slow = [sys.executable, "-c", "import time; print('before', flush=True); time.sleep(5)"]
        for field, check_id, code in (
            ("validation_commands", "slow-validation", "VALIDATION_TIMED_OUT"),
            ("reconstruction_commands", "slow-reconstruction", "RECONSTRUCTION_TIMED_OUT"),
        ):
            with self.subTest(field=field):
                request = self.candidate.request(timeout_seconds=1, **{field: [{"check_id": check_id, "argv": slow}]})
                result = self.candidate.evaluate(request)
                target = next(check for check in result["checks"] if check["check_id"] == check_id)  # type: ignore[union-attr]
                self.assertEqual(target["outcome"], "TimedOut")
                self.assertIn("before", target["stdout"]["text_utf8"])
                self.assertIn(code, [b["code"] for b in result["blockers"]])  # type: ignore[index]

    def test_15_validation_and_reconstruction_launch_errors_are_separate(self) -> None:
        for field, check_id, code in (
            ("validation_commands", "bad-validation", "VALIDATION_LAUNCH_ERROR"),
            ("reconstruction_commands", "bad-reconstruction", "RECONSTRUCTION_LAUNCH_ERROR"),
        ):
            request = self.candidate.request(**{field: [{"check_id": check_id, "argv": ["/no/such/maestro-command"]}]})
            result = self.candidate.evaluate(request)
            self.assertIn(code, [b["code"] for b in result["blockers"]])  # type: ignore[index]
            target = next(check for check in result["checks"] if check["check_id"] == check_id)  # type: ignore[union-attr]
            self.assertEqual(target["outcome"], "LaunchError")
        no_shell = self.candidate.evaluate(
            self.candidate.request(
                validation_commands=[{"check_id": "no-shell", "argv": ["printf shell-would-run"]}]
            )
        )
        self.assert_codes(no_shell, "VALIDATION_LAUNCH_ERROR")

    def test_15b_nul_argv_launch_errors_are_canonical_and_suppress_callback(self) -> None:
        for field, check_id, code in (
            ("validation_commands", "nul-validation", "VALIDATION_LAUNCH_ERROR"),
            ("reconstruction_commands", "nul-reconstruction", "RECONSTRUCTION_LAUNCH_ERROR"),
        ):
            with self.subTest(field=field):
                callbacks = 0

                def callback() -> None:
                    nonlocal callbacks
                    callbacks += 1

                request = self.candidate.request(
                    **{field: [{"check_id": check_id, "argv": [sys.executable, "\0"]}]}
                )
                result = self.candidate.evaluate(request, callback)
                self.assert_codes(result, code)
                check = next(item for item in result["checks"] if item["check_id"] == check_id)  # type: ignore[union-attr]
                self.assertEqual(check["outcome"], "LaunchError")
                self.assertIn("ValueError: embedded null byte", result["blockers"][0]["detail"])  # type: ignore[index]
                self.assertEqual(result["callback"], {"outcome": "Suppressed", "detail": None})
                self.assertEqual(callbacks, 0)
                self.assertEqual(result_exit_code(result), 2)
                validate_result(result)

    def test_16_successful_command_mutations_are_caught_after_commands(self) -> None:
        scripts = {
            "staged": "from pathlib import Path; import subprocess; Path('post.txt').write_text('x'); subprocess.run(['git','add','post.txt'],check=True)",
            "unstaged": "from pathlib import Path; Path('candidate.txt').write_text('post')",
            "untracked": "from pathlib import Path; Path('post.txt').write_text('x')",
        }
        for kind, script in scripts.items():
            with self.subTest(kind=kind):
                fresh = GitCandidate()
                try:
                    calls = 0

                    def callback() -> None:
                        nonlocal calls
                        calls += 1

                    request = fresh.request(validation_commands=[{"check_id": kind, "argv": [sys.executable, "-c", script]}])
                    result = fresh.evaluate(request, callback)
                    self.assertIn("DIRTY_AFTER", [b["code"] for b in result["blockers"]])  # type: ignore[index]
                    self.assertEqual(calls, 0)
                finally:
                    fresh.close()

    def test_17_large_output_retains_prefix_and_complete_stream_digest(self) -> None:
        size = MAX_CAPTURE_BYTES + 999
        script = f"import sys; sys.stdout.buffer.write(b'o'*{size}); sys.stderr.buffer.write(b'e'*{size})"
        request = self.candidate.request(validation_commands=[{"check_id": "large", "argv": [sys.executable, "-c", script]}])
        result = self.candidate.evaluate(request)
        check = result["checks"][0]  # type: ignore[index]
        for stream_name, byte in (("stdout", b"o"), ("stderr", b"e")):
            stream = check[stream_name]
            self.assertEqual(stream["bytes_total"], size)
            self.assertTrue(stream["truncated"])
            self.assertEqual(len(stream["text_utf8"].encode()), MAX_CAPTURE_BYTES)
            self.assertEqual(stream["sha256"], hashlib.sha256(byte * size).hexdigest())

    def test_18_simultaneous_blockers_have_declared_order(self) -> None:
        script = (
            "from pathlib import Path; import subprocess,sys; "
            f"subprocess.run(['git','checkout','-q','{self.candidate.base}'],check=True); "
            "Path('dirty.txt').write_text('x'); sys.exit(7)"
        )
        request = self.candidate.request(
            timeout_seconds=1,
            validation_commands=[{"check_id": "fails", "argv": [sys.executable, "-c", script]}],
            reconstruction_commands=[{"check_id": "slow", "argv": [sys.executable, "-c", "import time; time.sleep(5)"]}],
        )
        result = self.candidate.evaluate(request)
        self.assert_codes(
            result,
            "VALIDATION_FAILED",
            "RECONSTRUCTION_TIMED_OUT",
            "DIRTY_AFTER",
            "HEAD_NOT_CHECKED_OUT_AFTER",
        )

    def test_19_malformed_requests_execute_nothing_and_invoke_no_callback(self) -> None:
        valid = self.candidate.request()
        malformed_bytes = [
            b"{",
            b"\xff",
            b'{"schema":"x","schema":"y"}',
            b'{"timeout_seconds":NaN}',
        ]
        malformed_values: list[object] = []
        unknown = copy.deepcopy(valid); unknown["unknown"] = True; malformed_values.append(unknown)
        for key in valid:
            wrong = copy.deepcopy(valid)
            wrong[key] = None
            malformed_values.append(wrong)
        enum = copy.deepcopy(valid); enum["review_kind"] = "Other"; malformed_values.append(enum)
        duplicate_id = copy.deepcopy(valid); duplicate_id["reconstruction_commands"][0]["check_id"] = "validation"; malformed_values.append(duplicate_id)  # type: ignore[index]
        reversed_paths = copy.deepcopy(valid); reversed_paths["allowed_paths"] = ["z", "a"]; malformed_values.append(reversed_paths)
        duplicates = copy.deepcopy(valid); duplicates["allowed_paths"] = ["a", "a"]; malformed_values.append(duplicates)
        for field in ("validation_commands", "reconstruction_commands"):
            empty = copy.deepcopy(valid); empty[field] = []; malformed_values.append(empty)
            argv = copy.deepcopy(valid); argv[field][0]["argv"] = []; malformed_values.append(argv)  # type: ignore[index]
        for timeout in (0, 3601, True):
            bad = copy.deepcopy(valid); bad["timeout_seconds"] = timeout; malformed_values.append(bad)
        malformed_bytes.extend(canonical_json(value) for value in malformed_values)
        nested_duplicate = canonical_json(valid).replace(
            b'"check_id":"validation"',
            b'"check_id":"validation","check_id":"again"',
            1,
        )
        malformed_bytes.append(nested_duplicate)
        calls = 0

        def callback() -> None:
            nonlocal calls
            calls += 1

        for raw in malformed_bytes:
            with self.subTest(raw=raw[:80]):
                result = evaluate_review_readiness(raw, callback)
                self.assert_codes(result, "MALFORMED_REQUEST")
                self.assertEqual(result["request"], None)
                self.assertEqual(result["checks"], [])
        self.assertEqual(calls, 0)

    def test_19b_combined_invalid_request_uses_canonical_field_first_reason(self) -> None:
        request = self.candidate.request(
            reconstruction_commands=[{"check_id": "", "argv": []}],
            repository="relative-and-invalid",
            validation_commands=[],
        )
        result = self.candidate.evaluate(request)
        self.assertEqual(
            result["blockers"][0]["detail"],  # type: ignore[index]
            "request does not conform to maestro.review-readiness.request/v1: "
            "reconstruction_commands[0].argv must be a nonempty array",
        )

        duplicate = self.candidate.request()
        duplicate["validation_commands"][0]["check_id"] = "reconstruction"  # type: ignore[index]
        duplicate_result = self.candidate.evaluate(duplicate)
        self.assertEqual(
            duplicate_result["blockers"][0]["detail"],  # type: ignore[index]
            "request does not conform to maestro.review-readiness.request/v1: "
            "duplicate check_id reconstruction",
        )

    def test_20_result_and_nested_objects_are_closed_and_enums_are_closed(self) -> None:
        valid = self.candidate.evaluate()
        mutations = []
        for container_path in (
            (),
            ("request",),
            ("request", "validation_commands", 0),
            ("checks", 0),
            ("checks", 0, "stdout"),
            ("callback",),
        ):
            for operation in ("missing", "extra"):
                mutant = copy.deepcopy(valid)
                container = mutant
                for part in container_path:
                    container = container[part]  # type: ignore[index]
                if operation == "missing":
                    container.pop(next(iter(container)))  # type: ignore[union-attr]
                else:
                    container["extra"] = True  # type: ignore[index]
                mutations.append(mutant)
        blocked = self.candidate.evaluate(
            self.candidate.request(validation_commands=[{"check_id": "bad", "argv": [sys.executable, "-c", "import sys;sys.exit(1)"]}])
        )
        for operation in ("missing", "extra"):
            mutant = copy.deepcopy(blocked)
            if operation == "missing":
                mutant["blockers"][0].pop("detail")
            else:
                mutant["blockers"][0]["extra"] = True
            mutations.append(mutant)
        enum_mutations = (
            (valid, ("request", "review_kind"), "Other"),
            (valid, ("checks", 0, "category"), "Other"),
            (valid, ("checks", 0, "outcome"), "Other"),
            (valid, ("callback", "outcome"), "Other"),
            (blocked, ("blockers", 0, "code"), "Other"),
        )
        for source, path, value in enum_mutations:
            mutant = copy.deepcopy(source)
            target = mutant
            for part in path[:-1]:
                target = target[part]  # type: ignore[index]
            target[path[-1]] = value  # type: ignore[index]
            mutations.append(mutant)
        skipped = self.candidate.evaluate(self.candidate.request(base=self.candidate.head))
        skipped["checks"][0]["skip_reason"] = "Other"
        mutations.append(skipped)
        passed_nonzero = copy.deepcopy(valid); passed_nonzero["checks"][0]["exit_code"] = 1; mutations.append(passed_nonzero)
        ready_with_blocker = copy.deepcopy(blocked); ready_with_blocker["ready"] = True; mutations.append(ready_with_blocker)
        missing_check = copy.deepcopy(valid); missing_check["checks"].pop(); mutations.append(missing_check)
        for mutant in mutations:
            with self.assertRaises(ResultError):
                validate_result(mutant)

    def test_21_canonical_object_and_array_order_rules(self) -> None:
        request = self.candidate.request()
        raw_reversed_keys = json.dumps(dict(reversed(list(request.items()))), separators=(",", ":")).encode()
        self.assertEqual(parse_request(raw_reversed_keys), request)
        reversed_allowed = copy.deepcopy(request); reversed_allowed["allowed_paths"] = ["z", "candidate.txt"]
        with self.assertRaises(RequestError):
            parse_request(canonical_json(reversed_allowed))
        first = [
            {"check_id": "one", "argv": [sys.executable, "-c", "print('one')"]},
            {"check_id": "two", "argv": [sys.executable, "-c", "print('two')"]},
        ]
        result_one = self.candidate.evaluate(self.candidate.request(validation_commands=first))
        result_two = self.candidate.evaluate(self.candidate.request(validation_commands=list(reversed(first))))
        self.assertEqual([c["check_id"] for c in result_one["checks"][:2]], ["one", "two"])  # type: ignore[index]
        self.assertEqual([c["check_id"] for c in result_two["checks"][:2]], ["two", "one"])  # type: ignore[index]
        self.assertNotEqual(canonical_json(result_one), canonical_json(result_two))

    def test_22_record_digest_reproduces_and_covers_scalars_and_array_order(self) -> None:
        result = self.candidate.evaluate()
        validate_result(result)
        unsigned = copy.deepcopy(result)
        supplied = unsigned.pop("record_digest")
        self.assertEqual(supplied, hashlib.sha256(canonical_json(unsigned)).hexdigest())
        scalar = copy.deepcopy(result); scalar["clean_before"] = False
        reordered = copy.deepcopy(result); reordered["checks"].reverse()
        wrong_digest = copy.deepcopy(result); wrong_digest["record_digest"] = "0" * 64
        for mutant in (scalar, reordered, wrong_digest):
            with self.assertRaises(ResultError):
                validate_result(mutant)

    def test_23_callback_and_allowance_remain_zero_when_blocked_and_increment_once_when_valid(self) -> None:
        launches = 0
        allowances = 0

        def callback() -> None:
            nonlocal launches, allowances
            launches += 1
            allowances += 1

        blocked = self.candidate.evaluate(self.candidate.request(base=self.candidate.head), callback)
        self.assertEqual((launches, allowances), (0, 0))
        self.assertEqual(blocked["callback"]["outcome"], "Suppressed")  # type: ignore[index]
        valid = self.candidate.evaluate(callback=callback)
        self.assertEqual((launches, allowances), (1, 1))
        self.assertEqual(valid["callback"]["outcome"], "Succeeded")  # type: ignore[index]
        self.assertTrue(valid["ready"])

    def test_24_callback_exception_is_not_retried_or_counted_as_consumed(self) -> None:
        launches = 0
        allowances = 0

        def callback() -> None:
            nonlocal launches
            launches += 1
            raise RuntimeError("transport failed")

        result = self.candidate.evaluate(callback=callback)
        self.assertEqual((launches, allowances), (1, 0))
        self.assertEqual(result["callback"], {"outcome": "Raised", "detail": "RuntimeError: transport failed"})
        self.assert_codes(result, "CALLBACK_EXCEPTION")
        self.assertFalse(result["ready"])
        self.assertEqual(result_exit_code(result), 2)

    def test_cli_status_and_canonical_output(self) -> None:
        request_path = self.candidate.root / "request.json"
        request_path.write_bytes(canonical_json(self.candidate.request()))
        result = subprocess.run(
            [sys.executable, "-m", "maestro.cli", "review-readiness", "--request", str(request_path)],
            cwd=REPOSITORY_ROOT,
            env={**os.environ, "PYTHONPATH": str(REPOSITORY_ROOT / "services" / "maestro")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        # The request file is intentionally inside the candidate and therefore proves
        # the CLI observes untracked candidate state rather than hiding it.
        payload = json.loads(result.stdout)
        self.assertIn("DIRTY_BEFORE", [b["code"] for b in payload["blockers"]])
        self.assertFalse(result.stdout.endswith(b"\n"))

        request_path.unlink()
        with tempfile.TemporaryDirectory() as request_directory:
            clean_request = Path(request_directory) / "request.json"
            clean_request.write_bytes(canonical_json(self.candidate.request()))
            passing = subprocess.run(
                [sys.executable, "-m", "maestro.cli", "review-readiness", "--request", str(clean_request)],
                cwd=REPOSITORY_ROOT,
                env={**os.environ, "PYTHONPATH": str(REPOSITORY_ROOT / "services" / "maestro")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(passing.returncode, 0, passing.stderr)
        self.assertTrue(json.loads(passing.stdout)["ready"])

        with tempfile.TemporaryDirectory() as request_directory:
            nul_request = Path(request_directory) / "nul-request.json"
            nul_request.write_bytes(
                canonical_json(
                    self.candidate.request(
                        validation_commands=[
                            {"check_id": "nul", "argv": [sys.executable, "\0"]}
                        ]
                    )
                )
            )
            blocked = subprocess.run(
                [sys.executable, "-m", "maestro.cli", "review-readiness", "--request", str(nul_request)],
                cwd=REPOSITORY_ROOT,
                env={**os.environ, "PYTHONPATH": str(REPOSITORY_ROOT / "services" / "maestro")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        blocked_result = json.loads(blocked.stdout)
        self.assertEqual(blocked_result["blockers"][0]["code"], "VALIDATION_LAUNCH_ERROR")
        self.assertFalse(blocked_result["ready"])


if __name__ == "__main__":
    unittest.main()
