# loads the hand-labeled gold set from JSON

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluation_models import GoldCase, GoldEntity


class GoldLabelLoader:
    """Load gold cases from JSON and resolve label spans."""

    def load(self, path: str | Path) -> list[GoldCase]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return [self._case_from_dict(case) for case in data.get("cases", [])]

    def _case_from_dict(self, data: dict[str, Any]) -> GoldCase:
        text = data["text"]
        labels = [self._label_from_dict(text, label) for label in data.get("labels", [])]
        return GoldCase(name=data["name"], text=text, labels=labels, source=data.get("source", ""))

    def _label_from_dict(self, case_text: str, label: dict[str, Any]) -> GoldEntity:
        value = label["text"]
        start = label.get("start")
        end = label.get("end")
        if start is None or end is None:
            start = case_text.find(value)
            if start < 0:
                raise ValueError(f"Gold label text not found in case: {value!r}")
            end = start + len(value)
        return GoldEntity(label["type"], value, int(start), int(end))
