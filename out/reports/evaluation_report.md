# Evaluation Report

## What Changed

Old hardcoded-sample baseline: 15 TP, 0 FP, 0 FN, F1 1.000 on four tiny in-code cases.

That earlier number was not a reliable quality claim because the cases were hardcoded into the evaluator and too small. This report uses a tracked gold-label helper set and strict scoring.

## Gold Dataset

- Cases: 6
- Labeled entities: 22
- Sources: public prospectus excerpts plus synthetic examples for PII types that are absent or rare in the source.
- Public-safe check: tracked labels only contain excerpts from the filed prospectus or synthetic placeholder data.

## Scoring Rule

- TP requires the same entity type and same normalized text.
- Normalization trims punctuation at the edges, collapses whitespace, and compares case-insensitively.
- Cross-type matches are FP for the predicted type and FN for the gold type.
- Same-type partial overlaps are boundary errors; they still count as one FP and one FN in strict metrics.

## Strict Metrics By Entity Type

| Entity Type | TP | FP | FN | Boundary Errors | Precision | Recall | Accuracy | F1 | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| address | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| api_key | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| company | 4 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| credit_card | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| dob | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| email | 2 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| ip_address | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| person | 6 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| phone | 2 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| ssn | 1 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| url | 2 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| overall_micro | 22 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | pass |

## Optional NER Comparison

Not run for this deterministic submission command. Use optional NER explicitly for experimentation.

## Case-Level Errors

### prospectus_contact_block
- False positives: 0
- False negatives: 0
- Boundary errors: 0
- Type mismatches: 0

### lead_manager_contacts
- False positives: 0
- False negatives: 0
- Boundary errors: 0
- Type mismatches: 0

### promoters_and_company
- False positives: 0
- False negatives: 0
- Boundary errors: 0
- Type mismatches: 0

### synthetic_structured_ids
- False positives: 0
- False negatives: 0
- Boundary errors: 0
- Type mismatches: 0

### negative_public_legal_terms
- False positives: 0
- False negatives: 0
- Boundary errors: 0
- Type mismatches: 0

### type_ambiguity_guard
- False positives: 0
- False negatives: 0
- Boundary errors: 0
- Type mismatches: 0

## Redaction Counts From Full DOCX Run

- address: 45
- company: 128
- email: 52
- person: 199
- phone: 36
- url: 52
- total: 512

## Limitations

- The gold helper set is intentionally small, so per-type metrics are more useful than one headline number.
- The full prospectus is not exhaustively human-labeled; full-DOCX counts are audit counts, not ground truth.
- Default execution uses deterministic local rules. Optional NER may improve recall but can also introduce false positives.

## Command

`python redact_pii.py --input /Users/deepanshu/Documents/GitHub/Scalar_Final/input/Red Herring Prospectus.docx --output /Users/deepanshu/Documents/GitHub/Scalar_Final/out/redacted/redacted_prospectus.docx --audit /Users/deepanshu/Documents/GitHub/Scalar_Final/out/audit/redaction_audit.csv --report /Users/deepanshu/Documents/GitHub/Scalar_Final/out/reports/evaluation_report.md --gold /Users/deepanshu/Documents/GitHub/Scalar_Final/evaluation_helper/gold_labels.json --rules /Users/deepanshu/Documents/GitHub/Scalar_Final/config/redaction_rules.json --profile prospectus --no-optional-ner`
