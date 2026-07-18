# indexes paragraph text and run offsets
# kinda need this so we don't destroy all the bold/italic formatting
# gotta handle merged cells carefully or we get duplicates

from __future__ import annotations

from typing import Any

from .models import RunSegment, TextUnit


class DocxTextIndexer:
    """Indexes body, table, header, and footer text into paragraph-like units."""

    def index(self, doc: Any) -> list[TextUnit]:
        units: list[TextUnit] = []

        for idx, paragraph in enumerate(doc.paragraphs):
            units.append(self._make_unit(f"body_p{idx}", "body", paragraph))

        for table_idx, table in enumerate(doc.tables):
            self._index_table(units, table, f"body_t{table_idx}", "table")

        for section_idx, section in enumerate(doc.sections):
            for idx, paragraph in enumerate(section.header.paragraphs):
                units.append(self._make_unit(f"header_s{section_idx}_p{idx}", "header", paragraph))
            for table_idx, table in enumerate(section.header.tables):
                self._index_table(units, table, f"header_s{section_idx}_t{table_idx}", "header_table")

            for idx, paragraph in enumerate(section.footer.paragraphs):
                units.append(self._make_unit(f"footer_s{section_idx}_p{idx}", "footer", paragraph))
            for table_idx, table in enumerate(section.footer.tables):
                self._index_table(units, table, f"footer_s{section_idx}_t{table_idx}", "footer_table")

        return units

    def _index_table(self, units: list[TextUnit], table: Any, prefix: str, part: str) -> None:
        seen_cells: set[int] = set()
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                cell_key = id(cell._tc)
                if cell_key in seen_cells:
                    continue
                seen_cells.add(cell_key)
                cell_prefix = f"{prefix}_r{row_idx}_c{cell_idx}"
                for paragraph_idx, paragraph in enumerate(cell.paragraphs):
                    units.append(self._make_unit(f"{cell_prefix}_p{paragraph_idx}", part, paragraph))
                for nested_idx, nested_table in enumerate(cell.tables):
                    self._index_table(units, nested_table, f"{cell_prefix}_t{nested_idx}", part)

    def _make_unit(self, unit_id: str, part: str, paragraph: Any) -> TextUnit:
        segments: list[RunSegment] = []
        offset = 0
        for run in paragraph.runs:
            run_length = len(run.text)
            segments.append(RunSegment(run=run, start=offset, end=offset + run_length))
            offset += run_length
        return TextUnit(id=unit_id, part=part, text=paragraph.text, run_segments=segments)
