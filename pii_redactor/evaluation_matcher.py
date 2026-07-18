# strict matching - compares predictions against gold labels

from __future__ import annotations

from .evaluation_models import BoundaryError, CaseEvaluation, GoldCase, GoldEntity, TypeMismatch
from .models import EntitySpan
from .utils import normalize_entity


class ExactEntityMatcher:
    """Score exact normalized type+text matches and report boundary/type errors."""

    def evaluate_case(self, case: GoldCase, predictions: list[EntitySpan]) -> CaseEvaluation:
        matched_gold: set[int] = set()
        matched_predictions: set[int] = set()
        true_positives: list[tuple[EntitySpan, GoldEntity]] = []

        for pred_index, prediction in enumerate(predictions):
            for gold_index, gold in enumerate(case.labels):
                if gold_index in matched_gold:
                    continue
                if prediction.entity_type == gold.entity_type and normalize_entity(prediction.text) == normalize_entity(gold.text):
                    true_positives.append((prediction, gold))
                    matched_predictions.add(pred_index)
                    matched_gold.add(gold_index)
                    break

        false_positives = [prediction for index, prediction in enumerate(predictions) if index not in matched_predictions]
        false_negatives = [gold for index, gold in enumerate(case.labels) if index not in matched_gold]

        boundary_errors = self._boundary_errors(case.name, false_positives, false_negatives)
        type_mismatches = self._type_mismatches(case.name, false_positives, false_negatives)

        return CaseEvaluation(
            case.name,
            true_positives,
            false_positives,
            false_negatives,
            boundary_errors,
            type_mismatches,
        )

    def _boundary_errors(
        self,
        case_name: str,
        false_positives: list[EntitySpan],
        false_negatives: list[GoldEntity],
    ) -> list[BoundaryError]:
        errors: list[BoundaryError] = []
        for prediction in false_positives:
            for gold in false_negatives:
                if prediction.entity_type == gold.entity_type and self._overlaps(prediction.start, prediction.end, gold.start, gold.end):
                    errors.append(BoundaryError(prediction.entity_type, prediction.text, gold.text, case_name))
                    break
        return errors

    def _type_mismatches(
        self,
        case_name: str,
        false_positives: list[EntitySpan],
        false_negatives: list[GoldEntity],
    ) -> list[TypeMismatch]:
        mismatches: list[TypeMismatch] = []
        for prediction in false_positives:
            pred_norm = normalize_entity(prediction.text)
            for gold in false_negatives:
                if pred_norm == normalize_entity(gold.text) and prediction.entity_type != gold.entity_type:
                    mismatches.append(TypeMismatch(prediction.entity_type, gold.entity_type, prediction.text, case_name))
                    break
        return mismatches

    def _overlaps(self, left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
        return left_start < right_end and right_start < left_end
