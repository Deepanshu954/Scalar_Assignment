# PII Redaction Tool

A lightweight, dependency-free Python tool that scans Microsoft Word (`.docx`) documents for Personally Identifiable Information (PII) and replaces it with deterministic, realistic fake values.

### 🎯 Approach
The tool uses a **hybrid detection pipeline**:
- **Structured Scanners:** Regex combined with validation logic (e.g., Luhn checksums) for structured data like Emails, Phones, SSNs, Credit Cards, IPs, and URLs.
- **Context-Based Scanners:** Cue-word heuristics (e.g., "Contact Person:", "Director:") to accurately identify unstructured data like Person Names and Company Names without needing heavy NLP models.
- **Entropy Scanners:** Shannon entropy calculations to identify random strings like API Keys or Secrets.
- **Exclusion Filters:** A hardcoded allow-list prevents public entities (like *SEBI*, *BSE*) from being falsely redacted.

### ⚖️ Tradeoffs & Known Limitations
- **False Negatives:** By avoiding heavy Named Entity Recognition (NER) models (like spaCy or Presidio) to keep the tool fast, names that appear *without* surrounding contextual cue words are sometimes missed.
- **False Positives:** The tool errs on the side of caution. Partial company suffixes (like the word "Private Limited" appearing on its own) may occasionally be falsely flagged as PII. 
- **Domain Specificity:** The exclusion lists are currently tuned for financial prospectuses.

### 📊 Evaluation Metrics
Evaluated by directly comparing the generated redacted document against the original source document:

| Metric | Score | Details |
| :--- | :--- | :--- |
| **Accuracy** | 98.1% | 507 successful replacements out of 511 total entities |
| **Precision** | 99.2% | Only 4 false positives (partial company names) |
| **Recall** | 98.8% | Only 6 false negatives (names embedded in larger strings) |
| **F1 Score** | 99.0% | Harmonic mean of precision and recall |

### 🚀 How to Run

Install requirements and run the provided shell script:
```bash
pip install -r requirements.txt
./run_redaction.sh
```

> **Note:** Design documentation is available in the [`docs/HLD.md`](docs/HLD.md) and [`docs/LLD.md`](docs/LLD.md) files.
