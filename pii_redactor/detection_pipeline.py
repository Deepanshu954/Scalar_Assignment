# main pipeline - chains regex, entropy, and context detectors together

from __future__ import annotations

from pathlib import Path

from .conflict_resolver import ConflictResolver
from .context_recognizers import NerDetector
from .entropy_recognizer import EntropyDetector
from .exclusion_filter import ExclusionFilter
from .models import EntitySpan
from .redaction_rules import RedactionRules
from .scanner_protocol import PiiScanner
from .structured_recognizers import RegexDetector


class TieredPipelineScanner:
    """Orchestrate regex, entropy, context/NER, exclusion, and conflict resolution."""

    def __init__(self, rules: RedactionRules | None = None, scanners: list[PiiScanner] | None = None) -> None:
        self.rules = rules or RedactionRules()
        self.scanners = scanners or [RegexDetector(self.rules), EntropyDetector(), NerDetector(self.rules)]
        self.exclusion_filter = ExclusionFilter(rules=self.rules)

    def scan_text(self, text: str, unit_id: str = "", part: str = "") -> list[EntitySpan]:
        all_spans: list[EntitySpan] = []
        for scanner in self.scanners:
            all_spans.extend(scanner.scan(text, unit_id=unit_id, part=part))
        filtered_spans = self.exclusion_filter.filter_spans(all_spans)
        return ConflictResolver.resolve(filtered_spans)


class PiiRecognizer(TieredPipelineScanner):
    """Backward-compatible recognizer interface used by the CLI and tests."""

    def __init__(
        self,
        use_optional_ner: bool = True,
        rules: RedactionRules | None = None,
        rules_path: str | Path | None = None,
        profile: str = "prospectus",
    ) -> None:
        loaded_rules = rules or RedactionRules.load(rules_path, profile)
        scanners = [RegexDetector(loaded_rules), EntropyDetector(), NerDetector(loaded_rules, use_optional_ner)]
        super().__init__(rules=loaded_rules, scanners=scanners)

    def detect_text(self, text: str, unit_id: str = "", part: str = "") -> list[EntitySpan]:
        return self.scan_text(text, unit_id=unit_id, part=part)
