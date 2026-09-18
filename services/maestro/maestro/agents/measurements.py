"""Verified agent usage and context measurements."""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


class MeasurementError(ValueError):
    pass


@dataclass(frozen=True)
class ContextPolicy:
    warning_percent: float = 75
    handoff_percent: float = 85
    resume_below_percent: float = 70
    sample_interval_seconds: float = 10
    stale_after_seconds: float = 30
    def __post_init__(self) -> None:
        if not 0 < self.resume_below_percent < self.warning_percent < self.handoff_percent < 100:
            raise MeasurementError("context thresholds are invalid")
        if self.sample_interval_seconds <= 0 or self.stale_after_seconds < self.sample_interval_seconds:
            raise MeasurementError("context sampling policy is invalid")


@dataclass(frozen=True)
class ContextReading:
    segment_id: str
    limit_tokens: int | None
    used_tokens: int | None
    quality: str
    observed_at: float
    source: str
    def __post_init__(self) -> None:
        if not isinstance(self.segment_id, str) or not self.segment_id or not isinstance(self.source, str) or not self.source:
            raise MeasurementError("context provenance is invalid")
        if self.quality not in {"reported", "estimated", "unavailable"}:
            raise MeasurementError("measurement quality is invalid")
        if self.limit_tokens is not None and self.limit_tokens <= 0:
            raise MeasurementError("context limit is invalid")
        if self.used_tokens is not None and self.used_tokens < 0:
            raise MeasurementError("context use is invalid")
        if self.quality == "unavailable" and (self.limit_tokens is not None or self.used_tokens is not None):
            raise MeasurementError("unavailable context must not invent a value")

    @property
    def used_percent(self) -> float | None:
        if self.limit_tokens is None or self.used_tokens is None:
            return None
        return self.used_tokens * 100 / self.limit_tokens

    def classification(self, policy: ContextPolicy, *, now: float | None = None) -> str:
        now = monotonic() if now is None else now
        if self.quality == "unavailable" or now - self.observed_at > policy.stale_after_seconds:
            return "unknown"
        percent = self.used_percent
        if percent is None:
            return "unknown"
        if percent >= policy.handoff_percent:
            return "handoff"
        if percent >= policy.warning_percent:
            return "warning"
        return "normal"


@dataclass(frozen=True)
class UsageMeasurement:
    session_id: str
    source_event_id: str
    active_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    quality: str
    source: str
    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str) or not self.session_id or not isinstance(self.source_event_id, str) or not self.source_event_id or not isinstance(self.source, str) or not self.source:
            raise MeasurementError("usage provenance is invalid")
        if self.quality not in {"reported", "estimated", "unavailable"} or self.active_seconds < 0:
            raise MeasurementError("usage measurement is invalid")
        if any(value is not None and value < 0 for value in (self.input_tokens, self.output_tokens)):
            raise MeasurementError("token measurement is invalid")

    @property
    def provenance_key(self) -> tuple[str, str, str]:
        """Stable producer event identity used for durable retry deduplication."""
        return (self.session_id, self.source, self.source_event_id)
