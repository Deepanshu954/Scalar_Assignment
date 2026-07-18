# filters out stuff that looks like PII but isn't (SEBI, NSE, etc)

from __future__ import annotations

from typing import Sequence

from .models import EntitySpan
from .redaction_rules import DEFAULT_PUBLIC_ORGANIZATIONS, RedactionRules
from .utils import normalize_entity


class ExclusionFilter:
    """Filter spans that are known false positives in the selected domain."""

    def __init__(
        self,
        public_organizations: set[str] | Sequence[str] | None = None,
        rules: RedactionRules | None = None,
    ) -> None:
        self.rules = rules or RedactionRules.load()
        organizations = public_organizations or self.rules.public_organizations or DEFAULT_PUBLIC_ORGANIZATIONS
        self.public_orgs = {normalize_entity(org) for org in organizations}
        self.person_stop_words = {normalize_entity(word) for word in self.rules.person_stop_words}
        self.person_stop_phrases = {normalize_entity(phrase) for phrase in self.rules.person_stop_phrases}
        self.non_company_phrases = {normalize_entity(phrase) for phrase in self.rules.non_company_phrases}

    # these keep showing up as false positives
    def is_excluded(self, span: EntitySpan) -> bool:
        norm = normalize_entity(span.text)
        if norm in self.public_orgs or span.text.lower() in self.public_orgs:
            return True
        if span.entity_type == "person":
            tokens = set(norm.split())
            return norm in self.person_stop_phrases or bool(tokens & self.person_stop_words)
        if span.entity_type == "company":
            return any(phrase and phrase in norm for phrase in self.non_company_phrases)
        return False

    def filter_spans(self, spans: Sequence[EntitySpan]) -> list[EntitySpan]:
        return [span for span in spans if not self.is_excluded(span)]
