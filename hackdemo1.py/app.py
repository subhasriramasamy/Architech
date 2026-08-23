from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent

SIGNALS = [
    {
        "key": "payment",
        "title": "Asks for payment upfront",
        "description": "Legitimate employers do not charge students a registration, training, security, or placement fee to apply.",
        "patterns": [
            r"registration\s*fee", r"security\s*deposit", r"pay\s*(?:a|the)?\s*(?:fee|amount)",
            r"payment\s*(?:of|for|to)", r"refundable\s*(?:fee|deposit)", r"processing\s*fee", r"training\s*fee",
        ],
        "weight": 30,
        "advice": "Never pay to apply. Verify the role through the company’s official careers page.",
    },
    {
        "key": "urgency",
        "title": "Uses pressure or urgency",
        "description": "Scammers create a rushed decision so there is less time to verify the sender or opportunity.",
        "patterns": [
            r"limited\s*(?:slots|seats|vacancies)", r"apply\s*(?:now|today|immediately)", r"within\s*\d+\s*(?:hours?|minutes?)",
            r"last\s*chance", r"urgent", r"act\s*fast", r"offer\s*expires", r"only\s*\d+\s*(?:spots?|seats?)",
        ],
        "weight": 15,
        "advice": "Pause. A real recruiter will allow time for you to verify the role and company.",
    },
    {
        "key": "unrealistic_pay",
        "title": "Promises unusually high pay",
        "description": "Very high daily earnings with no experience or little effort are a common bait pattern.",
        "patterns": [
            r"(?:earn|make|salary|income).{0,30}(?:₹|rs\.?|inr)?\s*\d[\d,]*(?:\s*(?:per|/|a)\s*(?:day|hour|week|month))?",
            r"₹\s*[\d,]+\s*(?:/|per|a)\s*(?:day|hour|week)", r"no\s*experience\s*(?:needed|required)",
            r"work\s*from\s*home.{0,80}(?:₹|rs\.?|inr)",
        ],
        "weight": 20,
        "advice": "Compare the compensation with similar roles on the company’s official job board.",
    },
    {
        "key": "sensitive_data",
        "title": "Requests sensitive information too early",
        "description": "A recruiter should not ask for OTPs, bank credentials, or identity documents before a verified hiring process.",
        "patterns": [
            r"(?:send|share|submit|provide).{0,35}(?:otp|one[- ]time password|pin|cvv|password)",
            r"(?:aadhaar|aadhar|pan\s*card|bank\s*(?:details|account)|upi\s*id)",
            r"(?:verify|activate).{0,30}(?:account|wallet).{0,30}(?:otp|pin)",
        ],
        "weight": 30,
        "advice": "Do not share OTPs, PINs, passwords, or bank details. Stop contact and report the sender.",
    },
    {
        "key": "generic_greeting",
        "title": "Uses a generic candidate greeting",
        "description": "Mass messages often use phrases like ‘Dear Candidate’ instead of identifying you or the role clearly.",
        "patterns": [r"dear\s+(?:candidate|applicant|job\s*seeker)", r"hello\s+(?:candidate|dear)", r"dear\s+sir/?madam"],
        "weight": 7,
        "advice": "Look for a named recruiter, a specific job ID, and a verifiable company contact.",
    },
    {
        "key": "suspicious_link",
        "title": "Contains a suspicious or shortened link",
        "description": "Shortened links and unfamiliar domains can hide a fake login page or a malicious download.",
        "patterns": [r"bit\.ly", r"tinyurl\.com", r"t\.co/", r"is\.gd", r"cutt\.ly", r"\.(?:xyz|top|click|work|buzz)(?:/|\b)"],
        "weight": 18,
        "advice": "Do not open the link. Type the company’s official website into your browser yourself.",
    },
    {
        "key": "poor_writing",
        "title": "Has unusual writing or formatting",
        "description": "Repeated spelling errors, excessive capitals, and many exclamation marks can be warning signs, especially alongside payment requests.",
        "patterns": [r"!!!+", r"\b(?:congradulations|recieve| sucessfully|immediatly|opurtunity|kindly revert)\b", r"[A-Z]{5,}\s+[A-Z]{5,}"],
        "weight": 8,
        "advice": "Treat poor writing as a supporting signal, not proof by itself. Verify independently.",
    },
]


def compact_phrase(text, match):
    start = max(0, match.start() - 42)
    end = min(len(text), match.end() + 58)
    phrase = re.sub(r"\s+", " ", text[start:end]).strip()
    if start > 0:
        phrase = "..." + phrase
    if end < len(text):
        phrase += "..."
    return phrase


def domain_checks(text, supplied_url=""):
    urls = re.findall(r"https?://[^\s<>\"']+", text)
    if supplied_url.strip():
        urls.append(supplied_url.strip())
    domains = []
    for item in urls:
        try:
            host = urlparse(item if "://" in item else "https://" + item).hostname
            if host:
                domains.append(host.lower().removeprefix("www."))
        except ValueError:
            continue
    return sorted(set(domains))


def analyze(text, sender_email="", claimed_company="", supplied_url=""):
    clean = text.strip()
    lowered = clean.lower()
    findings = []
    score = 0
    for signal in SIGNALS:
        matches = []
        for pattern in signal["patterns"]:
            matches.extend(re.finditer(pattern, lowered, re.IGNORECASE | re.DOTALL))
        if matches:
            unique_phrases = []
            for match in matches:
                phrase = compact_phrase(clean, match)
                if phrase not in unique_phrases:
                    unique_phrases.append(phrase)
            findings.append({
                "key": signal["key"],
                "title": signal["title"],
                "description": signal["description"],
                "evidence": unique_phrases[:2],
                "advice": signal["advice"],
                "weight": signal["weight"],
            })
            score += signal["weight"]

    domains = domain_checks(clean, supplied_url)
    sender_domain = sender_email.rsplit("@", 1)[-1].lower().strip() if "@" in sender_email else ""
    company_words = [word for word in re.findall(r"[a-z0-9]+", claimed_company.lower()) if len(word) > 2]
    if sender_domain and company_words and not any(word in sender_domain for word in company_words):
        findings.append({
            "key": "domain_mismatch",
            "title": "Sender domain does not match the claimed company",
            "description": "A free email address or unrelated domain is inconsistent with a formal company recruitment message.",
            "evidence": [f"Sender: {sender_email} | Claimed company: {claimed_company}"],
            "advice": "Find the company’s official contact page and confirm the recruiter’s identity there.",
            "weight": 25,
        })
        score += 25
    elif sender_domain in {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me"} and claimed_company:
        findings.append({
            "key": "free_email",
            "title": "Uses a free email address for company recruiting",
            "description": "Free email providers are not automatically scams, but formal recruiters usually use a company domain.",
            "evidence": [f"Sender: {sender_email}"],
            "advice": "Verify the sender through the company’s official website before replying.",
            "weight": 12,
        })
        score += 12

    score = min(100, score)
    if score >= 55:
        level, label, color = "high", "High risk", "#e05252"
    elif score >= 25:
        level, label, color = "medium", "Medium risk", "#d99b32"
    else:
        level, label, color = "low", "Low risk", "#2f9b72"

    if not clean:
        return {"score": 0, "level": "unknown", "label": "Add an opportunity to analyze", "color": "#73808c", "findings": [], "domains": domains, "summary": "Paste the message, email, or offer details to begin."}

    summary = {
        "high": "Several strong scam indicators are present. Do not pay or share personal information until independently verified.",
        "medium": "Some warning signs are present. Slow down and verify the opportunity through official channels.",
        "low": "Few automated warning signs were found. This is not proof that the opportunity is legitimate, so verify the sender and role anyway.",
    }[level]
    return {"score": score, "level": level, "label": label, "color": color, "findings": findings, "domains": domains, "summary": summary}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok": True})
            return
        target = ROOT / ("index.html" if self.path in {"/", ""} else self.path.lstrip("/"))
        if target.exists() and target.is_file() and target.suffix in {".html", ".css", ".js"}:
            content_type = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8"}[target.suffix]
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(target.read_bytes())
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/api/analyze":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = analyze(payload.get("text", ""), payload.get("sender_email", ""), payload.get("claimed_company", ""), payload.get("url", ""))
            self.send_json(result)
        except (ValueError, json.JSONDecodeError):
            self.send_json({"error": "Invalid request"}, 400)

    def send_json(self, data, status=200):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("ScamCheck running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ScamCheck")
        server.server_close()
