from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from maestro.agents.supervisor import AgentSupervisor, FileSupervisorJournal, LocalProcessUnits
from maestro.agents.workspaces import WorkspaceManager
from maestro.foundation import Database, StorageSettings
from maestro.service.agent_runs import AgentRunError, AgentRunService


class AgentRunRecordsTest(unittest.TestCase):
    """Reservation, recovery limits and duration exceptions, decided in SQL before any launch."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        journal = root / "journal"
        journal.mkdir(mode=0o700)
        self.gate = threading.Event()
        self.entered = threading.Event()
        self.failure = "tool_failure"

        def resolver(role: str, tool: str, model: str):
            self.entered.set()
            self.gate.wait(5)
            raise AgentRunError(self.failure, "route unavailable in this test")

        self.service = AgentRunService(
            Database(StorageSettings(path=root / "maestro.sqlite3")),
            AgentSupervisor(FileSupervisorJournal(journal / "j.json"), LocalProcessUnits()),
            WorkspaceManager.__new__(WorkspaceManager),
            route_resolver=resolver,
            profile_resolver=lambda route: None,
            artifact_root=root / "artifacts",
            clock=time.monotonic,
        )
        self.service.create_assignment("a1", "p", "act", "architect", "codex", "gpt-5.6-sol", duration_seconds=100)

    def _start(self, run_id: str, kind: str, **kwargs):
        with self.assertRaises(AgentRunError):
            self.service.start_run("a1", run_id, kind, lambda rid: None, **kwargs)

    def test_simultaneous_starts_reserve_the_assignment_once(self) -> None:
        outcomes: list[str] = []

        def first() -> None:
            try:
                self.service.start_run("a1", "r1", "initial", lambda rid: None)
            except AgentRunError as error:
                outcomes.append(error.code)

        thread = threading.Thread(target=first)
        thread.start()
        self.assertTrue(self.entered.wait(5))
        with self.assertRaises(AgentRunError) as second:
            self.service.start_run("a1", "r2", "initial", lambda rid: None)
        self.gate.set()
        thread.join()
        self.assertEqual("run_not_ended", second.exception.code)
        self.assertEqual(["tool_failure"], outcomes)

    def test_automatic_limit_manual_retry_and_one_time_duration_exception(self) -> None:
        self.gate.set()
        self._start("r1", "initial")
        self.assertEqual("needs_recovery", self.service.assignment_state("a1")["state"])
        self._start("r2", "recovery")
        self._start("r3", "recovery")
        state = self.service.assignment_state("a1")
        self.assertEqual((2, "paused"), (state["automatic_used"], state["state"]))
        self._start("r4", "recovery")  # limit used: refused before any launch
        self.assertEqual(2, self.service.assignment_state("a1")["automatic_used"])
        self._start("r5", "manual")  # needs a recorded intervention
        self.service.set_next_run_duration("a1", 900)
        self._start("r6", "manual", intervention="restored access")
        state = self.service.assignment_state("a1")
        self.assertEqual((2, 1, None), (state["automatic_used"], state["manual_used"], state["next_duration_seconds"]))
        durations = {run: self.service.view(run).duration_seconds for run in ("r1", "r6")}
        self.assertEqual({"r1": 100, "r6": 900}, durations)

    def test_intervention_causes_pause_without_automatic_retry(self) -> None:
        self.gate.set()
        self.failure = "model_mismatch"
        self._start("r1", "initial")
        state = self.service.assignment_state("a1")
        self.assertEqual("paused", state["state"])
        self.assertEqual(0, state["automatic_used"])
        self._start("r2", "recovery")


if __name__ == "__main__":
    unittest.main()
