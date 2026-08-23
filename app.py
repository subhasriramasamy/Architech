"""
ScamCheck - AI-Powered Opportunity Verification System
=========================================================
Main Streamlit application entry point.

Run with:
    streamlit run app.py
"""

import os
import sys

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

# Make sure local modules are importable regardless of working directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules import text_analyzer, url_analyzer, entity_extractor
from modules import risk_engine, recommendation_engine, company_verifier
from modules import ocr_processor
from database import database

# ---------------------------------------------------------------------------
# Page config + one-time setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ScamCheck | Opportunity Verification System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_opportunities.csv")
KAGGLE_DATASET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "internship_job_scam_dataset.csv")


@st.cache_data
def load_sample_data():
    return pd.read_csv(DATA_PATH)


@st.cache_data
def load_kaggle_dataset(path: str = KAGGLE_DATASET_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    for column in ["title", "text", "label", "risk_level", "red_flags"]:
        if column not in df.columns:
            df[column] = ""
    df["label"] = df["label"].fillna("").astype(str).str.strip()
    df["risk_level"] = df["risk_level"].fillna("").astype(str).str.strip()
    return df


def summarize_dataset(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total": 0, "fraudulent": 0, "suspicious": 0, "legitimate": 0, "high": 0, "medium": 0, "low": 0}

    label_counts = df["label"].str.lower().value_counts().to_dict()
    risk_counts = df["risk_level"].str.lower().value_counts().to_dict()
    return {
        "total": int(len(df)),
        "fraudulent": int(label_counts.get("fraudulent", 0)),
        "suspicious": int(label_counts.get("suspicious", 0)),
        "legitimate": int(label_counts.get("legitimate", 0)),
        "high": int(risk_counts.get("high", 0)),
        "medium": int(risk_counts.get("medium", 0)),
        "low": int(risk_counts.get("low", 0)),
    }


# ---------------------------------------------------------------------------
# Global styling (cybersecurity / AI inspired theme)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp {
        background: radial-gradient(circle at top left, #0f172a 0%, #0b1120 55%, #05070d 100%);
        color: #e2e8f0;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1120 0%, #111827 100%);
        border-right: 1px solid #1e293b;
    }

    h1, h2, h3, h4 {
        color: #f8fafc !important;
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }

    .scamcheck-hero {
        text-align: center;
        padding: 2.5rem 1rem 1rem 1rem;
    }
    .scamcheck-hero h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .scamcheck-tagline {
        font-size: 1.15rem;
        color: #94a3b8;
        font-style: italic;
    }

    .feature-card {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 1.4rem;
        height: 100%;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        border-color: #38bdf8;
    }
    .feature-card h3 { margin-top: 0; color: #38bdf8 !important; }
    .feature-card p { color: #cbd5e1; font-size: 0.92rem; }

    section[data-testid="stSidebar"] {
        background: rgba(5, 11, 22, 0.92);
        border-right: 1px solid rgba(56, 189, 248, 0.5);
        padding-top: 1.2rem;
    }
    section[data-testid="stSidebar"] .stButton {
        margin-top: 0.2rem;
    }
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        display: block;
    }
    .nav-button {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 0.75rem 0.9rem !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        margin-bottom: 0.2rem !important;
    }
    .nav-button:hover {
        background: rgba(148, 163, 184, 0.07) !important;
        border-color: rgba(56, 189, 248, 0.18) !important;
    }
    .nav-button.active {
        background: rgba(56, 189, 248, 0.08) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
        box-shadow: inset 0 0 0 1px rgba(56, 189, 248, 0.08) !important;
    }
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.3rem 0.4rem 0.8rem 0.4rem;
        margin-bottom: 0.3rem;
    }
    .sidebar-brand .brand-icon {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #3b82f6, #0ea5e9); 
        box-shadow: 0 0 0 1px rgba(14, 165, 233, 0.35);
        font-size: 1.4rem;
    }
    .sidebar-brand .brand-text {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #e2e8f0;
    }
    .sidebar-subtitle {
        font-size: 1.05rem;
        color: #cbd5e1;
        line-height: 1.4;
        margin: 0.4rem 0 1.2rem 0;
        padding-left: 0.35rem;
    }

    .risk-badge {
        display: inline-block;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }
    .risk-low { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid #16a34a; }
    .risk-moderate { background: rgba(250,204,21,0.15); color: #fde047; border: 1px solid #ca8a04; }
    .risk-high { background: rgba(249,115,22,0.15); color: #fb923c; border: 1px solid #c2410c; }
    .risk-critical { background: rgba(239,68,68,0.18); color: #f87171; border: 1px solid #b91c1c; }

    .indicator-card {
        background: rgba(15, 23, 42, 0.75);
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
    }
    .indicator-card.HIGH { border-left-color: #ef4444; }
    .indicator-card.MODERATE { border-left-color: #eab308; }
    .indicator-card.LOW { border-left-color: #22c55e; }

    .entity-pill {
        display: inline-block;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid #38bdf8;
        color: #7dd3fc;
        border-radius: 999px;
        padding: 0.2rem 0.75rem;
        margin: 0.15rem;
        font-size: 0.85rem;
    }

    div.stButton > button {
        background: linear-gradient(90deg, #38bdf8, #a855f7);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.4rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    div.stButton > button:hover {
        opacity: 0.9;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

RISK_CSS_CLASS = {
    "LOW RISK": "risk-low",
    "MODERATE RISK": "risk-moderate",
    "HIGH RISK": "risk-high",
    "CRITICAL RISK": "risk-critical",
}

DEMO_EXAMPLES = {
    "-- Select a demo example --": "",
    "High-Risk Internship": (
        "Congratulations! You have been SELECTED for our Work From Home Data "
        "Entry Internship. Guaranteed job, no interview required. To confirm "
        "your seat, pay a refundable registration fee of Rs 1999 via UPI to "
        "quickhire@ybl within 24 hours. Limited seats, offer expires today! "
        "Contact us at hr.quickhire@gmail.com or +919876543210 for the "
        "payment link: http://quickhire-jobs.xyz/confirm"
    ),
    "Suspicious Job Offer": (
        "URGENT: Immediate joining available for Content Writing job. 100% "
        "placement guaranteed. Earn Rs 80000 per month working just 2 hours "
        "a day. Send your bank account details and Aadhaar number to verify "
        "eligibility. Act immediately, only 3 seats left! Visit "
        "http://192.168.10.44/apply-now to register."
    ),
    "Legitimate-Looking Internship": (
        "We are pleased to offer you a Software Development Internship at "
        "Infotech Solutions Pvt Ltd. The role involves working on our web "
        "application team under the guidance of a senior developer. "
        "Duration: 3 months. Stipend: Rs 15000 per month. Please find the "
        "detailed job description and requirements attached. For queries, "
        "contact hr@infotechsolutions.com or visit our careers page at "
        "https://www.infotechsolutions.com/careers."
    ),
}


# ---------------------------------------------------------------------------
# Core analysis pipeline (shared by text page + screenshot page)
# ---------------------------------------------------------------------------
def run_full_analysis(raw_text: str, company_name: str = "", company_website: str = "",
                       recruiter_email: str = "", recruiter_phone: str = "") -> dict:
    text_result = text_analyzer.analyze_text(raw_text)
    url_result = url_analyzer.analyze_urls(raw_text)
    entities = entity_extractor.extract_entities(raw_text, provided_company=company_name)
    company_result = company_verifier.verify_company(
        company_name=company_name,
        company_website=company_website,
        recruiter_email=recruiter_email or (entities["emails"][0] if entities["emails"] else ""),
        recruiter_phone=recruiter_phone,
    )
    risk_result = risk_engine.calculate_risk(text_result, url_result, entities, company_result)
    recommendations = recommendation_engine.generate_recommendations(risk_result)

    return {
        "text_result": text_result,
        "url_result": url_result,
        "entities": entities,
        "company_result": company_result,
        "risk_result": risk_result,
        "recommendations": recommendations,
    }


def render_gauge(score: int, risk_level: str):
    color_map = {
        "LOW RISK": "#4ade80",
        "MODERATE RISK": "#fde047",
        "HIGH RISK": "#fb923c",
        "CRITICAL RISK": "#f87171",
    }
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": " / 100", "font": {"size": 40, "color": "#f8fafc"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
            "bar": {"color": color_map.get(risk_level, "#38bdf8")},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "rgba(34,197,94,0.2)"},
                {"range": [25, 50], "color": "rgba(250,204,21,0.2)"},
                {"range": [50, 75], "color": "rgba(249,115,22,0.2)"},
                {"range": [75, 100], "color": "rgba(239,68,68,0.2)"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_factor_chart(factors):
    if not factors:
        return
    names = [f["factor"] for f in factors]
    weights = [f["weight"] for f in factors]
    colors = {"HIGH": "#f87171", "MODERATE": "#fde047", "LOW": "#4ade80"}
    bar_colors = [colors.get(f["severity"], "#38bdf8") for f in factors]

    fig = go.Figure(go.Bar(
        x=weights, y=names, orientation="h",
        marker_color=bar_colors,
        text=[f"+{w}" for w in weights],
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
        xaxis={"title": "Score Contribution", "range": [0, max(weights) + 10]},
        margin=dict(l=10, r=10, t=10, b=10),
        height=max(220, 45 * len(factors)),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_results_dashboard(result: dict, opportunity_label: str = "", source: str = "text",
                              raw_text: str = ""):
    risk = result["risk_result"]
    score = risk["score"]
    level = risk["risk_level"]
    css_class = RISK_CSS_CLASS.get(level, "risk-moderate")

    st.markdown("---")
    st.subheader("Overall Risk")

    col1, col2 = st.columns([1, 1.3])
    with col1:
        render_gauge(score, level)
        st.markdown(
            f'<div style="text-align:center;">'
            f'<span class="risk-badge {css_class}">{level}</span></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown("#### Why ScamCheck Flagged This")
        st.info(risk["summary"])

    # --- Risk indicators -------------------------------------------------
    st.markdown("#### Risk Indicators")
    if risk["factors"]:
        render_factor_chart(risk["factors"])
        for factor in risk["factors"]:
            st.markdown(
                f"""
                <div class="indicator-card {factor['severity']}">
                    <b>{factor['severity']}</b> &nbsp;|&nbsp; <b>{factor['factor']}</b>
                    &nbsp; <span style="color:#94a3b8;">+{factor['weight']} points</span>
                    <p style="margin-top:0.4rem; margin-bottom:0; color:#cbd5e1;">{factor['explanation']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.success("No weighted risk factors were triggered by the current rule set.")

    # --- Extracted entities -----------------------------------------------
    st.markdown("#### Extracted Information")
    entities = result["entities"]
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        st.markdown(f"**Company:** {entities['company_name'] or 'Not detected'}")
        if entities["emails"]:
            st.markdown("**Emails:** " + " ".join(f'<span class="entity-pill">{e}</span>' for e in entities["emails"]), unsafe_allow_html=True)
        if entities["phones"]:
            st.markdown("**Phones:** " + " ".join(f'<span class="entity-pill">{p}</span>' for p in entities["phones"]), unsafe_allow_html=True)
    with ecol2:
        if entities["upi_ids"]:
            st.markdown("**UPI IDs:** " + " ".join(f'<span class="entity-pill">{u}</span>' for u in entities["upi_ids"]), unsafe_allow_html=True)
        if entities["salary_mentions"]:
            st.markdown("**Salary/Stipend:** " + " ".join(f'<span class="entity-pill">{s}</span>' for s in entities["salary_mentions"]), unsafe_allow_html=True)
        if entities["payment_amounts"]:
            st.markdown("**Payment Mentions:** " + " ".join(f'<span class="entity-pill">{p}</span>' for p in entities["payment_amounts"]), unsafe_allow_html=True)

    if result["url_result"]["urls_found"]:
        st.markdown("**URLs Found:**")
        for analysis in result["url_result"]["analyses"]:
            st.markdown(
                f"- `{analysis['url']}` &nbsp; → &nbsp; **{analysis['risk_level']} RISK**",
                unsafe_allow_html=True,
            )
            with st.expander("Why this URL risk level?"):
                for reason in analysis["reasons"]:
                    st.write(f"- {reason}")
        st.caption(result["url_result"]["disclaimer"])

    # --- Recommendations ---------------------------------------------------
    st.markdown("#### Recommended Next Steps")
    for rec in result["recommendations"]:
        st.markdown(f"✅ {rec}")

    # --- Save to history ---------------------------------------------------
    label = opportunity_label or entities["company_name"] or "Untitled Opportunity"
    factor_names = [f["factor"] for f in risk["factors"]]
    database.save_analysis(
        opportunity_label=label,
        risk_score=score,
        risk_level=level,
        indicators=factor_names,
        source=source,
        raw_text=raw_text[:2000],
    )
    st.caption("This analysis has been saved to your Analysis History.")


# ---------------------------------------------------------------------------
# Authentication gate
# ---------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "Login"
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if not st.session_state.authenticated:
    st.title("Access your workspace")

    if st.session_state.auth_view == "Login":
       st.subheader("Login")
       with st.form("login_form", clear_on_submit=False):
           username = st.text_input("Username or Email", key="login_username")
           password = st.text_input("Password", type="password", key="login_password")
           login_clicked = st.form_submit_button("Login", use_container_width=True)

           if login_clicked:
               user = database.authenticate_user(username, password)
               if user:
                   st.session_state.authenticated = True
                   st.session_state.auth_user = user
                   st.session_state.auth_view = "Login"
                   st.rerun()
               else:
                   st.error("Invalid username/email or password.")

       if st.button("Create an account", use_container_width=True):
           st.session_state.auth_view = "Sign Up"
           st.rerun()

    else:
       st.subheader("Sign Up")
       with st.form("signup_form", clear_on_submit=False):
           new_username = st.text_input("Username", key="signup_username")
           new_email = st.text_input("Email", key="signup_email")
           new_password = st.text_input("Password", type="password", key="signup_password")
           signup_clicked = st.form_submit_button("Create Account", use_container_width=True)

           if signup_clicked:
               result = database.register_user(new_username, new_email, new_password)
               if result["success"]:
                   st.success(result["message"])
                   st.session_state.auth_view = "Login"
                   st.rerun()
               else:
                   st.error(result["message"])

       if st.button("Back to Login", use_container_width=True):
           st.session_state.auth_view = "Login"
           st.rerun()

    st.stop()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
       """
       <div class="sidebar-brand">
           <div class="brand-text">ScamCheck</div>
       </div>
       <div class="sidebar-subtitle">AI-Powered Opportunity Verification System</div>
       """,
       unsafe_allow_html=True,
    )

    nav_items = [
       "Home",
       "Analyze Opportunity",
       "Screenshot Analyzer",
       "Dataset Explorer",
       "Analysis History",
       "About ScamCheck",
    ]

    if "selected_page" not in st.session_state:
       st.session_state.selected_page = "Home"

    for label in nav_items:
       if st.button(label, key=f"nav_{label}", use_container_width=True):
           st.session_state.selected_page = label
           st.rerun()

    st.markdown("---")
    if st.session_state.auth_user:
       st.caption(f"Logged in as: {st.session_state.auth_user['username']}")
    if st.button("Logout", use_container_width=True):
       st.session_state.authenticated = False
       st.session_state.auth_user = None
       st.session_state.auth_view = "Login"
       st.rerun()
    st.caption("Verify before you trust.")

    page = st.session_state.selected_page

if "prefill_text" not in st.session_state:
    st.session_state.prefill_text = ""
if "goto_analyze" not in st.session_state:
    st.session_state.goto_analyze = False

if st.session_state.goto_analyze:
    page = "Analyze Opportunity"
    st.session_state.goto_analyze = False


# ---------------------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------------------
if page == "Home":
    st.markdown(
        """
        <div class="scamcheck-hero">
            <h1>ScamCheck</h1>
            <p class="scamcheck-tagline">"Verify before you trust."</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style="text-align:center; max-width:750px; margin: 0 auto 2rem auto; color:#cbd5e1;">
        ScamCheck helps students identify potentially fraudulent internship and job
        opportunities by analyzing suspicious language, payment requests, contact
        information, URLs, and other risk indicators.
        </p>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """<div class="feature-card"><h3> AI Risk Analysis</h3>
            <p>Multi-signal detection across payment requests, urgency language,
            guaranteed-job claims, and suspicious recruitment patterns.</p></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """<div class="feature-card"><h3>🔍 Explainable Warnings</h3>
            <p>Every point on the risk score is traceable to a specific,
            plain-language explanation -- never a black-box verdict.</p></div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="feature-card"><h3> Opportunity Verification</h3>
            <p>Extracts contact details, links, and compensation claims so you
            can independently verify before you respond.</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button(" Start Analysis", use_container_width=True):
            st.session_state.goto_analyze = True
            st.rerun()


# ---------------------------------------------------------------------------
# ANALYZE OPPORTUNITY PAGE
# ---------------------------------------------------------------------------
elif page == "Analyze Opportunity":
    st.title("🔎 Analyze Opportunity")

    with st.expander(" Examples "):
        demo_choice = st.selectbox("Load a sample message:", list(DEMO_EXAMPLES.keys()))
        if demo_choice != "-- Select a demo example --":
            st.session_state.prefill_text = DEMO_EXAMPLES[demo_choice]

    with st.form("analyze_opportunity_form", clear_on_submit=False):
        opportunity_text = st.text_area(
            "Paste your internship/job opportunity here...",
            value=st.session_state.prefill_text,
            height=220,
            key="opportunity_text_area",
        )

        st.markdown("##### Optional Verification Details")
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name")
            recruiter_email = st.text_input("Recruiter Email")
        with col2:
            company_website = st.text_input("Company Website")
            recruiter_phone = st.text_input("Recruiter Phone Number")

        analyze_clicked = st.form_submit_button("ANALYZE OPPORTUNITY", use_container_width=True)

    if analyze_clicked:
        if not opportunity_text or not opportunity_text.strip():
            st.error("Please paste an opportunity message before analyzing.")
        else:
            with st.spinner("Analyzing opportunity..."):
                result = run_full_analysis(
                    opportunity_text,
                    company_name=company_name,
                    company_website=company_website,
                    recruiter_email=recruiter_email,
                    recruiter_phone=recruiter_phone,
                )
            render_results_dashboard(
                result,
                opportunity_label=company_name,
                source="text",
                raw_text=opportunity_text,
            )


# ---------------------------------------------------------------------------
# SCREENSHOT ANALYZER PAGE
# ---------------------------------------------------------------------------
elif page == "Screenshot Analyzer":
    st.title(" Screenshot Analyzer")
    st.caption("Upload Screenshot → OCR → Extracted Text → Analyze → Risk Score → Warnings")

    uploaded_file = st.file_uploader("Upload a screenshot (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Screenshot", use_container_width=True)

        if st.button(" Run OCR & Analyze", use_container_width=True):
            with st.spinner("Extracting text with OCR..."):
                ocr_result = ocr_processor.extract_text_from_image(image)

            if not ocr_result["success"]:
                st.error(ocr_result["error"])
            else:
                st.markdown("#### Extracted Text")
                st.text_area("OCR Output", value=ocr_result["text"], height=180, disabled=True)

                with st.spinner("Analyzing extracted text..."):
                    result = run_full_analysis(ocr_result["text"])
                render_results_dashboard(
                    result,
                    opportunity_label="Screenshot Upload",
                    source="screenshot",
                    raw_text=ocr_result["text"],
                )


# ---------------------------------------------------------------------------
# DATASET EXPLORER PAGE
# ---------------------------------------------------------------------------
elif page == "Dataset Explorer":
    st.title(" Dataset Explorer")
    dataset_df = load_kaggle_dataset()

    if dataset_df.empty:
        st.warning("The Kaggle dataset file was not found in the project data folder. Copy it into data/internship_job_scam_dataset.csv to enable this view.")
    else:
        summary = summarize_dataset(dataset_df)
        st.caption("Connected to the uploaded Kaggle internship/job scam dataset.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total rows", summary["total"])
        c2.metric("Fraudulent", summary["fraudulent"])
        c3.metric("Suspicious", summary["suspicious"])
        c4.metric("Legitimate", summary["legitimate"])

        st.markdown("#### Dataset preview")
        preview = dataset_df[["title", "label", "risk_level", "red_flags", "source_dataset"]].head(20).copy()
        st.dataframe(preview, use_container_width=True, hide_index=True)

        st.markdown("#### Analyze a dataset example")
        sample_index = st.selectbox(
            "Choose a record",
            dataset_df.index.tolist(),
            format_func=lambda idx: f"{idx}: {dataset_df.loc[idx, 'title'][:60]} ({dataset_df.loc[idx, 'label']})",
        )

        if st.button("Run analysis on selected dataset example", use_container_width=True):
            row = dataset_df.loc[sample_index]
            text = str(row.get("text", "") or "")
            if not text.strip():
                st.warning("This record does not contain any text to analyze.")
            else:
                with st.spinner("Analyzing selected dataset sample..."):
                    result = run_full_analysis(
                        text,
                        company_name=str(row.get("title", "") or ""),
                        company_website="",
                        recruiter_email="",
                        recruiter_phone="",
                    )
                render_results_dashboard(
                    result,
                    opportunity_label=str(row.get("title", "")) or f"Dataset row {sample_index}",
                    source="dataset",
                    raw_text=text,
                )

# ---------------------------------------------------------------------------
# ANALYSIS HISTORY PAGE
# ---------------------------------------------------------------------------
elif page == "Analysis History":
    st.title("Analysis History")

    history = database.fetch_all_analyses()

    if not history:
        st.info("No analyses yet. Run one from 'Analyze Opportunity' or 'Screenshot Analyzer'.")
    else:
        df = pd.DataFrame([
            {
                "ID": h["id"],
                "Timestamp": h["timestamp"],
                "Opportunity": h["opportunity_label"],
                "Score": h["risk_score"],
                "Risk Level": h["risk_level"],
                "Source": h["source"],
            }
            for h in history
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("#### View a Past Analysis")
        selected_id = st.selectbox("Select an analysis ID", df["ID"].tolist())
        if st.button("View Details"):
            record = database.fetch_analysis_by_id(int(selected_id))
            if record:
                css_class = RISK_CSS_CLASS.get(record["risk_level"], "risk-moderate")
                st.markdown(
                    f'<span class="risk-badge {css_class}">{record["risk_level"]}</span> '
                    f'&nbsp; **Score: {record["risk_score"]} / 100**',
                    unsafe_allow_html=True,
                )
                st.write(f"**Opportunity:** {record['opportunity_label']}")
                st.write(f"**Timestamp:** {record['timestamp']}")
                st.write(f"**Source:** {record['source']}")
                st.write("**Major Indicators:**")
                if record["indicators"]:
                    for ind in record["indicators"]:
                        st.write(f"- {ind}")
                else:
                    st.write("None recorded.")
                if record.get("raw_text"):
                    with st.expander("Original submitted text"):
                        st.write(record["raw_text"])

        st.markdown("---")
        if st.button(" Clear All History"):
            database.clear_history()
            st.success("History cleared.")
            st.rerun()


# ---------------------------------------------------------------------------
# ABOUT PAGE
# ---------------------------------------------------------------------------
elif page == "About ScamCheck":
    st.title("About ScamCheck")

    st.markdown("#### What is ScamCheck?")
    st.write(
        "ScamCheck is an AI-assisted opportunity verification tool built for "
        "students who receive internship and job offers through WhatsApp, "
        "email, Telegram, LinkedIn, Instagram, and other platforms. It "
        "analyzes the text of an opportunity (or a screenshot of one) and "
        "produces an explainable risk assessment."
    )

    st.markdown("#### Why is it useful?")
    st.write(
        "Scam job postings are increasingly common and often mimic the tone "
        "of real recruiters. ScamCheck helps students pause and evaluate an "
        "opportunity systematically, instead of relying on gut feeling alone, "
        "before sharing money or personal information."
    )

    st.markdown("#### How does the risk engine work?")
    st.write(
        "ScamCheck scans the submitted text for known categories of "
        "risk language (payment requests, urgency, guaranteed-job claims, "
        "sensitive-information requests, and suspicious recruitment "
        "patterns), extracts structured entities (emails, phone numbers, "
        "UPI IDs, URLs, and salary figures), and runs basic structural "
        "checks on any links and recruiter contact details. Each detected "
        "signal contributes a transparent, pre-defined weight to a 0-100 "
        "score. No single keyword can push the score into a high category "
        "on its own -- the system is designed to combine multiple weak "
        "signals into a stronger, explainable picture."
    )

    st.markdown("#### What technologies are used?")
    st.write(
        "Python, Streamlit, Pandas, NumPy, regular expressions for pattern "
        "matching, Plotly for visualizations, SQLite for analysis history, "
        "and Tesseract OCR (via pytesseract) for screenshot text extraction."
    )

    st.warning(
        "**Disclaimer:** ScamCheck provides a preliminary risk assessment "
        "and does not guarantee that an opportunity is legitimate or "
        "fraudulent. Users should independently verify organizations "
        "through trusted official sources."
    )
