# maps original PII to deterministic fake values
# same input always gives same output - important for consistency

from __future__ import annotations

from .fake_value_strategy import FakeValueStrategy
from .models import Replacement
from .utils import normalize_entity


class ReplacementGenerator:
    """Same original entity type and value always maps to the same fake value."""

    def __init__(self, strategy: FakeValueStrategy | None = None) -> None:
        self.strategy = strategy or FakeValueStrategy()
        self._mapping: dict[tuple[str, str], Replacement] = {}

    def replacement_for(self, entity_type: str, original: str) -> Replacement:
        key = (entity_type, normalize_entity(original))
        if key not in self._mapping:
            self._mapping[key] = Replacement(original, entity_type, self.strategy.generate(entity_type, original))
        return self._mapping[key]


FakeValueGenerator = ReplacementGenerator
