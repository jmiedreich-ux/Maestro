"""Restart reconciliation for saved agent operations.

Recovery only reports the saved operation's state.  It never calls launch and
therefore cannot duplicate work or reset an allowance.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .supervisor import OperationIdentity, RunRecord, SupervisorJournal, UnitController


@dataclass(frozen=True)
class RecoveryDecision:
    operation: OperationIdentity
    status: str
    reason: str
    replacement_permitted: bool = False
    allowance_change: int = 0


class RecoveryReconciler:
    def __init__(self, journal: SupervisorJournal, units: UnitController) -> None:
        self.journal, self.units = journal, units

    def reconcile(self, operation: OperationIdentity) -> RecoveryDecision:
        record = self.journal.get(operation.key)
        if record is None:
            return RecoveryDecision(operation, "unknown", "operation_not_journaled")
        if record.state in {"completed", "failed", "cancelled", "timed_out", "stalled", "stopped"}:
            return RecoveryDecision(operation, "terminal", record.terminal_reason or record.state)
        observed = self.units.inspect(record.unit_name)
        if observed is not None and record.pid is not None and observed.matches(record):
            if observed.active:
                return RecoveryDecision(operation, "running", "same_unit_identity")
            if observed.cgroup_empty:
                self.journal.save(replace(record, state="recovery_required", terminal_reason="unit_ended"))
                return RecoveryDecision(operation, "recovery_required", "unit_ended")
        if observed is not None and observed.active:
            self.journal.save(replace(record, state="stop_unconfirmed", terminal_reason="identity_mismatch"))
            return RecoveryDecision(operation, "blocked", "identity_mismatch")
        self.journal.save(replace(record, state="recovery_required", terminal_reason="launch_or_run_interrupted"))
        return RecoveryDecision(operation, "recovery_required", "launch_or_run_interrupted")
