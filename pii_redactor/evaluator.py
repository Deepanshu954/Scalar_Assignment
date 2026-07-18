# runs the gold-label evaluation and writes the report

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from .detection_pipeline import PiiRecognizer
from .evaluation_matcher import ExactEntityMatcher
from .evaluation_report_writer import EvaluationReportWriter
from .gold_loader import GoldLabelLoader
from .metric_calculator import MetricCalculator
from .models import MetricResult


class RedactionEvaluator:
    """Evaluate detections against a tracked gold-label helper set."""

    DEFAULT_GOLD_PATH = Path(__file__).resolve().parents[1] / "evaluation_helper" / "gold_labels.json"

    def __init__(
        self,
        detector: PiiRecognizer | None = None,
        gold_path: str | Path | None = None,
        include_optional_ner: bool = False,
    ) -> None:
        self.detector = detector or PiiRecognizer(use_optional_ner=False)
        self.gold_path = Path(gold_path) if gold_path else self.DEFAULT_GOLD_PATH
        self.include_optional_ner = include_optional_ner
        self.loader = GoldLabelLoader()
        self.matcher = ExactEntityMatcher()
        self.calculator = MetricCalculator()
        self.report_writer = EvaluationReportWriter()

    def evaluate(self, detector: PiiRecognizer | None = None) -> tuple[list[MetricResult], list[Any], list[Any]]:
        active_detector = detector or self.detector
        cases = self.loader.load(self.gold_path)
        case_results = []
        for case in cases:
            spans = active_detector.detect_text(case.text, unit_id=case.name, part="evaluation")
            case_results.append(self.matcher.evaluate_case(case, spans))
        return self.calculator.calculate(case_results), case_results, cases

    def write_report(
        self,
        report_path: str | Path,
        audit_rows: Sequence[dict[str, Any]] | None = None,
        command: str | None = None,
    ) -> list[MetricResult]:
        metrics, case_results, cases = self.evaluate()
        optional_metrics = self._optional_metrics() if self.include_optional_ner else None
        output = Path(report_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            self.report_writer.render(metrics, case_results, cases, audit_rows or [], command, optional_metrics),
            encoding="utf-8",
        )
        return metrics

    def _optional_metrics(self) -> list[MetricResult] | None:
        try:
            optional_detector = PiiRecognizer(use_optional_ner=True)
            metrics, _case_results, _cases = self.evaluate(optional_detector)
            return metrics
        except Exception:
            return None
