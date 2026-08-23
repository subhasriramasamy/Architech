# ScamCheck

A dependency-free prototype for explainable internship and job opportunity verification. Students paste a message, optionally add the sender email, claimed company, and URL, and receive a 0-100 risk score with the exact evidence behind each warning.

## Run on Windows

1. Open PowerShell in this folder:

```powershell
cd "C:\Users\Jaisre..S\OneDrive\Desktop\Project\hackdemo1.py"
```

2. Start the local server:

```powershell
python app.py
```

3. Open http://127.0.0.1:8000 in a browser.

Stop with `Ctrl+C`.

## Demo flow

Click **Registration fee scam** for an instant high-risk example, or click **Professional offer** to demonstrate a low-risk result. You can also paste any message and include sender metadata to trigger domain checks.

## Included detection signals

- Upfront registration, training, processing, or security fees
- Urgency and pressure language
- Unrealistic pay promises and no-experience claims
- Aadhaar, bank details, OTP, PIN, password, or other sensitive-data requests
- Generic greetings
- Shortened and suspicious top-level domains
- Poor writing and excessive formatting
- Sender email versus claimed company mismatch

This prototype is heuristic and educational. It does not prove that an opportunity is safe or fraudulent, and it does not call an external LLM, OCR service, WHOIS service, or company database.
