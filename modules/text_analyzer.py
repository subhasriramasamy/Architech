"""
text_analyzer.py
-----------------
Rule-based (but genuinely dynamic) text analysis engine for ScamCheck.

This module normalizes opportunity text and scans it for known categories of
scam-related language. It does NOT declare something a scam from a single
keyword hit -- it returns *evidence* (which category, which phrase, where it
matched) and lets risk_engine.py decide how to weigh it, so multiple weak
signals combine into a stronger overall picture.

Kept dependency-light on purpose (pure regex + string ops) so the hackathon
demo never breaks because of a missing NLTK corpus download. spaCy/NLTK can
be dropped in later (see bottom of file) without changing the public API.
"""

import re
from typing import Dict, List

# ---------------------------------------------------------------------------
# Keyword banks. Each entry is a regex fragment (word-boundary safe) so we
# catch simple variations (plurals, punctuation) without heavy NLP.
# ---------------------------------------------------------------------------

PAYMENT_RISK_PHRASES = [
    r"registration\s*fee", r"application\s*fee", r"processing\s*fee",
    r"security\s*deposit", r"training\s*fee", r"pay\s*to\s*confirm",
    r"pay\s*before\s*joining", r"send\s*payment", r"upi\s*payment",
    r"refundable\s*deposit", r"joining\s*fee", r"kit\s*fee",
    r"pay\s*(rs|inr|₹)\s*\d+", r"transfer\s*(the\s*)?amount",
]

URGENCY_RISK_PHRASES = [
    r"act\s*immediately", r"limited\s*seats?", r"offer\s*expires?\s*today",
    r"last\s*chance", r"immediate\s*joining", r"pay\s*today",
    r"respond\s*immediately", r"hurry\s*up", r"only\s*\d+\s*seats?\s*left",
    r"within\s*\d+\s*hours?", r"today\s*only",
]

GUARANTEED_JOB_PHRASES = [
    r"guaranteed\s*job", r"guaranteed\s*placement", r"100%\s*placement",
    r"job\s*without\s*interview", r"selected\s*without\s*interview",
    r"guaranteed\s*internship", r"no\s*interview\s*required",
    r"guaranteed\s*offer\s*letter", r"assured\s*selection",
]

PERSONAL_INFO_RISK_PHRASES = [
    r"bank\s*account\s*(number|details)", r"\botp\b", r"\bpassword\b",
    r"atm\s*(pin|card)", r"debit\s*card\s*(number|pin)",
    r"credit\s*card\s*(number|pin)", r"\baadhaar\b", r"\bpan\s*card\b",
    r"\bpan\s*number\b", r"share\s*your\s*pin",
]

RECRUITMENT_PROCESS_RISK_PHRASES = [
    r"no\s*interview", r"selection\s*without\s*screening",
    r"immediate\s*selection", r"unrealistic\s*salary",
    r"extremely\s*high\s*stipend", r"vague\s*job\s*description",
    r"work\s*from\s*home.{0,20}earn.{0,20}(lakh|crore)",
    r"no\s*experience.{0,20}high\s*salary",
]

CATEGORY_DEFINITIONS = {
    "payment_risk": {
        "label": "Payment Risk",
        "patterns": PAYMENT_RISK_PHRASES,
        "description": "The message asks for money before any legitimate "
                        "employment relationship has been established.",
    },
    "urgency_risk": {
        "label": "Urgency Risk",
        "patterns": URGENCY_RISK_PHRASES,
        "description": "The message pressures the reader to act fast, "
                        "which is a common tactic to prevent careful verification.",
    },
    "guaranteed_job_risk": {
        "label": "Guaranteed Job Risk",
        "patterns": GUARANTEED_JOB_PHRASES,
        "description": "The message promises a job/internship without a "
                        "normal, merit-based selection process.",
    },
    "personal_info_risk": {
        "label": "Personal Information Risk",
        "patterns": PERSONAL_INFO_RISK_PHRASES,
        "description": "The message asks for sensitive personal or "
                        "financial identifiers that a legitimate recruiter "
                        "would never request over chat/email.",
    },
    "recruitment_process_risk": {
        "label": "Recruitment Process Risk",
        "patterns": RECRUITMENT_PROCESS_RISK_PHRASES,
        "description": "The described hiring process skips normal steps "
                        "(screening, interviews) or offers implausible pay.",
    },
}


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, and strip control characters."""
    if not text:
        return ""
    text = text.replace("\u200b", " ")  # zero-width space sometimes used to evade filters
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def _find_matches(normalized_text: str, patterns: List[str]) -> List[str]:
    hits = []
    for pattern in patterns:
        for match in re.finditer(pattern, normalized_text, flags=re.IGNORECASE):
            snippet_start = max(0, match.start() - 25)
            snippet_end = min(len(normalized_text), match.end() + 25)
            snippet = normalized_text[snippet_start:snippet_end].strip()
            hits.append(snippet)
    return hits


def analyze_text(raw_text: str) -> Dict:
    """
    Run every category detector over the supplied text.

    Returns a dict keyed by category id with:
        - label
        - description
        - matched (bool)
        - matches (list of short text snippets that triggered it)
        - match_count (int)
    """
    normalized = normalize_text(raw_text)
    results = {}

    for category_id, definition in CATEGORY_DEFINITIONS.items():
        matches = _find_matches(normalized, definition["patterns"])
        results[category_id] = {
            "label": definition["label"],
            "description": definition["description"],
            "matched": len(matches) > 0,
            "matches": matches[:5],  # cap for display purposes
            "match_count": len(matches),
        }

    results["_word_count"] = len(normalized.split())
    results["_has_job_details"] = _has_minimum_job_details(normalized)
    return results


def _has_minimum_job_details(normalized_text: str) -> bool:
    """
    Heuristic check for whether the opportunity actually describes a role.
    A legitimate posting usually mentions a role/title/responsibility word.
    Missing all of these is itself a (mild) risk signal -- "Missing job details".
    """
    role_indicators = [
        "responsibilit", "role", "position", "intern", "job description",
        "requirements", "qualification", "skills", "duration", "eligib",
    ]
    return any(word in normalized_text for word in role_indicators)


# ---------------------------------------------------------------------------
# Future-ready hook (not used in the prototype): swap in spaCy/NLTK-based
# tokenization + NER here without changing analyze_text()'s return shape.
# ---------------------------------------------------------------------------
def analyze_text_advanced(raw_text: str) -> Dict:  # pragma: no cover
    """Placeholder for a future transformer/NLP-based analyzer."""
    return analyze_text(raw_text)
