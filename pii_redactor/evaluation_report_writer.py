# renders the markdown evaluation report

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

from .evaluation_models import CaseEvaluation, GoldCase
from .models import MetricResult


class EvaluationReportWriter:
    """Render a human-readable evaluation report."""

    OLD_BASELINE_NOTE = "Old hardcoded-sample baseline: 15 TP, 0 FP, 0 FN, F1 1.000 on four tiny in-code cases."

    STRUCTURED_TYPES = {"email", "phone", "ssn", "credit_card", "dob", "ip_address", "url", "api_key", "token"}
    CONTEXT_TYPES = {"person", "company", "address"}

    def render(
        self,
        metrics: Sequence[MetricResult],
        case_results: Sequence[CaseEvaluation],
        cases: Sequence[GoldCase],
        audit_rows: Sequence[dict[str, Any]],
        command: str | None,
        optional_metrics: Sequence[MetricResult] | None = None,
    ) -> str:
        counts = self._counts_by_type(audit_rows)
        lines = [
            "# Evaluation Report",
            "",
            "## What Changed",
            "",
            self.OLD_BASELINE_NOTE,
            "",
            "That earlier number was not a reliable quality claim because the cases were hardcoded into the evaluator and too small. "
            "This report uses a tracked gold-label helper set and strict scoring.",
            "",
            "## Gold Dataset",
            "",
            f"- Cases: {len(cases)}",
            f"- Labeled entities: {sum(len(case.labels) for case in cases)}",
            "- Sources: public prospectus excerpts plus synthetic examples for PII types that are absent or rare in the source.",
            "- Public-safe check: tracked labels only contain excerpts from the filed prospectus or synthetic placeholder data.",
            "",
            "## Scoring Rule",
            "",
            "- TP requires the same entity type and same normalized text.",
            "- Normalization trims punctuation at the edges, collapses whitespace, and compares case-insensitively.",
            "- Cross-type matches are FP for the predicted type and FN for the gold type.",
            "- Same-type partial overlaps are boundary errors; they still count as one FP and one FN in strict metrics.",
            "",
            "## Strict Metrics By Entity Type",
            "",
            "| Entity Type | TP | FP | FN | Boundary Errors | Precision | Recall | Accuracy | F1 | Target |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for metric in metrics:
            lines.append(
                f"| {metric.entity_type} | {metric.tp} | {metric.fp} | {metric.fn} | {metric.boundary_errors} | "
                f"{metric.precision:.3f} | {metric.recall:.3f} | {metric.accuracy:.3f} | {metric.f1:.3f} | {self._target_status(metric)} |"
            )

        if optional_metrics:
            lines.extend(["", "## Optional NER Comparison", "", "| Entity Type | Deterministic F1 | Optional NER F1 |", "| --- | ---: | ---: |"])
            deterministic = {metric.entity_type: metric for metric in metrics}
            for optional in optional_metrics:
                baseline = deterministic.get(optional.entity_type)
                if baseline:
                    lines.append(f"| {optional.entity_type} | {baseline.f1:.3f} | {optional.f1:.3f} |")
        else:
            lines.extend(["", "## Optional NER Comparison", "", "Not run for this deterministic submission command. Use optional NER explicitly for experimentation."])

        lines.extend(["", "## Case-Level Errors", ""])
        for result in case_results:
            lines.append(f"### {result.case_name}")
            lines.append(f"- False positives: {len(result.false_positives)}")
            lines.append(f"- False negatives: {len(result.false_negatives)}")
            lines.append(f"- Boundary errors: {len(result.boundary_errors)}")
            lines.append(f"- Type mismatches: {len(result.type_mismatches)}")
            if result.false_positives:
                lines.append("- FP values: " + ", ".join(sorted({f"{span.entity_type}:{span.text}" for span in result.false_positives})))
            if result.false_negatives:
                lines.append("- FN values: " + ", ".join(sorted({f"{gold.entity_type}:{gold.text}" for gold in result.false_negatives})))
            lines.append("")

        lines.extend(["## Redaction Counts From Full DOCX Run", ""])
        for entity_type in sorted(counts):
            lines.append(f"- {entity_type}: {counts[entity_type]}")
        lines.append(f"- total: {sum(counts.values())}" if counts else "- No full DOCX audit rows were supplied.")

        lines.extend(
            [
                "",
                "## Limitations",
                "",
                "- The gold helper set is intentionally small, so per-type metrics are more useful than one headline number.",
                "- The full prospectus is not exhaustively human-labeled; full-DOCX counts are audit counts, not ground truth.",
                "- Default execution uses deterministic local rules. Optional NER may improve recall but can also introduce false positives.",
            ]
        )
        if command:
            lines.extend(["", "## Command", "", f"`{command}`"])
        return "\n".join(lines) + "\n"

    def _counts_by_type(self, audit_rows: Sequence[dict[str, Any]]) -> dict[str, int]:
        return dict(Counter(row["entity_type"] for row in audit_rows))

    def _target_status(self, metric: MetricResult) -> str:
        if metric.entity_type in self.STRUCTURED_TYPES:
            return "pass" if metric.precision >= 1.0 and metric.recall >= 1.0 else "miss"
        if metric.entity_type in self.CONTEXT_TYPES:
            return "pass" if metric.precision >= 0.8 and metric.recall >= 0.8 else "miss"
        if metric.entity_type == "overall_micro":
            return "pass" if metric.f1 >= 0.9 else "miss"
        return "-"
