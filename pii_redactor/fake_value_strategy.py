# picks which fake value to use for each entity type

from __future__ import annotations

from . import fake_value_catalog as catalog
from .utils import normalize_entity, stable_index


class FakeValueStrategy:
    """Generate a syntactically plausible fake value for one entity."""

    def generate(self, entity_type: str, original: str) -> str:
        key = f"{entity_type}:{normalize_entity(original)}"
        # TODO: add more variety to fake names at some point
        if entity_type == "person":
            return catalog.PERSON_NAMES[stable_index(key, len(catalog.PERSON_NAMES))]
        if entity_type == "company":
            return f"{catalog.COMPANY_BASES[stable_index(key, len(catalog.COMPANY_BASES))]} {self._company_suffix(original)}".strip()
        if entity_type == "email":
            return f"user{stable_index(key, 9000) + 1000}@example.com"
        if entity_type == "phone":
            national = str(7000000000 + stable_index(key, 1999999999))
            return f"+91 {national[:5]} {national[5:]}"
        if entity_type == "address":
            return catalog.ADDRESSES[stable_index(key, len(catalog.ADDRESSES))]
        if entity_type == "dob":
            return catalog.DOB_VALUES[stable_index(key, len(catalog.DOB_VALUES))]
        if entity_type == "ssn":
            return catalog.SSN_VALUES[stable_index(key, len(catalog.SSN_VALUES))]
        if entity_type == "credit_card":
            return catalog.CARD_VALUES[stable_index(key, len(catalog.CARD_VALUES))]
        if entity_type == "ip_address":
            return catalog.IP_VALUES[stable_index(key, len(catalog.IP_VALUES))]
        return f"[REDACTED_{entity_type.upper()}]"

    def _company_suffix(self, original: str) -> str:
        upper = original.upper()
        suffixes = [
            ("PRIVATE LIMITED", "Private Limited"),
            ("SECURITIES LIMITED", "Securities Limited"),
            ("RATINGS LIMITED", "Ratings Limited"),
            ("FINANCE LIMITED", "Finance Limited"),
            ("BANK OF INDIA", "Bank of India"),
            ("BANK LIMITED", "Bank Limited"),
            ("LIMITED", "Limited"),
            ("LLP", "LLP"),
            ("N.A", "N.A."),
        ]
        for marker, suffix in suffixes:
            if marker in upper:
                return suffix
        return ""
