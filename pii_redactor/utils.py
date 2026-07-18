# helper functions for text normalization and stuff

import hashlib
import re


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_entity(value: str) -> str:
    return normalize_space(value).strip(" ,.;:()[]{}\"'").lower()


def stable_index(value: str, modulo: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % modulo


def span_context(text: str, start: int, end: int, radius: int = 44) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return normalize_space(text[left:right])


# standard luhn check - copied the algo from wikipedia basically
def luhn_valid(candidate: str) -> bool:
    digits = [int(ch) for ch in re.sub(r"\D", "", candidate)]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
