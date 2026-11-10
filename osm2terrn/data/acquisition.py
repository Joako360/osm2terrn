"""Result model for provider-backed data acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LayerAcquisitionStatus = Literal["not_requested", "empty", "available", "failed"]
AcquisitionFailureCategory = Literal["temporary", "permanent", "unknown"]
AcquisitionFailureStage = Literal["acquisition", "transformation"]
AcquisitionSource = Literal["none", "query", "cache"]


@dataclass(frozen=True, slots=True)
class LayerAcquisitionResult:
    """Describe whether a requested data layer was acquired and transformed."""

    status: LayerAcquisitionStatus
    source: AcquisitionSource = "query"
    failure_category: AcquisitionFailureCategory | None = None
    failure_stage: AcquisitionFailureStage | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.status == "failed":
            if self.failure_category is None or self.failure_stage is None:
                raise ValueError("Failed layer acquisition requires a category and stage")
            if not self.diagnostic or not self.diagnostic.strip():
                raise ValueError("Failed layer acquisition requires a diagnostic")
        elif any(
            value is not None
            for value in (self.failure_category, self.failure_stage, self.diagnostic)
        ):
            raise ValueError("Successful layer acquisition cannot include failure details")
        if self.status == "not_requested" and self.source != "none":
            raise ValueError("Not-requested layers must use source='none'")
