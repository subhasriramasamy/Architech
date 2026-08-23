"""
url_analyzer.py
-----------------
Lightweight, dependency-free URL risk heuristics.

IMPORTANT: This performs a *preliminary* structural risk assessment only.
It never claims a URL is proven malicious -- it flags structural patterns
that are statistically more common in phishing / scam links.
"""

import re
from typing import Dict, List
from urllib.parse import urlparse

URL_REGEX = re.compile(
    r"(?:(?:https?://)|(?:www\.))[^\s,)\]<>\"']+", re.IGNORECASE
)

SUSPICIOUS_TLDS = {
    "xyz", "top", "click", "work", "loan", "gq", "tk", "ml", "ga", "cf",
    "info", "live", "icu", "buzz", "rest", "bid",
}

SUSPICIOUS_KEYWORDS = [
    "verify", "secure-login", "confirm-account", "update-payment",
    "job-offer", "hr-portal", "career-verify", "bonus", "reward",
    "free-money", "claim-now",
]

IP_ADDRESS_REGEX = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def extract_urls(text: str) -> List[str]:
    """Find all URL-like substrings in the raw text."""
    if not text:
        return []
    found = URL_REGEX.findall(text)
    # Normalize: add scheme if missing, strip trailing punctuation
    cleaned = []
    for url in found:
        url = url.rstrip(".,;:!?)")
        if not url.lower().startswith("http"):
            url = "http://" + url
        cleaned.append(url)
    return list(dict.fromkeys(cleaned))  # de-duplicate, preserve order


def _analyze_single_url(url: str) -> Dict:
    reasons = []
    score = 0  # 0-100 internal sub-score for this single URL

    try:
        parsed = urlparse(url)
    except Exception:
        return {
            "url": url,
            "risk_level": "MODERATE",
            "reasons": ["URL could not be parsed reliably."],
            "score": 40,
        }

    scheme = parsed.scheme
    hostname = parsed.hostname or ""
    full_length = len(url)

    # 1. HTTP vs HTTPS
    if scheme == "http":
        reasons.append("Uses unencrypted HTTP instead of HTTPS.")
        score += 15

    # 2. IP address instead of domain
    if IP_ADDRESS_REGEX.match(hostname):
        reasons.append("Uses a raw IP address instead of a domain name.")
        score += 30

    # 3. Very long URL
    if full_length > 75:
        reasons.append("Unusually long URL, often used to obscure the real destination.")
        score += 15

    # 4. Excessive subdomains
    if hostname:
        subdomain_count = hostname.count(".")
        if subdomain_count >= 3:
            reasons.append("Contains an unusually high number of subdomains.")
            score += 15

    # 5. Suspicious TLD
    tld = hostname.split(".")[-1] if "." in hostname else ""
    if tld.lower() in SUSPICIOUS_TLDS:
        reasons.append(f"Uses a top-level domain ('.{tld}') frequently associated with low-cost, disposable websites.")
        score += 15

    # 6. Suspicious keywords in the URL itself
    lowered = url.lower()
    for kw in SUSPICIOUS_KEYWORDS:
        if kw in lowered:
            reasons.append(f"URL contains the suspicious keyword pattern '{kw}'.")
            score += 10
            break

    # 7. Misleading brand-in-subdomain pattern, e.g. "paypal.security-update.xyz"
    if hostname.count("-") >= 2:
        reasons.append("Domain contains multiple hyphens, a pattern common in look-alike domains.")
        score += 10

    score = min(score, 100)

    if score == 0:
        risk_level = "LOW"
        reasons.append("No structural red flags detected in this URL.")
    elif score <= 30:
        risk_level = "LOW"
    elif score <= 60:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    return {
        "url": url,
        "risk_level": risk_level,
        "reasons": reasons,
        "score": score,
    }


def analyze_urls(text: str) -> Dict:
    """
    Extract and analyze all URLs in the given text.

    Returns:
        {
            "urls_found": [...],
            "analyses": [ per-url dict ... ],
            "highest_risk_level": "LOW"/"MODERATE"/"HIGH"/"NONE",
            "any_high_risk": bool,
        }
    """
    urls = extract_urls(text)
    analyses = [_analyze_single_url(u) for u in urls]

    if not analyses:
        highest = "NONE"
    else:
        order = {"LOW": 0, "MODERATE": 1, "HIGH": 2}
        highest = max(analyses, key=lambda a: order[a["risk_level"]])["risk_level"]

    return {
        "urls_found": urls,
        "analyses": analyses,
        "highest_risk_level": highest,
        "any_high_risk": any(a["risk_level"] == "HIGH" for a in analyses),
        "disclaimer": (
            "This is a preliminary structural risk assessment only. It does "
            "not prove a website is malicious -- always verify independently."
        ),
    }
