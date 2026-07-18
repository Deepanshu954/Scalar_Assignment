# catches high-entropy strings like API keys and tokens

from __future__ import annotations

import math
import re
from typing import Any

from .models import EntitySpan
from .scanner_protocol import PiiScanner
from .utils import span_context


# shannon entropy formula - measures randomness of a string
def calculate_shannon_entropy(data: str) -> float:
    # calculate shannon entropy for a string
    if not data:
        return 0.0
    entropy = 0.0
    frequencies: dict[str, int] = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        probability = count / len(data)
        entropy -= probability * math.log2(probability)
    return entropy


class EntropyDetector(PiiScanner):
    """Tier 2 recognizer for API keys, bearer tokens, and credentials."""

    TOKEN_PREFIX_RE = re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|auth[_-]?token|bearer|private[_-]?key|client[_-]?secret)\s*[:=]\s*"
        r"(?P<token>[A-Za-z0-9_\-\.]{16,256})\b"
    )
    GENERIC_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_\-]{20,128}\b")
    JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")

    def __init__(self, entropy_threshold: float = 3.7) -> None:
        self.entropy_threshold = entropy_threshold

    @property
    def tier(self) -> int:
        return 2

    @property
    def name(self) -> str:
        return "EntropyDetector"

    def scan(self, text: str, unit_id: str = "", part: str = "", context: dict[str, Any] | None = None) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        for match in self.JWT_RE.finditer(text):
            spans.append(EntitySpan("token", match.group(0), match.start(), match.end(), 0.98, "entropy_jwt", span_context(text, match.start(), match.end()), unit_id, part))
        for match in self.TOKEN_PREFIX_RE.finditer(text):
            start, end = match.span("token")
            if calculate_shannon_entropy(text[start:end]) >= 3.0:
                spans.append(EntitySpan("api_key", text[start:end], start, end, 0.95, "entropy_labeled_token", span_context(text, start, end), unit_id, part))
        for match in self.GENERIC_TOKEN_RE.finditer(text):
            token_text = match.group(0)
            if not token_text.isdigit() and not token_text.isalpha() and calculate_shannon_entropy(token_text) >= self.entropy_threshold:
                spans.append(EntitySpan("api_key", token_text, match.start(), match.end(), 0.90, "entropy_high_token", span_context(text, match.start(), match.end()), unit_id, part))
        return spans
