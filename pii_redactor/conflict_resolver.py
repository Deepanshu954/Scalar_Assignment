# resolves overlapping detections

from __future__ import annotations

from typing import Sequence

from .models import ENTITY_PRIORITY, EntitySpan
from .utils import normalize_entity


class ConflictResolver:
    """Resolve overlapping detections using type priority, length, and confidence."""

    @staticmethod
    def resolve(spans: Sequence[EntitySpan]) -> list[EntitySpan]:
        unique: dict[tuple[int, int, str, str], EntitySpan] = {}
        for span in spans:
            key = (span.start, span.end, span.entity_type, normalize_entity(span.text))
            if key not in unique or span.confidence > unique[key].confidence:
                unique[key] = span

        # sort by priority, then longest span wins
        sorted_spans = sorted(
            unique.values(),
            key=lambda span: (-ENTITY_PRIORITY.get(span.entity_type, 0), -span.length, -span.confidence, span.start),
        )
        accepted: list[EntitySpan] = []
        for span in sorted_spans:
            if not any(span.start < existing.end and existing.start < span.end for existing in accepted):
                accepted.append(span)
        return sorted(accepted, key=lambda span: (span.start, span.end))
