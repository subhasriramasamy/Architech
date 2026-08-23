"""
company_verifier.py
---------------------
Lightweight, offline heuristic checks on recruiter/company information.

This deliberately does NOT call any external "company verification API" --
the brief requires the prototype to work without paid APIs. Instead it
checks for internal consistency red flags that are cheap, free, and
explainable:

  - Was any company name / website / recruiter contact given at all?
  - Does the recruiter's email domain match the company website's domain?
  - Is the recruiter using a free/personal email provider (gmail, yahoo,
    etc.) instead of a company domain?

Swap in a real registry / domain-age / WHOIS API later behind the same
`verify_company()` function signature.
"""

from typing import Dict, List
from urllib.parse import urlparse

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com",
    "protonmail.com", "icloud.com", "aol.com", "live.com",
}


def _domain_from_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@")[-1].lower().strip()


def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    if not url.lower().startswith("http"):
        url = "http://" + url
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""


def verify_company(company_name: str = "", company_website: str = "",
                    recruiter_email: str = "", recruiter_phone: str = "") -> Dict:
    """
    Run offline consistency checks and return findings.

    Returns:
        {
            "provided_fields": {...bool flags...},
            "flags": [ {issue, severity, explanation}, ... ],
            "verification_completeness": 0-100,
        }
    """
    flags: List[Dict] = []

    provided_fields = {
        "company_name": bool(company_name and company_name.strip()),
        "company_website": bool(company_website and company_website.strip()),
        "recruiter_email": bool(recruiter_email and recruiter_email.strip()),
        "recruiter_phone": bool(recruiter_phone and recruiter_phone.strip()),
    }

    fields_given = sum(provided_fields.values())
    verification_completeness = int((fields_given / 4) * 100)

    if fields_given == 0:
        flags.append({
            "issue": "No recruiter or company contact information provided",
            "severity": "MODERATE",
            "explanation": "Without a company name, website, or recruiter "
                            "contact, this opportunity cannot be cross-checked "
                            "against any official source.",
        })

    email_domain = _domain_from_email(recruiter_email)
    website_domain = _domain_from_url(company_website)

    if email_domain and email_domain in FREE_EMAIL_DOMAINS:
        flags.append({
            "issue": "Recruiter is using a free/personal email provider",
            "severity": "MODERATE",
            "explanation": f"The recruiter contact uses '{email_domain}' "
                            "rather than a company-owned email domain. "
                            "Legitimate HR teams typically use official "
                            "company email addresses.",
        })

    if email_domain and website_domain and email_domain not in FREE_EMAIL_DOMAINS:
        if email_domain != website_domain:
            flags.append({
                "issue": "Recruiter email domain does not match company website",
                "severity": "HIGH",
                "explanation": f"The recruiter's email domain ('{email_domain}') "
                                f"does not match the stated company website "
                                f"domain ('{website_domain}'). This mismatch is "
                                "a common indicator of impersonation.",
            })

    return {
        "provided_fields": provided_fields,
        "flags": flags,
        "verification_completeness": verification_completeness,
    }
