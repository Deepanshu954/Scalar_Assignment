# top-level service that ties everything together

from __future__ import annotations

from pathlib import Path

from docx import Document

from .audit_log import AuditRowBuilder, CsvAuditWriter
from .docx_field_sanitizer import DocxFieldSanitizer
from .exclusion_filter import ExclusionFilter
from .indexer import DocxTextIndexer
from .models import EntitySpan, PipelineMode, Replacement, TextUnit
from .replacement_generator import ReplacementGenerator
from .run_replacer import RunLevelReplacer
from .span_propagator import SpanPropagator
from .detection_pipeline import TieredPipelineScanner
from .utils import normalize_entity


class DocxRedactor:
    """Coordinate indexing, detection, replacement, mutation, and audit logging."""

    def __init__(
        self,
        scanner: TieredPipelineScanner | None = None,
        detector: TieredPipelineScanner | None = None,
        generator: ReplacementGenerator | None = None,
        exclusion_filter: ExclusionFilter | None = None,
        indexer: DocxTextIndexer | None = None,
        propagator: SpanPropagator | None = None,
        replacer: RunLevelReplacer | None = None,
        field_sanitizer: DocxFieldSanitizer | None = None,
        audit_builder: AuditRowBuilder | None = None,
        audit_writer: CsvAuditWriter | None = None,
        mode: PipelineMode | str = PipelineMode.MUTATION,
    ) -> None:
        self.scanner = scanner or detector or TieredPipelineScanner()
        self.generator = generator or ReplacementGenerator()
        rules = getattr(self.scanner, "rules", None)
        self.exclusion_filter = exclusion_filter or ExclusionFilter(rules=rules)
        self.indexer = indexer or DocxTextIndexer()
        self.propagator = propagator or SpanPropagator()
        self.replacer = replacer or RunLevelReplacer()
        self.field_sanitizer = field_sanitizer or DocxFieldSanitizer()
        self.audit_builder = audit_builder or AuditRowBuilder()
        self.audit_writer = audit_writer or CsvAuditWriter()
        self.mode = PipelineMode(mode)

    def redact_docx(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        audit_path: str | Path | None = None,
        mode: PipelineMode | str | None = None,
    ) -> list[dict[str, str]]:
        current_mode = PipelineMode(mode) if mode is not None else self.mode
        doc = Document(str(input_path))
        units = self.indexer.index(doc)

        spans_by_unit, replacement_lookup = self._detect_and_prepare(units)
        self.propagator.add_propagation(units, spans_by_unit, replacement_lookup)
        self._apply_allowlist(spans_by_unit)

        audit_rows = self.audit_builder.build(units, spans_by_unit, replacement_lookup)

        if output_path and current_mode == PipelineMode.MUTATION:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            self.replacer.apply_all(units, spans_by_unit, replacement_lookup, self._key_for_span)
            doc.save(str(output))
            self.field_sanitizer.sanitize(output, list(replacement_lookup.values()))

        if audit_path:
            self.audit_writer.write(audit_rows, audit_path)

        return audit_rows

    def _detect_and_prepare(
        self,
        units: list[TextUnit],
    ) -> tuple[dict[str, list[EntitySpan]], dict[tuple[str, str], Replacement]]:
        spans_by_unit: dict[str, list[EntitySpan]] = {}
        lookup: dict[tuple[str, str], Replacement] = {}
        for unit in units:
            spans = self.scanner.scan_text(unit.text, unit.id, unit.part)
            spans_by_unit[unit.id] = spans
            for span in spans:
                lookup[self._key_for_span(span)] = self.generator.replacement_for(span.entity_type, span.text)
        return spans_by_unit, lookup

    def _apply_allowlist(self, spans_by_unit: dict[str, list[EntitySpan]]) -> None:
        for unit_id, spans in list(spans_by_unit.items()):
            spans_by_unit[unit_id] = self.exclusion_filter.filter_spans(spans)

    def _key_for_span(self, span: EntitySpan) -> tuple[str, str]:
        return (span.entity_type, normalize_entity(span.text))

    def _apply_spans(self, unit: TextUnit, spans: list[EntitySpan], replacements: dict[EntitySpan, Replacement]) -> None:
        """Backward-compatible delegate for focused unit tests."""
        self.replacer.apply_spans(unit, spans, replacements)


DocxRedactionService = DocxRedactor
