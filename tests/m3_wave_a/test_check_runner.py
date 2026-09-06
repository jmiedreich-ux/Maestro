from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maestro.check_runner import CheckCommandError, all_passed, run_declared_checks


class RunDeclaredChecksTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.repository_path = Path(self._temporary.name)

    def tearDown(self):
        self._temporary.cleanup()

    def test_a_real_passing_command_reports_passed_true_with_real_stdout(self):
        results = run_declared_checks(self.repository_path, ["python3 -c \"print('ok')\""])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)
        self.assertEqual(results[0].exit_code, 0)
        self.assertIn("ok", results[0].stdout)

    def test_a_real_failing_command_reports_passed_false_with_real_exit_code(self):
        results = run_declared_checks(self.repository_path, ["python3 -c \"import sys; sys.exit(1)\""])
        self.assertFalse(results[0].passed)
        self.assertEqual(results[0].exit_code, 1)

    def test_multiple_declared_commands_all_run_even_after_a_real_failure(self):
        results = run_declared_checks(
            self.repository_path,
            ["python3 -c \"import sys; sys.exit(1)\"", "python3 -c \"print('second')\""],
        )
        self.assertEqual(len(results), 2)
        self.assertFalse(results[0].passed)
        self.assertTrue(results[1].passed)
        self.assertFalse(all_passed(results))

    def test_all_passed_is_true_only_when_every_real_command_passed(self):
        results = run_declared_checks(
            self.repository_path,
            ["python3 -c \"pass\"", "python3 -c \"pass\""],
        )
        self.assertTrue(all_passed(results))

    def test_a_command_that_does_not_exist_fails_without_raising(self):
        results = run_declared_checks(self.repository_path, ["this-binary-does-not-exist-anywhere"])
        self.assertFalse(results[0].passed)
        self.assertIn("not found", results[0].stderr)

    def test_a_real_timeout_fails_without_raising(self):
        results = run_declared_checks(
            self.repository_path,
            ["python3 -c \"import time; time.sleep(5)\""],
            timeout_seconds=0.1,
        )
        self.assertFalse(results[0].passed)
        self.assertIn("timed out", results[0].stderr)

    def test_an_empty_command_string_raises_before_running_anything(self):
        with self.assertRaises(CheckCommandError):
            run_declared_checks(self.repository_path, [""])

    def test_command_runs_with_the_repository_path_as_its_working_directory(self):
        (self.repository_path / "marker.txt").write_text("real")
        results = run_declared_checks(
            self.repository_path, ["python3 -c \"print(open('marker.txt').read())\""]
        )
        self.assertTrue(results[0].passed)
        self.assertIn("real", results[0].stdout)

    def test_commands_never_run_through_a_shell(self):
        # With shell=False, "&&" is just another literal argument to the
        # first program — python3 -c only consumes its own script
        # argument, so the trailing "&& python3 -c ..." never runs as a
        # second process. A shell would instead really execute it and
        # create the side-effect file. Proves no shell interpretation.
        side_effect = self.repository_path / "side-effect.txt"
        command = (
            "python3 -c \"print('first')\" && "
            f"python3 -c \"open('{side_effect}', 'w').write('bad')\""
        )
        results = run_declared_checks(self.repository_path, [command])
        self.assertIn("first", results[0].stdout)
        self.assertFalse(side_effect.exists())


if __name__ == "__main__":
    unittest.main()
