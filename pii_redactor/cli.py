# command line argument parsing and main entry point

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .docx_redaction_service import DocxRedactionService
from .evaluator import RedactionEvaluator
from .models import PipelineMode
from .recognizers import PiiRecognizer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Redact PII from a DOCX file using Tiered Detection.")
    parser.add_argument("--input", required=True, help="Input DOCX path")
    parser.add_argument("--output", required=True, help="Redacted output DOCX path")
    parser.add_argument("--audit", default="out/audit/redaction_audit.csv", help="CSV audit log path")
    parser.add_argument("--report", default="out/reports/evaluation_report.md", help="Evaluation report path")
    parser.add_argument("--gold", default="evaluation_helper/gold_labels.json", help="Gold-label JSON path for evaluation")
    parser.add_argument(
        "--mode",
        choices=["mutation", "validation"],
        default="mutation",
        help="Pipeline execution mode (mutation = rewrite DOCX, validation = scan compliance only)",
    )
    parser.add_argument(
        "--no-optional-ner",
        action="store_true",
        help="Disable optional spaCy NER even if installed",
    )
    parser.add_argument("--rules", default=None, help="Optional redaction rules JSON path")
    parser.add_argument("--profile", default="prospectus", help="Rules profile to load")
    parser.add_argument(
        "--compare-optional-ner",
        action="store_true",
        help="Also evaluate optional NER mode if local dependencies are available",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input DOCX not found: {input_path}")
    if input_path.suffix.lower() != ".docx":
        parser.error("Input must be a .docx file")

    detector = PiiRecognizer(
        use_optional_ner=not args.no_optional_ner,
        rules_path=args.rules,
        profile=args.profile,
    )
    mode = PipelineMode(args.mode)
    service = DocxRedactionService(detector=detector, mode=mode)
    audit_rows = service.redact_docx(input_path, args.output, args.audit, mode=mode)

    command = "python redact_pii.py " + " ".join(argv or sys.argv[1:])
    RedactionEvaluator(
        detector=detector,
        gold_path=args.gold,
        include_optional_ner=args.compare_optional_ner,
    ).write_report(args.report, audit_rows=audit_rows, command=command)

    print(f"Pipeline Mode:    {mode.value}")
    if mode == PipelineMode.MUTATION:
        print(f"Redacted DOCX:    {args.output}")
    print(f"Audit CSV:        {args.audit}")
    print(f"Evaluation report:{args.report}")
    print(f"Entities flagged: {len(audit_rows)}")
    return 0
