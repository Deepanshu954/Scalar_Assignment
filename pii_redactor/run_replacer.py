# handles the actual text replacement in DOCX runs
# this is the tricky part - DOCX splits text across multiple runs

from __future__ import annotations

from .models import EntitySpan, Replacement, TextUnit


class RunLevelReplacer:
    """Apply replacement spans while preserving the first affected run's style."""

    def apply_all(
        self,
        units: list[TextUnit],
        spans_by_unit: dict[str, list[EntitySpan]],
        replacement_lookup: dict[tuple[str, str], Replacement],
        key_for_span,
    ) -> None:
        for unit in units:
            spans = spans_by_unit.get(unit.id, [])
            if not spans:
                continue
            replacements = {span: replacement_lookup[key_for_span(span)] for span in spans}
            self.apply_spans(unit, spans, replacements)

    def apply_spans(self, unit: TextUnit, spans: list[EntitySpan], replacements: dict[EntitySpan, Replacement]) -> None:
        for span in sorted(spans, key=lambda item: item.start, reverse=True):
            impacted_segments = [
                segment
                for segment in unit.run_segments
                if segment.end > span.start and segment.start < span.end
            ]
            for index, segment in enumerate(impacted_segments):
                run_text = segment.run.text
                local_start = max(span.start - segment.start, 0)
                local_end = min(span.end - segment.start, len(run_text))
                replacement_text = replacements[span].fake_value if index == 0 else ""
                segment.run.text = run_text[:local_start] + replacement_text + run_text[local_end:]
