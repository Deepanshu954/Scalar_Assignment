# regex patterns for emails, phones, SSNs, credit cards, etc

from __future__ import annotations

import ipaddress
import re
from typing import Any, Sequence

from .models import EntitySpan
from .redaction_rules import RedactionRules
from .scanner_protocol import PiiScanner
from .utils import luhn_valid, span_context


class RegexDetector(PiiScanner):
    """Tier 1 deterministic recognizer for structured PII."""

    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    URL_RE = re.compile(r"\b(?:https?://|www\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?\b")
    SPACED_URL_RE = re.compile(
        r"\b(?:https?\s*:\s*/\s*/\s*)?www\s*\.\s*[A-Za-z0-9-]+(?:\s*\.\s*[A-Za-z]{2,})(?:/[^\s]*)?\b",
        re.IGNORECASE,
    )
    SSN_RE = re.compile(r"\b(?!000|666|9\d\d)\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b")
    IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
    # luhn check prevents random number sequences from matching
    CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
    DOB_RE = re.compile(
        r"(?i)\b(?:date\s+of\s+birth|dob|born\s+on|birth\s+date)\s*[:.-]?\s*"
        r"(?P<date>(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|"
        r"(?:(?:January|February|March|April|May|June|July|August|September|October|"
        r"November|December)\s+\d{1,2},\s+\d{4}))"
    )
    PINCODE_RE = re.compile(r"\b\d{3}\s?\d{3}\b")
    LABELLED_PHONE_RE = re.compile(r"(?i)\b(?:telephone|tel|mobile|phone|fax|contact)\s*[:.-]?\s*(?P<num>\+?\s*(?:\d[\d\s().-]{7,24}\d))")
    # indian phone numbers mostly start with +91
    COUNTRY_PHONE_RE = re.compile(r"(?<!\d)\+\s*91[\s().-]*(?:\d[\d\s().-]{7,20}\d)(?!\d)")

    def __init__(self, rules: RedactionRules | None = None) -> None:
        self.rules = rules or RedactionRules()
        self._compile_company_patterns(self.rules.company_suffixes)

    def _compile_company_patterns(self, suffixes: Sequence[str]) -> None:
        escaped = sorted((re.escape(suffix) for suffix in suffixes), key=len, reverse=True)
        suffix_pattern = "|".join(suffix.replace(r"\ ", r"\s+") for suffix in escaped) or r"Limited"
        upper_suffix_pattern = "|".join(suffix.upper().replace(r"\ ", r"\s+") for suffix in escaped) or r"LIMITED"
        self.company_re = re.compile(rf"\b[A-Z][A-Za-z0-9&'-]*(?:\s+[A-Z][A-Za-z0-9&'-]*){{0,9}}\s+(?:{suffix_pattern})\b")
        self.upper_company_re = re.compile(rf"\b[A-Z][A-Z0-9&'-]*(?:\s+[A-Z][A-Z0-9&'-]*){{0,9}}\s+(?:{upper_suffix_pattern})\b")

    @property
    def tier(self) -> int:
        return 1

    @property
    def name(self) -> str:
        return "RegexDetector"

    def scan(self, text: str, unit_id: str = "", part: str = "", context: dict[str, Any] | None = None) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        spans.extend(self._scan_basic_patterns(text, unit_id, part))
        spans.extend(self._scan_company_patterns(text, unit_id, part))
        spans.extend(self._detect_addresses(text, unit_id, part))
        return spans

    def _scan_basic_patterns(self, text: str, unit_id: str, part: str) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        for match in self.EMAIL_RE.finditer(text):
            spans.append(self._span("email", text, match.start(), match.end(), 0.99, "email_regex", unit_id, part))
        for match in self.URL_RE.finditer(text):
            spans.append(self._span("url", text, match.start(), match.end(), 0.95, "url_regex", unit_id, part))
        for match in self.SPACED_URL_RE.finditer(text):
            spans.append(self._span("url", text, match.start(), match.end(), 0.93, "url_spaced_regex", unit_id, part))
        for match in self.SSN_RE.finditer(text):
            spans.append(self._span("ssn", text, match.start(), match.end(), 0.98, "ssn_regex", unit_id, part))
        for match in self.IP_RE.finditer(text):
            try:
                ipaddress.ip_address(match.group(0))
            except ValueError:
                continue
            spans.append(self._span("ip_address", text, match.start(), match.end(), 0.98, "ip_regex", unit_id, part))
        for match in self.CREDIT_CARD_RE.finditer(text):
            digits = re.sub(r"\D", "", match.group(0))
            if luhn_valid(match.group(0)) and len(set(digits)) > 1:
                spans.append(self._span("credit_card", text, match.start(), match.end(), 0.97, "card_luhn_regex", unit_id, part))
        for match in self.DOB_RE.finditer(text):
            start, end = match.span("date")
            spans.append(self._span("dob", text, start, end, 0.96, "dob_context_regex", unit_id, part))
        for match in self.COUNTRY_PHONE_RE.finditer(text):
            if self._valid_phone(match.group(0), require_country=True):
                spans.append(self._span("phone", text, match.start(), match.end(), 0.96, "phone_country_regex", unit_id, part))
        for match in self.LABELLED_PHONE_RE.finditer(text):
            start, end = match.span("num")
            if self._valid_phone(text[start:end], require_country=False):
                spans.append(self._span("phone", text, start, end, 0.92, "phone_label_regex", unit_id, part))
        return spans

    def _scan_company_patterns(self, text: str, unit_id: str, part: str) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        patterns = ((self.company_re, 0.88, "company_suffix_regex"), (self.upper_company_re, 0.84, "upper_company_suffix_regex"))
        for regex, confidence, detector in patterns:
            for match in regex.finditer(text):
                if not any(phrase in match.group(0).lower() for phrase in self.rules.non_company_phrases):
                    spans.append(self._span("company", text, match.start(), match.end(), confidence, detector, unit_id, part))
        return spans

    def _valid_phone(self, raw: str, require_country: bool) -> bool:
        digits = re.sub(r"\D", "", raw)
        if digits.startswith("91") and len(digits) >= 12:
            return len(digits[2:]) == 10
        return not require_country and 8 <= len(digits) <= 11

    def _detect_addresses(self, text: str, unit_id: str, part: str) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        for label in ("Registered Office", "Corporate Office"):
            regex = re.compile(rf"(?i)\b{re.escape(label)}\s*:\s*(?P<addr>[^;\n]+)")
            for match in regex.finditer(text):
                start, end = match.span("addr")
                if self.PINCODE_RE.search(text[start:end]) and any(cue in text[start:end].lower() for cue in self.rules.address_cues):
                    spans.append(self._span("address", text, start, end, 0.95, "address_label_regex", unit_id, part))
        for match in self.PINCODE_RE.finditer(text):
            start, end = self._expand_address(text, match.start(), match.end())
            if any(cue in text[start:end].lower() for cue in self.rules.address_cues):
                spans.append(self._span("address", text, start, end, 0.80, "address_pincode_context", unit_id, part))
        return spans

    def _expand_address(self, text: str, pin_start: int, pin_end: int) -> tuple[int, int]:
        start = max(0, pin_start - 180)
        for boundary in (";", "\n"):
            idx = text.rfind(boundary, start, pin_start)
            if idx >= 0:
                start = max(start, idx + 1)
        colon = text.rfind(":", start, pin_start)
        if colon >= 0 and pin_start - colon < 170:
            start = colon + 1
        candidates = [idx for idx in (text.find(";", pin_end), text.find("\n", pin_end)) if idx >= 0]
        end = min(candidates) if candidates else min(len(text), pin_end + 80)
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        return start, end

    def _span(self, entity_type: str, text: str, start: int, end: int, confidence: float, detector: str, unit_id: str, part: str) -> EntitySpan:
        return EntitySpan(entity_type, text[start:end], start, end, confidence, detector, span_context(text, start, end), unit_id, part)
