"""
entity_extractor.py
---------------------
Regex-based entity extraction for opportunity messages: emails, phone
numbers, UPI IDs, salary/stipend figures, and explicit payment amounts.

Kept separate from text_analyzer.py so entity extraction (structured data)
is cleanly decoupled from risk-language detection (unstructured signals).
"""

import re
from typing import Dict, List

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Indian-style phone numbers: optional +91, optional spaces/hyphens, 10 digits
PHONE_REGEX = re.compile(r"(?:\+?91[-\s]?)?[6-9]\d{9}\b")

# UPI IDs look like name@bank but bank part is a known-ish short handle set,
# so we exclude anything that already matched as an email domain-like TLD.
UPI_REGEX = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z][a-zA-Z]{2,64}\b")
KNOWN_UPI_HANDLES = {
    "upi", "okhdfcbank", "okicici", "okaxis", "oksbi", "ybl", "paytm",
    "apl", "ibl", "axl", "sbi", "hdfcbank", "icici", "kotak", "airtel",
}

SALARY_REGEX = re.compile(
    r"(?:₹|rs\.?|inr)\s?[\d,]+(?:\s?(?:-|to)\s?(?:₹|rs\.?|inr)?\s?[\d,]+)?"
    r"(?:\s?/?-?\s?(?:per\s?month|pm|per\s?annum|pa|lpa|lakh|k))?",
    re.IGNORECASE,
)

PAYMENT_CONTEXT_REGEX = re.compile(
    r"(?:pay|fee|deposit|charge|amount)\D{0,15}(₹|rs\.?|inr)\s?[\d,]+",
    re.IGNORECASE,
)

COMPANY_NAME_HINT_REGEX = re.compile(
    r"([A-Z][A-Za-z&]*(?:\s[A-Z][A-Za-z&]*){0,3}\s"
    r"(?:Technologies|Pvt\.?\s?Ltd\.?|Solutions|Consultancy|Corp\.?|Inc\.?|Services|Group|Enterprises))"
)


def extract_emails(text: str) -> List[str]:
    return list(dict.fromkeys(EMAIL_REGEX.findall(text or "")))


def extract_phones(text: str) -> List[str]:
    return list(dict.fromkeys(PHONE_REGEX.findall(text or "")))


def extract_upi_ids(text: str, known_emails: List[str]) -> List[str]:
    candidates = UPI_REGEX.findall(text or "")
    upi_ids = []
    for candidate in candidates:
        # Skip anything that is itself, or is a prefix of, a full email address
        # (avoids "user@gmail" being extracted separately from "user@gmail.com")
        if candidate in known_emails:
            continue
        if any(email.startswith(candidate) for email in known_emails):
            continue
        handle = candidate.split("@")[-1].lower()
        if handle in KNOWN_UPI_HANDLES:
            upi_ids.append(candidate)
    return list(dict.fromkeys(upi_ids))


def extract_salary_mentions(text: str) -> List[str]:
    return list(dict.fromkeys(m.strip() for m in SALARY_REGEX.findall(text or "") if m.strip()))


def extract_payment_amounts(text: str) -> List[str]:
    matches = PAYMENT_CONTEXT_REGEX.findall(text or "")
    # findall with groups returns only the group; re-run with finditer for full match
    full_matches = [m.group(0) for m in PAYMENT_CONTEXT_REGEX.finditer(text or "")]
    return list(dict.fromkeys(full_matches))


def extract_company_name_guess(text: str, provided_company: str = "") -> str:
    if provided_company and provided_company.strip():
        return provided_company.strip()
    match = COMPANY_NAME_HINT_REGEX.search(text or "")
    if match:
        return match.group(1).strip()
    return ""


def extract_entities(text: str, provided_company: str = "") -> Dict:
    """Run all extractors and return a single structured dict."""
    emails = extract_emails(text)
    phones = extract_phones(text)
    upi_ids = extract_upi_ids(text, emails)
    salaries = extract_salary_mentions(text)
    payments = extract_payment_amounts(text)
    company = extract_company_name_guess(text, provided_company)

    return {
        "emails": emails,
        "phones": phones,
        "upi_ids": upi_ids,
        "salary_mentions": salaries,
        "payment_amounts": payments,
        "company_name": company,
    }
