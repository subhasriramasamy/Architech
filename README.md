# 🛡️ ScamCheck — AI-Powered Opportunity Verification System

> **"Verify before you trust."**

ScamCheck analyzes internship and job opportunity messages (pasted text or a
screenshot) and produces an explainable 0–100 risk score, a plain-language
breakdown of *why* it flagged the message, and actionable next steps —
built for a hackathon demo, fully functional, no paid APIs required.

---

## 1. Features

- Paste-text or screenshot (OCR) input
- Multi-category suspicious-language detection (payment, urgency,
  guaranteed-job, personal-info, recruitment-process risk)
- Entity extraction: emails, phone numbers, UPI IDs, URLs, salary/stipend,
  payment amounts, company name
- Structural URL risk analysis (HTTP vs HTTPS, IP hosts, suspicious TLDs,
  long/obscured links, misleading domains)
- Offline recruiter/company consistency checks (no paid verification APIs)
- Transparent, weighted 0–100 risk engine with a 4-tier classification
  (LOW / MODERATE / HIGH / CRITICAL)
- Auto-generated, factor-linked recommendations
- SQLite-backed Analysis History with detail drill-down
- Built-in demo examples for live hackathon judging
- Kaggle dataset integration via a Dataset Explorer page for real labeled rows
- Professional Streamlit dashboard with Plotly gauge + factor charts

---

## 2. Project Structure

```text
ScamCheck/
│
├── app.py                        # Main Streamlit app (pages + orchestration)
├── requirements.txt
├── README.md
│
├── modules/
│   ├── text_analyzer.py          # Keyword/category risk-language detector
│   ├── url_analyzer.py           # URL extraction + structural risk scoring
│   ├── entity_extractor.py       # Emails, phones, UPI, salary, company
│   ├── company_verifier.py       # Offline recruiter/company consistency checks
│   ├── risk_engine.py            # Combines all signals into 0-100 score
│   ├── recommendation_engine.py  # Factor -> actionable advice mapping
│   └── ocr_processor.py          # Tesseract OCR wrapper for screenshots
│
├── database/
│   └── database.py               # SQLite persistence (analysis history)
│
├── data/
│   ├── sample_opportunities.csv            # 17 labeled demo messages
│   └── internship_job_scam_dataset.csv     # 900-row Kaggle benchmark dataset
│
├── models/
│   └── README.md                 # Placeholder + upgrade path for a trained ML model
│
└── assets/
    └── README.md                 # Optional logo instructions
```

---

## 3. Setup Instructions

### Step 1 — Clone / unzip the project and enter the folder

```bash
cd ScamCheck
```

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Install the Tesseract OCR engine (system binary)

The Screenshot Analyzer needs the **Tesseract binary** installed on your
machine — `pytesseract` is only a Python wrapper around it.

- **Windows:** Download the installer from
  https://github.com/UB-Mannheim/tesseract/wiki and add it to your PATH.
- **macOS:** `brew install tesseract`
- **Linux (Debian/Ubuntu):** `sudo apt-get install tesseract-ocr`

If Tesseract isn't installed, every other feature (text analysis, URL
analysis, risk scoring, history) still works fully — only the Screenshot
Analyzer page will show a clear setup message instead of crashing.

### Step 5 — Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. The SQLite database
(`scamcheck.db`) is created automatically on first run.

---

## 4. How Each Module Works

| Module | Responsibility |
|---|---|
| `text_analyzer.py` | Normalizes text and regex-matches it against five risk-language categories (payment, urgency, guaranteed-job, personal-info, recruitment-process). Returns *evidence*, not a verdict — the risk engine decides how much each category matters. |
| `url_analyzer.py` | Extracts URLs and scores each one on structural red flags (HTTP-only, IP-address host, excessive subdomains, long URLs, suspicious TLDs/keywords). Explicitly labeled as a *preliminary* assessment. |
| `entity_extractor.py` | Regex-based extraction of emails, Indian-format phone numbers, UPI IDs, salary/stipend mentions, payment amounts, and a best-guess company name. |
| `company_verifier.py` | Offline-only consistency checks: are contact details even provided? Does the recruiter's email domain match the company website? Is a free email provider (Gmail, Yahoo, etc.) being used instead of a company domain? |
| `risk_engine.py` | Combines all of the above into a single weighted 0–100 score using the brief's suggested weights, maps it to a 4-tier risk level, and generates a plain-language summary that names the strongest factor. |
| `recommendation_engine.py` | Maps each *triggered* risk factor to a specific, practical action — never generic filler unless nothing was detected. |
| `ocr_processor.py` | Wraps `pytesseract` to extract text from an uploaded screenshot, with graceful, actionable error handling if Tesseract isn't installed or the image is unreadable. |
| `database/database.py` | SQLite schema + CRUD helpers for the Analysis History page (timestamp, label, score, level, indicators, source, raw text). |

**Why this is explainable, not a black box:** `risk_engine.py` never
outputs a bare number — every point contributing to the score is attached
to a named factor (e.g. "Payment Request: +25") with a human-readable
explanation, and the final summary always names the strongest signal
rather than declaring "this is a scam."

---

## 5. Test Messages

Five ready-to-paste test cases (more are in `data/sample_opportunities.csv`
and in the app's built-in **Demo Examples** dropdown):

**1. Critical Risk — payment + urgency + guaranteed job**
```
Congratulations! You have been SELECTED for our Work From Home Data Entry
Internship. Guaranteed job, no interview required. To confirm your seat,
pay a refundable registration fee of Rs 1999 via UPI to quickhire@ybl
within 24 hours. Limited seats, offer expires today! Contact us at
hr.quickhire@gmail.com or +919876543210 for the payment link:
http://quickhire-jobs.xyz/confirm
```

**2. High Risk — sensitive info request + IP-address URL**
```
URGENT: Immediate joining available for Content Writing job. 100%
placement guaranteed. Earn Rs 80000 per month working just 2 hours a day.
Send your bank account details and Aadhaar number to verify eligibility.
Act immediately, only 3 seats left! Visit http://192.168.10.44/apply-now
to register.
```

**3. Low Risk — legitimate-style posting**
```
We are pleased to offer you a Software Development Internship at Infotech
Solutions Pvt Ltd. The role involves working on our web application team
under the guidance of a senior developer. Duration: 3 months. Stipend: Rs
15000 per month. Please find the detailed job description and
requirements attached. For queries, contact hr@infotechsolutions.com or
visit our careers page at https://www.infotechsolutions.com/careers.
```

**4. Moderate Risk — vague description + unverified free-email contact**
```
Skyline Ventures offers a Graphic Design internship with unrealistic
salary of Rs 60000 per month for freshers. Vague job description, no
clear responsibilities mentioned. Immediate joining required, pay Rs 1500
as a kit fee for design software access. Contact:
skyline.ventures2024@gmail.com
```

**5. High Risk — deposit + no screening**
```
Dear Candidate, you are selected without interview for our HR Executive
position. Pay a small training fee of Rs 2500 to activate your employee
ID. Respond immediately or the offer will be given to someone else.
Contact: nextgen.hr@gmail.com
```

---

## 6. Important Notes

- This is a **risk assessment tool**, not a fraud-detection guarantee.
  ScamCheck never states an opportunity is "definitely a scam" —
  it flags patterns that warrant independent verification.
- No paid APIs are used or required. The prototype runs entirely offline
  except for the Streamlit UI itself.
- No API keys are hardcoded anywhere in the codebase.
- The architecture is intentionally modular (see `models/README.md`) so
  the rule-based `risk_engine.py` can later be augmented with a trained
  ML classifier without rewriting the UI or other modules.

## 7. Roadmap (not implemented in this prototype)

- Trained ML scam classifier / transformer-based NLP
- Live company & domain-reputation verification APIs
- Browser extension / WhatsApp & email integrations
- Tamil + English multilingual scam detection
- Personalized student safety recommendations
