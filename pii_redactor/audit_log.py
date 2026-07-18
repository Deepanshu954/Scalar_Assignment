# writes out what we redacted and where

from __future__ import annotations

import csv
from pathlib import Path

from .models import EntitySpan, Replacement, TextUnit
from .utils import normalize_entity, normalize_space


class AuditRowBuilder:
    """Build serializable audit rows from spans and replacement mappings."""

    def build(
        self,
        units: list[TextUnit],
        spans_by_unit: dict[str, list[EntitySpan]],
        replacement_lookup: dict[tuple[str, str], Replacement],
    ) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for unit in units:
            for span in spans_by_unit.get(unit.id, []):
                replacement = replacement_lookup[(span.entity_type, normalize_entity(span.text))]
                rows.append(
                    {
                        "unit_id": unit.id,
                        "part": unit.part,
                        "entity_type": span.entity_type,
                        "detector": span.detector,
                        "confidence": f"{span.confidence:.2f}",
                        "original": normalize_space(span.text),
                        "replacement": replacement.fake_value,
                        "context": span.context,
                    }
                )
        return rows


class CsvAuditWriter:
    """Write audit rows to CSV."""

    FIELDS = ["unit_id", "part", "entity_type", "detector", "confidence", "original", "replacement", "context"]

    def write(self, rows: list[dict[str, str]], audit_path: str | Path) -> None:
        path = Path(audit_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(rows)
