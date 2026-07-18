# detects names by looking for context clues like "Contact Person:"

from __future__ import annotations

import re
from typing import Any

from .models import EntitySpan
from .redaction_rules import RedactionRules
from .scanner_protocol import PiiScanner
from .utils import span_context


class NerDetector(PiiScanner):
    """Tier 3 optional NER plus local context rules."""

    PERSON_TITLE_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+(?:[A-Z]\.|[A-Z][a-z]+)){1,3}\b")
    UPPER_PERSON_RE = re.compile(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,}){1,4}\b")

    def __init__(self, rules: RedactionRules | None = None, use_optional_ner: bool = True) -> None:
        self.rules = rules or RedactionRules()
        self.use_optional_ner = use_optional_ner
        self.gliner_model = self._load_gliner() if use_optional_ner else None
        self.spacy_nlp = self._load_spacy() if use_optional_ner and self.gliner_model is None else None

    def _load_gliner(self) -> Any | None:
        try:
            from gliner import GLiNER  # type: ignore

            return GLiNER.from_pretrained("urchade/gliner_small-v2.1")
        except Exception:
            return None

    def _load_spacy(self) -> Any | None:
        # optional - tries to load spacy if available but works fine without it
        try:
            import spacy  # type: ignore

            for model in ("en_core_web_sm", "en_core_web_md"):
                try:
                    return spacy.load(model)
                except Exception:
                    continue
        except Exception:
            return None
        return None

    @property
    def tier(self) -> int:
        return 3

    @property
    def name(self) -> str:
        return "NerDetector"

    def scan(self, text: str, unit_id: str = "", part: str = "", context: dict[str, Any] | None = None) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        spans.extend(self._scan_optional_ner(text, unit_id, part))
        spans.extend(self._scan_context_rules(text, unit_id, part))
        return spans

    def _scan_optional_ner(self, text: str, unit_id: str, part: str) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        if self.gliner_model is not None and text.strip():
            try:
                entities = self.gliner_model.predict_entities(text, ["person name", "organization", "physical address"], threshold=0.4)
                for ent in entities:
                    label = ent.get("label")
                    entity_type = "person" if label == "person name" else "company" if label == "organization" else "address" if label == "physical address" else None
                    if entity_type:
                        start, end = ent.get("start", 0), ent.get("end", 0)
                        spans.append(EntitySpan(entity_type, ent.get("text", ""), start, end, float(ent.get("score", 0.85)), "gliner_zero_shot", span_context(text, start, end), unit_id, part))
            except Exception:
                pass

        if self.spacy_nlp is not None and text.strip():
            try:
                doc = self.spacy_nlp(text)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        spans.append(EntitySpan("person", ent.text, ent.start_char, ent.end_char, 0.72, "spacy_person", span_context(text, ent.start_char, ent.end_char), unit_id, part))
            except Exception:
                pass
        return spans

    def _scan_context_rules(self, text: str, unit_id: str, part: str) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        promoter_index = text.upper().find("OUR PROMOTERS:")
        if promoter_index >= 0:
            offset = promoter_index + len("OUR PROMOTERS:")
            for match in self.UPPER_PERSON_RE.finditer(text[offset:]):
                start, end = offset + match.start(), offset + match.end()
                value = text[start:end]
                if not any(term in value for term in self.rules.upper_person_exclusion_terms) and 2 <= len(value.split()) <= 4:
                    spans.append(EntitySpan("person", value, start, end, 0.87, "promoter_uppercase_rule", span_context(text, start, end), unit_id, part))

        for match in self.PERSON_TITLE_RE.finditer(text):
            context = text[max(0, match.start() - 80) : min(len(text), match.end() + 80)].lower()
            if any(cue in context for cue in self.rules.person_context_cues) and match.group(0) not in self.rules.person_stop_phrases:
                spans.append(EntitySpan("person", match.group(0), match.start(), match.end(), 0.78, "person_context_regex", span_context(text, match.start(), match.end()), unit_id, part))
        return spans
