# calculates precision, recall, f1 from match results

from __future__ import annotations

from collections import Counter

from .evaluation_models import CaseEvaluation
from .models import MetricResult


class MetricCalculator:
    """Calculate per-type and overall precision/recall/accuracy/F1."""

    def calculate(self, case_results: list[CaseEvaluation]) -> list[MetricResult]:
        tp = Counter()
        fp = Counter()
        fn = Counter()
        boundary = Counter()

        for result in case_results:
            for prediction, _gold in result.true_positives:
                tp[prediction.entity_type] += 1
            for prediction in result.false_positives:
                fp[prediction.entity_type] += 1
            for gold in result.false_negatives:
                fn[gold.entity_type] += 1
            for error in result.boundary_errors:
                boundary[error.entity_type] += 1

        entity_types = sorted(set(tp) | set(fp) | set(fn))
        metrics = [self._metric(entity_type, tp[entity_type], fp[entity_type], fn[entity_type], boundary[entity_type]) for entity_type in entity_types]
        metrics.append(self._metric("overall_micro", sum(tp.values()), sum(fp.values()), sum(fn.values()), sum(boundary.values())))
        return metrics

    def _metric(self, entity_type: str, tp: int, fp: int, fn: int, boundary_errors: int) -> MetricResult:
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        accuracy = tp / (tp + fp + fn) if tp + fp + fn else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return MetricResult(entity_type, tp, fp, fn, precision, recall, accuracy, f1, boundary_errors)
