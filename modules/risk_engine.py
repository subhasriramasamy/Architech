"""
risk_engine.py
----------------
Combines signals from text_analyzer, url_analyzer, entity_extractor, and
company_verifier into a single explainable 0-100 risk score.

Design goals (per project brief):
  - Transparent: every point on the score is traceable to a named factor.
  - Non-absolute: never claims certainty of fraud.
  - Multi-signal: a single weak keyword hit should not dominate the score.
"""

from typing import Dict, List

# Suggested weights from the project brief.
WEIGHTS = {
    "payment_request": 25,
    "sensitive_info_request": 20,
    "urgency_language": 15,
    "suspicious_url": 15,
    "unverified_contact": 10,
    "unrealistic_compensation": 10,
    "guaranteed_job_language": 10,
    "missing_job_details": 5,
    "suspicious_recruitment_process": 10,
}

RISK_LEVELS = [
    (0, 25, "LOW RISK"),
    (26, 50, "MODERATE RISK"),
    (51, 75, "HIGH RISK"),
    (76, 100, "CRITICAL RISK"),
]


def _risk_level_for_score(score: int) -> str:
    for low, high, label in RISK_LEVELS:
        if low <= score <= high:
            return label
    return "CRITICAL RISK"  # safety fallback for score > 100 edge cases


def _looks_unrealistic(salary_mentions: List[str]) -> bool:
    """Very rough heuristic: flag salary mentions with large numbers (lakh/crore per month)."""
    for mention in salary_mentions:
        lowered = mention.lower()
        if "lakh" in lowered or "crore" in lowered:
            # extract leading number
            digits = "".join(ch for ch in lowered if ch.isdigit())
            if digits and int(digits[:3] or 0) >= 50 and "per month" in lowered.replace(" ", "") .replace("-", ""):
                return True
        if "lakh" in lowered and ("per month" in lowered or "/month" in lowered or "pm" in lowered):
            return True
    return False


def calculate_risk(text_analysis: Dict, url_analysis: Dict, entities: Dict,
                    company_check: Dict) -> Dict:
    """
    Combine all module outputs into a final score + a list of explainable factors.

    Returns:
        {
            "score": int (0-100),
            "risk_level": str,
            "factors": [ {factor, weight, severity, explanation}, ... ],
            "summary": str,
        }
    """
    factors: List[Dict] = []
    raw_total = 0

    # --- Payment request -----------------------------------------------
    if text_analysis.get("payment_risk", {}).get("matched"):
        raw_total += WEIGHTS["payment_request"]
        factors.append({
            "factor": "Payment Request",
            "weight": WEIGHTS["payment_request"],
            "severity": "HIGH",
            "explanation": ("The opportunity requests an upfront payment "
                             "(e.g. registration/processing/training fee) "
                             "before the internship/job begins."),
        })

    # --- Sensitive financial / personal info request ---------------------
    if text_analysis.get("personal_info_risk", {}).get("matched"):
        raw_total += WEIGHTS["sensitive_info_request"]
        factors.append({
            "factor": "Sensitive Information Request",
            "weight": WEIGHTS["sensitive_info_request"],
            "severity": "HIGH",
            "explanation": ("The message asks for sensitive personal or "
                             "financial identifiers such as OTP, passwords, "
                             "bank details, Aadhaar, or PAN."),
        })

    # --- Urgency language -------------------------------------------------
    if text_analysis.get("urgency_risk", {}).get("matched"):
        raw_total += WEIGHTS["urgency_language"]
        factors.append({
            "factor": "Urgency Language",
            "weight": WEIGHTS["urgency_language"],
            "severity": "MODERATE",
            "explanation": ("The message uses pressure tactics ('act now', "
                             "'limited seats', 'offer expires today') to "
                             "discourage careful verification."),
        })

    # --- Suspicious URL -----------------------------------------------------
    if url_analysis.get("highest_risk_level") in ("MODERATE", "HIGH"):
        raw_total += WEIGHTS["suspicious_url"]
        factors.append({
            "factor": "Suspicious URL",
            "weight": WEIGHTS["suspicious_url"],
            "severity": url_analysis.get("highest_risk_level"),
            "explanation": ("One or more links in the message show structural "
                             "warning signs (e.g. HTTP only, IP-address host, "
                             "unusual TLD, or a long/obscured URL)."),
        })

    # --- Unverified recruiter / contact --------------------------------------
    company_flags = company_check.get("flags", [])
    if company_flags:
        raw_total += WEIGHTS["unverified_contact"]
        factors.append({
            "factor": "Unverified Recruiter / Contact",
            "weight": WEIGHTS["unverified_contact"],
            "severity": "MODERATE",
            "explanation": "; ".join(f["explanation"] for f in company_flags),
        })

    # --- Unrealistic compensation --------------------------------------------
    if _looks_unrealistic(entities.get("salary_mentions", [])):
        raw_total += WEIGHTS["unrealistic_compensation"]
        factors.append({
            "factor": "Unrealistic Compensation",
            "weight": WEIGHTS["unrealistic_compensation"],
            "severity": "MODERATE",
            "explanation": ("The stated salary/stipend appears unusually "
                             "high relative to a typical entry-level "
                             "internship or job."),
        })

    # --- Guaranteed job language ------------------------------------------
    if text_analysis.get("guaranteed_job_risk", {}).get("matched"):
        raw_total += WEIGHTS["guaranteed_job_language"]
        factors.append({
            "factor": "Guaranteed Job Language",
            "weight": WEIGHTS["guaranteed_job_language"],
            "severity": "MODERATE",
            "explanation": ("The message promises guaranteed selection or "
                             "placement without describing a normal, "
                             "merit-based hiring process."),
        })

    # --- Missing job details --------------------------------------------------
    if not text_analysis.get("_has_job_details", True):
        raw_total += WEIGHTS["missing_job_details"]
        factors.append({
            "factor": "Missing Job Details",
            "weight": WEIGHTS["missing_job_details"],
            "severity": "LOW",
            "explanation": ("The message does not clearly describe role "
                             "responsibilities, requirements, or duration -- "
                             "a vague posting is harder to verify."),
        })

    # --- Suspicious recruitment process --------------------------------------
    if text_analysis.get("recruitment_process_risk", {}).get("matched"):
        raw_total += WEIGHTS["suspicious_recruitment_process"]
        factors.append({
            "factor": "Suspicious Recruitment Process",
            "weight": WEIGHTS["suspicious_recruitment_process"],
            "severity": "MODERATE",
            "explanation": ("The described hiring process skips normal "
                             "steps such as interviews or screening, or "
                             "describes vague/implausible role details."),
        })

    score = max(0, min(100, raw_total))
    risk_level = _risk_level_for_score(score)

    summary = _build_summary(factors, risk_level)

    return {
        "score": score,
        "risk_level": risk_level,
        "factors": factors,
        "summary": summary,
    }


def _build_summary(factors: List[Dict], risk_level: str) -> str:
    if not factors:
        return ("No significant risk indicators were detected in this "
                "opportunity based on the current rule set. This does not "
                "guarantee legitimacy -- always verify independently.")

    strongest = max(factors, key=lambda f: f["weight"])
    other_factor_names = [f["factor"] for f in factors if f is not strongest]

    parts = [
        "The opportunity contains characteristics that require verification "
        f"({risk_level.lower()})."
    ]
    parts.append(f"The strongest warning sign is: {strongest['factor']}.")
    if other_factor_names:
        parts.append("Additional concerns include: " + ", ".join(other_factor_names) + ".")
    parts.append(
        "This is a risk assessment, not proof of fraud -- please verify the "
        "organization independently before proceeding."
    )
    return " ".join(parts)
