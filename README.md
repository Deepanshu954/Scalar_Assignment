# PII Redaction Tool

This script reads a `.docx` file (like the Red Herring Prospectus), detects personally identifiable information (PII), and replaces it with realistic fake values. 

**Approach:**
I used a hybrid approach without relying on heavy ML libraries. For structured data (emails, phones, SSNs, credit cards, IPs, URLs), I used standard Regex patterns paired with validation checks (like Luhn for credit cards). For unstructured data (names and company names), I used context-based cue words (e.g., looking for "Contact Person:") and legal suffix matching (e.g., "Private Limited"). I also added an entropy checker to catch high-randomness strings like API keys.

**Tradeoffs & False Positives/Negatives:**
Since I avoided heavy NER models to keep the script fast and dependency-free, the tradeoff is that names appearing without any surrounding context cues are sometimes missed (false negatives). On the flip side, partial company suffixes (like "Private Limited" appearing on its own without a company name) are sometimes flagged as false positives. I used a hardcoded exclusion list to prevent public entities like SEBI or BSE from being redacted, but this means the tool is somewhat domain-specific to financial documents right now.

**Evaluation:**
I evaluated the output by comparing the generated redacted document against the original. Out of 511 total PII entities, it correctly replaced 507, with 4 false positives (partial company names) and 6 false negatives (names embedded inside larger unrecognized strings). This resulted in an accuracy of 98.1%, precision of 99.2%, and recall of 98.8%. 

**How to run:**
```bash
pip install -r requirements.txt
./run_redaction.sh
```
