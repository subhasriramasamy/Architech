"""
recommendation_engine.py
--------------------------
Generates practical, student-friendly recommendations based on the
detected risk factors. Purely rule-based mapping from factor -> advice,
so recommendations always trace back to something actually found in the
submitted opportunity (no generic filler unless nothing was detected).
"""

from typing import Dict, List

RECOMMENDATION_MAP = {
    "Payment Request": (
        "Do not make any upfront payment until the organization is "
        "independently verified through its official website or a trusted "
        "placement cell. Legitimate employers do not charge candidates to "
        "be hired."
    ),
    "Sensitive Information Request": (
        "Do not share OTPs, passwords, banking credentials, Aadhaar, PAN, "
        "or other sensitive identity information over chat, email, or a "
        "form linked from an unsolicited message."
    ),
    "Urgency Language": (
        "Slow down. Legitimate opportunities rarely require you to decide "
        "or pay within hours. Take time to verify before responding."
    ),
    "Suspicious URL": (
        "Do not click the provided link. Instead, search for the "
        "organization's official website manually and navigate to their "
        "careers/internship page directly."
    ),
    "Unverified Recruiter / Contact": (
        "Search for the organization's official website and verify the "
        "internship through its official careers page or LinkedIn company "
        "page. Cross-check the recruiter's name and email against the "
        "company's official domain."
    ),
    "Unrealistic Compensation": (
        "Compare the stated salary/stipend against typical rates for this "
        "role and experience level. Compensation that is far above market "
        "rate for minimal effort is a common lure."
    ),
    "Guaranteed Job Language": (
        "Be cautious of any offer that skips interviews or guarantees "
        "selection. Ask for a clear description of the selection process."
    ),
    "Missing Job Details": (
        "Ask the recruiter for a detailed job description, responsibilities, "
        "and duration in writing. Vague postings are harder to verify and "
        "easier to misuse."
    ),
    "Suspicious Recruitment Process": (
        "Request a formal offer letter on company letterhead and confirm "
        "the role directly with the organization through an independently "
        "sourced contact (not the one provided in the message)."
    ),
}

GENERAL_SAFETY_TIP = (
    "As a general rule: never pay to get a job, never share OTPs or "
    "passwords, and always verify an opportunity through the organization's "
    "official website or your institution's placement cell before sharing "
    "personal documents."
)


def generate_recommendations(risk_result: Dict) -> List[str]:
    """
    Given the risk_engine output, produce a de-duplicated, ordered list of
    actionable recommendations tied to the factors that were actually found.
    """
    factors = risk_result.get("factors", [])
    recommendations = []

    for factor in factors:
        advice = RECOMMENDATION_MAP.get(factor["factor"])
        if advice and advice not in recommendations:
            recommendations.append(advice)

    if not recommendations:
        recommendations.append(
            "No major red flags were detected, but you should still verify "
            "the organization independently, confirm the offer in writing, "
            "and never share sensitive documents before an official offer."
        )

    recommendations.append(GENERAL_SAFETY_TIP)
    return recommendations
