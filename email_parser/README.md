# PHISHGUARD-X Email Parser & Forensic Analysis Module

## Overview

This module is responsible for parsing `.eml` email files and extracting structured forensic intelligence for the PHISHGUARD-X platform.

The module converts raw emails into structured JSON that can be used by:

- Person 2: NLP / DistilBERT phishing classification
- Person 3: URL and XGBoost analysis
- Person 4: Neo4j threat graph
- Person 6: Backend and system integration

---

# Features

## 1. Email Parsing

The parser reads `.eml` files and extracts:

- From
- To
- Subject
- Date
- Reply-To
- Return-Path
- Message-ID

---

## 2. Email Body Extraction

The module extracts:

- Plain text body
- HTML body
- Clean text extracted from HTML

This provides clean email content for NLP analysis.

---

## 3. NLP-Ready Text

The parser generates:

```text
Subject: Email Subject

Email Body Content
```

This field can be directly used by the DistilBERT model.

Output field:

```text
nlp_text
```

---

## 4. URL Extraction

The module extracts:

- URLs from plain text
- URLs from HTML
- HTML `href` links
- Visible text and destination link mismatches

Example:

```text
Visible Link:
https://paypal.com

Actual Link:
https://paypal-login-attacker.com
```

This information can be used for phishing detection and URL-based machine learning.

---

## 5. Attachment Analysis

The module extracts:

- Filename
- MIME type
- File size
- File extension
- MD5 hash
- SHA-256 hash

It also flags suspicious attachment extensions such as:

```text
.exe
.bat
.cmd
.ps1
.js
.vbs
.scr
```

---

## 6. Email Authentication Analysis

The module extracts authentication results from:

- SPF
- DKIM
- DMARC

Example:

```json
{
    "spf": "fail",
    "dkim": "fail",
    "dmarc": "fail"
}
```

The module supports multiple `Authentication-Results` headers.

---

## 7. IP Extraction

IPv4 addresses are extracted from `Received` headers.

Example:

```text
185.22.44.100
```

These IPs can be used for infrastructure analysis and threat graph creation.

---

## 8. Email Relay Path Analysis

The parser extracts the email delivery path from `Received` headers.

Example:

```text
Suspicious Server
        ↓
Mail Relay
        ↓
Recipient Server
```

Output includes:

- Hop number
- Sending server
- Receiving server
- IP addresses
- Timestamp
- Raw `Received` header

---

## 9. Sender and Domain Analysis

The module analyzes:

- From domain
- Reply-To domain
- Return-Path domain
- Message-ID domain

It also identifies domain mismatches such as:

- From vs Reply-To
- From vs Return-Path
- From vs Message-ID

These mismatches are treated as forensic signals, not automatic proof of phishing.

---

# Installation

## Requirements

- Python 3.10 or higher
- beautifulsoup4

Install dependencies:

```bash
python -m pip install beautifulsoup4
```

---

# Project Structure

```text
email_parser/
│
├── parser.py
├── headers.py
├── body_extractor.py
├── url_extractor.py
├── attachment_analyzer.py
├── forensic_analyzer.py
│
├── samples/
│   ├── test_email.eml
│   ├── html_phishing_email.eml
│   └── attachment_email.eml
│
├── output/
│
└── README.md
```

---

# Usage

Activate the virtual environment:

### Windows PowerShell

```powershell
venv\Scripts\Activate.ps1
```

Run the parser:

```powershell
python parser.py samples/test_email.eml
```

Example:

```powershell
python parser.py samples/html_phishing_email.eml
```

Attachment analysis example:

```powershell
python parser.py samples/attachment_email.eml
```

---

# Output

The parser generates a JSON file inside the `output` folder.

Example:

```text
output/html_phishing_email_analysis.json
```

The output contains:

```json
{
    "email_id": "...",
    "headers": {},
    "body": {},
    "nlp_text": "...",
    "urls": [],
    "html_links": [],
    "attachments": [],
    "authentication": {},
    "ip_addresses": [],
    "relay_path": [],
    "reply_to_analysis": {},
    "sender_domain_analysis": {}
}
```

---

# Integration Contract

## Main Function

Other modules can import:

```python
from parser import analyze_email
```

Usage:

```python
result = analyze_email(
    "samples/test_email.eml"
)
```

The function returns a Python dictionary containing the complete forensic analysis.

---

# Integration With Person 2 — NLP / DistilBERT

Use:

```python
result["nlp_text"]
```

Example:

```python
nlp_input = result["nlp_text"]
```

This contains the subject and cleaned email body.

---

# Integration With Person 3 — URL / XGBoost

Use:

```python
result["urls"]
```

And:

```python
result["html_links"]
```

Person 3 can extract structured URL features from these fields.

Useful forensic signals may also include:

```python
result["authentication"]
result["sender_domain_analysis"]
result["reply_to_analysis"]
```

---

# Integration With Person 4 — Neo4j Threat Graph

Useful fields include:

```python
result["email_id"]

result["sender_domain_analysis"]

result["urls"]

result["ip_addresses"]

result["relay_path"]
```

Suggested graph:

```text
EMAIL
  │
  ├── SENT_FROM → DOMAIN
  │
  ├── CONTAINS → URL
  │
  └── RELAYED_THROUGH → IP
```

---

# Integration With Person 6 — Backend

The backend should call:

```python
result = analyze_email(
    uploaded_email_path
)
```

The returned dictionary can then be sent to:

- NLP model
- XGBoost model
- Threat graph
- Risk score fusion engine

---

# Example Integration Flow

```text
                     .eml EMAIL
                         │
                         ▼
                  EMAIL PARSER
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    DistilBERT         XGBoost          Neo4j
    Person 2          Person 3         Person 4
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                   BACKEND FUSION
                      Person 6
                         │
                         ▼
                    RISK SCORE
                         │
                         ▼
                  FORENSIC REPORT
```

---

# Current Status

| Feature | Status |
|---|---|
| `.eml` Parsing | ✅ |
| Header Extraction | ✅ |
| Plain Text Extraction | ✅ |
| HTML Extraction | ✅ |
| HTML Cleaning | ✅ |
| NLP Text Generation | ✅ |
| URL Extraction | ✅ |
| HTML Link Extraction | ✅ |
| Attachment Analysis | ✅ |
| MD5 Hashing | ✅ |
| SHA-256 Hashing | ✅ |
| Suspicious Attachment Detection | ✅ |
| SPF Analysis | ✅ |
| DKIM Analysis | ✅ |
| DMARC Analysis | ✅ |
| IP Extraction | ✅ |
| Relay Path Analysis | ✅ |
| Sender Domain Analysis | ✅ |
| Domain Mismatch Detection | ✅ |
| JSON Output | ✅ |

---

# PHISHGUARD-X

**AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform**

## Email Parser & Forensic Analysis Module

This module provides the foundational email parsing and forensic intelligence layer for PHISHGUARD-X.