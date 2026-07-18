# once we find an entity, look for it everywhere else in the doc too

from __future__ import annotations

import re

from .conflict_resolver import ConflictResolver
from .models import EntitySpan, Replacement, TextUnit
from .utils import normalize_entity, normalize_space, span_context


class SpanPropagator:
    """Propagate already detected entities by exact text match."""

    PROPAGATE_TYPES = {
        "api_key",
        "token",
        "email",
        "phone",
        "ssn",
        "credit_card",
        "ip_address",
        "dob",
        "address",
        "company",
        "person",
        "url",
    }

    def add_propagation(
        self,
        units: list[TextUnit],
        spans_by_unit: dict[str, list[EntitySpan]],
        lookup: dict[tuple[str, str], Replacement],
    ) -> None:
        candidates: list[tuple[str, str, str]] = []
        for (entity_type, normalized), replacement in lookup.items():
            original = normalize_space(replacement.original)
            if entity_type in self.PROPAGATE_TYPES and len(original) >= 5:
                candidates.append((entity_type, normalized, original))
        candidates.sort(key=lambda item: len(item[2]), reverse=True)

        for unit in units:
            propagated = list(spans_by_unit.get(unit.id, []))
            existing = {(span.entity_type, span.start, span.end, normalize_entity(span.text)) for span in propagated}
            for entity_type, normalized, original in candidates:
                for match in re.finditer(re.escape(original), unit.text, flags=re.IGNORECASE):
                    key = (entity_type, match.start(), match.end(), normalized)
                    if key in existing:
                        continue
                    propagated.append(
                        EntitySpan(
                            entity_type,
                            unit.text[match.start() : match.end()],
                            match.start(),
                            match.end(),
                            0.90,
                            "exact_propagation",
                            span_context(unit.text, match.start(), match.end()),
                            unit.id,
                            unit.part,
                        )
                    )
                    existing.add(key)
            spans_by_unit[unit.id] = ConflictResolver.resolve(propagated)
