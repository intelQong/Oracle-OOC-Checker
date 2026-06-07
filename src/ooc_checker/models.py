"""Shared checker data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass

AVAILABLE = "AVAILABLE"


@dataclass(frozen=True)
class AvailabilityResult:
    """A normalized capacity result for one availability/fault-domain row."""

    availability_domain: str
    fault_domain: str | None
    shape: str
    ocpus: float
    memory_gb: float
    status: str
    available_count: int | None

    @property
    def is_available(self) -> bool:
        return self.status == AVAILABLE and (self.available_count is None or self.available_count > 0)

    def to_dict(self) -> dict[str, object]:
        return asdict(self) | {"is_available": self.is_available}
