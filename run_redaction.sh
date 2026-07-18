#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif [[ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]]; then
    PYTHON_BIN="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  else
    PYTHON_BIN="python3"
  fi
fi

INPUT_DOCX="${1:-$ROOT_DIR/input/Red Herring Prospectus.docx}"
OUTPUT_DOCX="${2:-$ROOT_DIR/out/redacted/redacted_prospectus.docx}"
AUDIT_CSV="${AUDIT_CSV:-$ROOT_DIR/out/audit/redaction_audit.csv}"
REPORT_MD="${REPORT_MD:-$ROOT_DIR/out/reports/evaluation_report.md}"
GOLD_JSON="${GOLD_JSON:-$ROOT_DIR/evaluation_helper/gold_labels.json}"

mkdir -p "$ROOT_DIR/out/redacted" "$ROOT_DIR/out/audit" "$ROOT_DIR/out/reports"

NER_ARGS=(--no-optional-ner)
if [[ "${USE_OPTIONAL_NER:-0}" == "1" ]]; then
  NER_ARGS=()
fi

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import docx
PY
then
  echo "Missing Python dependencies for: $PYTHON_BIN" >&2
  echo "Install them with: $PYTHON_BIN -m pip install -r requirements.txt" >&2
  exit 1
fi

"$PYTHON_BIN" "$ROOT_DIR/redact_pii.py" \
  --input "$INPUT_DOCX" \
  --output "$OUTPUT_DOCX" \
  --audit "$AUDIT_CSV" \
  --report "$REPORT_MD" \
  --gold "$GOLD_JSON" \
  --rules "$ROOT_DIR/config/redaction_rules.json" \
  --profile "${RULE_PROFILE:-prospectus}" \
  "${NER_ARGS[@]}"

echo
echo "Done."
echo "Redacted DOCX: $OUTPUT_DOCX"
echo "Audit CSV:      $AUDIT_CSV"
echo "Report:         $REPORT_MD"
