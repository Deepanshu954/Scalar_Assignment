# data classes for evaluation results

from __future__ import annotations

from dataclasses import dataclass

from .models import EntitySpan


@dataclass(frozen=True)
class GoldEntity:
    entity_type: str
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class GoldCase:
    name: str
    text: str
    labels: list[GoldEntity]
    source: str = ""


@dataclass(frozen=True)
class BoundaryError:
    entity_type: str
    predicted: str
    expected: str
    case_name: str


@dataclass(frozen=True)
class TypeMismatch:
    predicted_type: str
    expected_type: str
    text: str
    case_name: str


@dataclass(frozen=True)
class CaseEvaluation:
    case_name: str
    true_positives: list[tuple[EntitySpan, GoldEntity]]
    false_positives: list[EntitySpan]
    false_negatives: list[GoldEntity]
    boundary_errors: list[BoundaryError]
    type_mismatches: list[TypeMismatch]
