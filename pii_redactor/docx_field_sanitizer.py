# cleans up hyperlink fields in the DOCX XML after redaction
# Word stores emails/urls in the XML too, not just the visible text

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from .models import Replacement


class DocxFieldSanitizer:
    """Remove original structured PII from hyperlink fields left by Word."""

    FIELD_TYPES = {"email", "url"}

    def sanitize(self, docx_path: str | Path, replacements: list[Replacement]) -> None:
        relevant = [
            replacement
            for replacement in replacements
            if replacement.entity_type in self.FIELD_TYPES and replacement.original and replacement.fake_value
        ]
        if not relevant:
            return

        path = Path(docx_path)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if self._should_clean(item.filename):
                    data = self._clean_xml_text(data, relevant)
                target.writestr(item, data)
        temp_path.replace(path)

    def _should_clean(self, filename: str) -> bool:
        return filename.startswith("word/") and (filename.endswith(".xml") or filename.endswith(".rels"))

    def _clean_xml_text(self, data: bytes, replacements: list[Replacement]) -> bytes:
        text = data.decode("utf-8", errors="ignore")
        for replacement in replacements:
            fake_value = self._field_safe_value(replacement)
            text = text.replace(replacement.original, escape(fake_value, {'"': "&quot;"}))
        return text.encode("utf-8")

    def _field_safe_value(self, replacement: Replacement) -> str:
        if replacement.entity_type == "url" and replacement.fake_value.startswith("["):
            return "example.com/redacted"
        return replacement.fake_value
