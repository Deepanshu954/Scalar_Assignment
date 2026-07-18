# shared data classes for the pipeline

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PipelineMode(str, Enum):
    """Execution mode for the redaction pipeline."""

    MUTATION = "mutation"
    VALIDATION = "validation"


# higher number = higher priority when spans overlap
ENTITY_PRIORITY = {
    "api_key": 105,
    "token": 104,
    "email": 100,
    "url": 98,
    "credit_card": 95,
    "ssn": 94,
    "ip_address": 93,
    "phone": 92,
    "dob": 85,
    "address": 75,
    "company": 65,
    "person": 55,
}


@dataclass(frozen=True)
class RunSegment:
    """Mapping between a DOCX run and offsets in a text unit."""

    run: Any
    start: int
    end: int


@dataclass
class TextUnit:
    """Paragraph-like content extracted from body/header/footer/table text."""

    id: str
    part: str
    text: str
    run_segments: list[RunSegment]


@dataclass(frozen=True)
class EntitySpan:
    """Detected entity span inside a TextUnit."""

    entity_type: str
    text: str
    start: int
    end: int
    confidence: float
    detector: str
    context: str = ""
    unit_id: str = ""
    part: str = ""

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Replacement:
    original: str
    entity_type: str
    fake_value: str


@dataclass(frozen=True)
class MetricResult:
    entity_type: str
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    accuracy: float
    f1: float
    boundary_errors: int = 0
