# PII Redaction Tool

A Python script that reads a Red Herring Prospectus (`.docx` format), finds all the personally identifiable information in it, and replaces each piece with a realistic-looking fake value. The output is a clean redacted DOCX along with an audit log and evaluation report.

I built this using a combination of regex patterns and context-based rules -- no heavy ML models needed, though there's an optional spaCy mode if you want to try it.

---

## How to Run

```bash
pip install -r requirements.txt
./run_redaction.sh
```

Or run it directly:

```bash
python3 redact_pii.py \
  --input "input/Red Herring Prospectus.docx" \
  --output out/redacted/redacted_prospectus.docx \
  --audit out/audit/redaction_audit.csv \
  --report out/reports/evaluation_report.md \
  --gold evaluation_helper/gold_labels.json \
  --rules config/redaction_rules.json \
  --profile prospectus \
  --no-optional-ner
```

---

## What PII it Detects

The tool handles the following types:

| PII Type | How it's Detected | Example |
|---|---|---|
| Full names | Cue words like "Contact Person:", "Director:" | `Sarthak Malvadkar` → `Aarav Menon` |
| Email addresses | Standard email regex | `cs@example.com` → `user1234@example.com` |
| Phone numbers | +91 country code patterns | `+91 20 4505 3237` → `+91 77298 17033` |
| Company names | Legal suffixes (Ltd, Pvt, LLP) | `XYZ Pvt Ltd` → `Acme Industries Ltd` |
| Physical addresses | Pincode + location keywords | `Village Birdewadi, Pune 410501` → `Sector 62, Noida 201309` |
| SSNs | xxx-xx-xxxx format | `123-45-6789` → `219-48-3710` |
| Credit card numbers | Regex + Luhn checksum | `4111 1111 1111 1111` → `5555 5555 5555 4444` |
| Dates of birth | DOB/born on context + date | `03/09/1992` → `January 14, 1991` |
| IP addresses | Standard IPv4 regex | `192.168.1.10` → `10.24.18.7` |
| URLs | http/www patterns | `www.example.com` → `[REDACTED_URL]` |
| API keys/secrets | Shannon entropy threshold | `sk_live_94f8...` → `[REDACTED_API_KEY]` |

---

## Approach

I went with a **hybrid approach** that combines three detection methods:

### Regex + Checksum (for structured PII)
Emails, phone numbers, SSNs, credit cards, IPs, DOBs, and URLs all follow predictable formats. I wrote regex patterns for each of these. Credit cards also go through a Luhn checksum to avoid flagging random number sequences.

### Context-based Rules (for names and companies)
People's names don't follow a fixed pattern, so I look for context clues instead. If the text says "Contact Person:" followed by a capitalized name, that's probably a person. Similarly, anything ending in "Private Limited" or "LLP" is treated as a company name.

For promoter names specifically, the prospectus has an "OUR PROMOTERS:" section with names in all caps, so I handle that separately.

### Entropy-based Detection (for secrets/tokens)
API keys and tokens have high randomness (Shannon entropy). I flag any long alphanumeric string with entropy above 3.7 that also matches common secret prefixes like `sk_`, `api_key=`, etc.

### Exclusion List
This is probably the most important part for precision. Public organizations (SEBI, NSE, BSE, RBI), legal terms ("Companies Act"), and offer-related phrases would otherwise get flagged as company names or PII. I maintain an allow-list that prevents these from being redacted.

### Consistent Replacements
Every unique original value maps to one fixed fake value (using a SHA-256 based index). So if "Sarthak Malvadkar" appears 15 times in the document, it gets the same fake name everywhere.

---

## Tradeoffs and Known Issues

**What works well:**
- Structured PII (emails, phones, SSNs, etc.) is caught very reliably — basically 100% on those.
- The exclusion list does a good job keeping public institutions from being falsely redacted.

**What doesn't work perfectly:**
- Names that appear without any context cue (no "Director:" or "Contact Person:" prefix) will be missed. I'd need a proper NER model (like spaCy) to catch those, but that adds a dependency.
- Some company fragments like "Private Limited" by itself (without the company name) get picked up as false positives. It's a minor issue but it's there.
- Addresses in non-standard formats can slip through if they don't have a recognizable pincode or location keyword.

**False positive rate:** Around 0.8% — mostly from partial company suffix matches.
**False negative rate:** Around 1.2% — mostly names in unusual contexts.

---

## Evaluation

I evaluated the tool by comparing the original prospectus against the redacted output. The main check was: did the original PII actually get removed and replaced?

See [evaluation_report.md](out/reports/evaluation_report.md) for detailed numbers. Quick summary:

| Metric | Value |
|---|---|
| Precision | 0.992 |
| Recall | 0.988 |
| F1 Score | 0.990 |
| Accuracy | 0.981 |
| Total entities redacted | 511 |
| Unique values replaced | 223 |

### Per-type Results

| PII Type | Count | Precision |
|---|---|---|
| Person names | 199 | 1.000 |
| Company names | 127 | 0.969 |
| Email addresses | 52 | 1.000 |
| URLs | 52 | 1.000 |
| Physical addresses | 45 | 1.000 |
| Phone numbers | 36 | 1.000 |

All 26 unique email addresses were successfully replaced. No original emails survived in the output.

---

## Project Structure

```
pii_redactor/
  cli.py                     # command line parsing
  detection_pipeline.py      # chains the three detectors together
  structured_recognizers.py  # regex for emails, phones, SSNs, etc
  context_recognizers.py     # name/company detection via context clues
  entropy_recognizer.py      # API key / token detection
  exclusion_filter.py        # allow-list for public terms
  conflict_resolver.py       # handles overlapping detections
  span_propagator.py         # if we find "John Doe" once, find it everywhere
  replacement_generator.py   # consistent fake value mapping
  docx_redaction_service.py  # main DOCX processing service
  run_replacer.py            # text replacement in DOCX runs
  evaluator.py               # evaluation pipeline
config/
  redaction_rules.json       # domain rules and exclusion lists
evaluation_helper/
  gold_labels.json           # hand-labeled test cases
tests/                       # unit tests
```

## Tests

```bash
python3 -m unittest discover -s tests
```

---

## Deliverables

| # | What | Where |
|---|---|---|
| 1 | Source code | This repo (`pii_redactor/` + `redact_pii.py`) |
| 2 | Redacted DOCX | `out/redacted/redacted_prospectus.docx` (generated locally) |
| 3 | This README | Approach, tradeoffs, false positives/negatives |
| 4 | Evaluation report | `out/reports/evaluation_report.md` |
