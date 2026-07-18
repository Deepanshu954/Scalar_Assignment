# config and domain-specific rules for what counts as PII

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "redaction_rules.json"

DEFAULT_PUBLIC_ORGANIZATIONS = {
    "bse",
    "bse limited",
    "nse",
    "national stock exchange of india limited",
    "sebi",
    "securities and exchange board of india",
    "rbi",
    "reserve bank of india",
    "sbi",
    "state bank of india",
    "sec",
    "securities and exchange commission",
    "nyse",
    "nasdaq",
    "federal reserve",
    "world bank",
    "imf",
    "international monetary fund",
    "mca",
    "ministry of corporate affairs",
}


class RedactionRules:
    """Configurable domain hints and stop words."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        d = data or {}
        self.company_suffixes = list(d.get("company_suffixes", ["Private Limited", "Limited", "LLP", "Bank Limited", "N.A."]))
        self.address_cues = set(d.get("address_cues", ["road", "street", "avenue", "floor", "building", "office", "india"]))
        self.partial_address_cues = set(d.get("partial_address_cues", ["road", "street", "tower", "office"]))
        self.person_context_cues = set(d.get("person_context_cues", ["contact person", "director", "officer", "shareholder", "name:", "contact:"]))
        self.person_stop_words = set(d.get("person_stop_words", ["company", "office", "email", "telephone", "website", "director", "officer"]))
        self.person_stop_phrases = set(d.get("person_stop_phrases", ["Contact Person", "Registered Office", "Corporate Office"]))
        self.upper_person_exclusion_terms = set(d.get("upper_person_exclusion_terms", ["LIMITED", "PRIVATE", "LLP", "TRUST", "COMPANY"]))
        self.non_company_phrases = set(d.get("non_company_phrases", ["companies act"]))
        self.public_organizations = set(d.get("public_organizations", DEFAULT_PUBLIC_ORGANIZATIONS))

    @classmethod
    def load(cls, path: str | Path | None = None, profile: str = "prospectus") -> "RedactionRules":
        rules_path = Path(path) if path else DEFAULT_RULES_PATH
        if not rules_path.exists():
            return cls()
        data = json.loads(rules_path.read_text(encoding="utf-8"))
        base = data.get("generic", {})
        selected = data.get("profiles", {}).get(profile, {})
        merged = cls._deep_merge(base, selected)
        return cls(merged)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key] = [*merged[key], *value]
            else:
                merged[key] = value
        return merged
