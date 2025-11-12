"""
AI Visibility Audit Tool - Streamlit Frontend
Version: 0.1.0
Complete P0 Features: Audit, History, Citations, API Keys, Plans
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time

from ai_visibility_mvp.frontend.backend_client import get_backend_client
from vysalytica.config import (
    DEFAULT_API_BASE_URL,
    get_anthropic_api_key,
    get_api_base_url,
    get_openai_api_key,
    get_routellm_api_key,
)
from vysalytica.db.migrations import run_migrations

# Page configuration
st.set_page_config(
    page_title="AI Visibility Audit Tool",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

run_migrations()

backend_client = get_backend_client()
CONFIGURED_API_BASE_URL = get_api_base_url()
API_BASE_URL = backend_client.base_url or ""

ROUTELLM_API_KEY = get_routellm_api_key()
OPENAI_API_KEY = get_openai_api_key()
ANTHROPIC_API_KEY = get_anthropic_api_key()

CHATGPT_BACKEND_AVAILABLE = bool(ROUTELLM_API_KEY or OPENAI_API_KEY)
CLAUDE_BACKEND_AVAILABLE = bool(ROUTELLM_API_KEY or ANTHROPIC_API_KEY)

# Custom CSS for better styling and "Coming Soon" overlay
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .score-badge {
        font-size: 2rem;
        font-weight: bold;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .score-excellent { background-color: #d4edda; color: #155724; }
    .score-good { background-color: #d1ecf1; color: #0c5460; }
    .score-warning { background-color: #fff3cd; color: #856404; }
    .score-poor { background-color: #f8d7da; color: #721c24; }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .blur-content { 
        filter: blur(8px); 
        pointer-events: none; 
    }
    .coming-soon-overlay { 
        position: fixed; 
        top: 0; 
        left: 0; 
        width: 100%; 
        height: 100%; 
        background: rgba(0, 0, 0, 0.7); 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        z-index: 9999; 
    }
    .coming-soon-text { 
        color: white; 
        font-size: 48px; 
        font-weight: bold; 
        text-align: center; 
    }
</style>
""",
    unsafe_allow_html=True,
)


# Utility Functions
def make_api_request(endpoint, method="GET", data=None, headers=None):
    """Route Streamlit requests through the configured backend client."""
    method = (method or "GET").upper()
    payload = data or {}
    headers = headers or {}
    normalized_endpoint = endpoint.lstrip("/")

    try:
        if normalized_endpoint == "health":
            return backend_client.health()

        if normalized_endpoint == "audit" and method == "POST":
            return backend_client.run_audit(
                url=payload.get("url", ""),
                plan=payload.get("plan", "quickscan"),
                packs=payload.get("packs") or ["base"],
                api_key=headers.get("X-API-Key"),
            )

        if normalized_endpoint == "audit/history":
            return backend_client.get_audit_history(
                domain=payload.get("domain"),
                limit=payload.get("limit", 10),
            )

        if normalized_endpoint.startswith("audit/") and method == "GET":
            try:
                audit_id = int(normalized_endpoint.split("/", 1)[1])
            except (IndexError, ValueError):
                return None, "Invalid audit identifier"
            return backend_client.get_audit_detail(audit_id)

        if normalized_endpoint == "citations/track":
            return backend_client.track_citations(
                brand=payload.get("brand", ""),
                intent=payload.get("intent", ""),
                assistants=payload.get("assistants") or ["chatgpt", "claude"],
            )

        if normalized_endpoint == "citations/stats":
            brand = payload.get("brand")
            if not brand:
                return None, "Brand parameter is required"
            return backend_client.get_citation_stats(brand)

        if normalized_endpoint == "citations/history":
            assistants_value = payload.get("assistants")
            if isinstance(assistants_value, str):
                assistants_value = [
                    item.strip() for item in assistants_value.split(",") if item.strip()
                ]
            return backend_client.get_citation_history(
                brand=payload.get("brand"),
                assistants=assistants_value,
                intent=payload.get("intent"),
                limit=payload.get("limit", 50),
            )

        if normalized_endpoint == "keys/create" and method == "POST":
            quota = int(payload.get("quota_per_hour", 10))
            return backend_client.create_api_key(payload.get("name"), quota)

        if normalized_endpoint == "keys/list":
            return backend_client.list_api_keys()

        if normalized_endpoint == "plans":
            return backend_client.get_plans()

        if normalized_endpoint == "plans/compare":
            return backend_client.compare_plans()

        if normalized_endpoint == "answer_graph/build" and method == "POST":
            return backend_client.build_answer_graph(
                domain=payload.get("domain", ""),
                intents=payload.get("intents") or [],
                packs=payload.get("packs") or ["base"],
            )

        if normalized_endpoint == "playbooks/generate" and method == "POST":
            return backend_client.generate_playbook(
                domain=payload.get("domain", ""),
                intent=payload.get("intent", ""),
                target_assistant=payload.get("target_assistant", "chatgpt"),
            )

        return None, f"Unsupported endpoint: {endpoint}"
    except Exception as exc:  # pragma: no cover - defensive
        return None, str(exc)


def get_score_class(score):
    """Get CSS class based on score"""
    if score >= 90:
        return "score-excellent"
    elif score >= 75:
        return "score-good"
    elif score >= 60:
        return "score-warning"
    else:
        return "score-poor"


def display_score_badge(score, label="Overall Score"):
    """Display score with styled badge"""
    score_class = get_score_class(score)
    st.markdown(
        f"""
    <div class="score-badge {score_class}">
        {label}: {score:.1f}/100
    </div>
    """,
        unsafe_allow_html=True,
    )


def display_coming_soon_overlay():
    """Display 'Coming Soon' overlay for disabled pages"""
    st.markdown(
        """
    <div class="coming-soon-overlay">
        <div class="coming-soon-text">Coming Soon</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def display_findings(findings):
    """Display findings with status badges"""
    if not findings:
        st.info("No findings in this category")
        return

    for finding in findings:
        status = finding.get("status", "unknown")

        # Status badge
        if status == "pass":
            badge = "✅ PASS"
            color = "green"
        elif status == "fail":
            badge = "❌ FAIL"
            color = "red"
        elif status == "partial":
            badge = "⚠️ PARTIAL"
            color = "orange"
        else:
            badge = "❓ UNKNOWN"
            color = "gray"

        with st.expander(f"{badge} - {finding.get('title', 'Unknown Rule')}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Rule ID:** `{finding.get('id', 'N/A')}`")
                st.markdown(f"**Category:** {finding.get('category', 'N/A')}")

                confidence = finding.get("confidence")
                if confidence is not None:
                    st.markdown(f"**Confidence:** {confidence * 100:.0f}%")

                if finding.get("why"):
                    st.markdown(f"**Why it matters:** {finding['why']}")

                if finding.get("fix"):
                    st.markdown(f"**How to fix:** {finding['fix']}")

                # Evidence
                evidence = finding.get("evidence", [])
                if evidence:
                    st.markdown("**Evidence:**")
                    for ev in evidence[:3]:  # Show first 3
                        if isinstance(ev, dict):
                            st.code(ev.get("snippet", ""), language=None)

            with col2:
                # Fix snippet (if available)
                if finding.get("fix_snippet"):
                    st.markdown("**💡 Fix Snippet:**")
                    st.code(finding["fix_snippet"], language="html")

                # Acceptance test (if available)
                if finding.get("acceptance_test"):
                    st.markdown("**🧪 Test:**")
                    st.code(finding["acceptance_test"], language="python")


# Header
st.markdown(
    '<h1 class="main-header">🤖 AI Visibility Audit Tool</h1>', unsafe_allow_html=True
)
st.markdown(
    '<p class="subtitle">Analyze your website for AI discoverability across ChatGPT, Claude, and more</p>',
    unsafe_allow_html=True,
)

# Sidebar Navigation
st.sidebar.title("Navigation")
if backend_client.mode == "remote" and API_BASE_URL:
    st.sidebar.caption(f"Backend mode: Remote API ({API_BASE_URL})")
    if CONFIGURED_API_BASE_URL == DEFAULT_API_BASE_URL:
        st.sidebar.caption(
            "Using default API base URL. Update API_BASE_URL for production deployments."
        )
else:
    st.sidebar.caption("Backend mode: Local (in-process)")
    st.sidebar.caption(
        "Set API_BASE_URL in Streamlit secrets or environment variables to connect to a remote API deployment."
    )

if not CHATGPT_BACKEND_AVAILABLE:
    st.sidebar.warning(
        "RouteLLM or OpenAI API key not configured. Citation tracking and auto-fix features will be unavailable."
    )
elif not CLAUDE_BACKEND_AVAILABLE:
    st.sidebar.info(
        "Claude tracking requires ANTHROPIC_API_KEY or RouteLLM credentials."
    )

page = st.sidebar.radio(
    "Choose a feature:",
    [
        "🏠 Home",
        "🔍 Run Audit",
        "📊 Audit History",
        "🤖 Citation Tracking",
        "🕸️ Answer Graph & Playbooks",
        "🔑 API Keys",
        "💰 Plans & Pricing",
        "ℹ️ About",
    ],
)

# Initialize session state
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "last_audit" not in st.session_state:
    st.session_state.last_audit = None

# ==================== HOME PAGE ====================
if page == "🏠 Home":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("Welcome to AI Visibility Audit Tool v0.1.0")

    if backend_client.mode == "local":
        st.info(
            "Running in local mode. Audits, history, and exports execute directly without the Flask API. "
            "Set API_BASE_URL to connect to a remote backend deployment."
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        ### 🔍 Audit Features
        - **Crawlability** checks
        - **Schema.org** validation
        - **Content quality** analysis
        - **Technical SEO** evaluation
        - **AI-specific** optimizations
        """
        )

    with col2:
        st.markdown(
            """
        ### 🤖 AI Citation Tracking
        - Track **ChatGPT** mentions
        - Track **Claude** mentions
        - View citation statistics
        - Historical tracking
        - Brand visibility metrics
        """
        )

    with col3:
        st.markdown(
            """
        ### 💰 Flexible Plans
        - **QuickScan** (Free): 3 pages
        - **Full** ($49): 12 pages + fixes
        - **Agency** ($199): Unlimited
        - Auto-fix suggestions
        - Audit history
        """
        )

    st.divider()

    # Quick stats
    st.subheader("📈 Platform Statistics")

    col1, col2, col3, col4 = st.columns(4)

    # Get health status
    health, error = make_api_request("/health")

    with col1:
        st.metric("Server Status", "✅ Online" if health else "❌ Offline")

    with col2:
        # Get audit history count
        history, _ = make_api_request("/audit/history")
        count = len(history.get("data", {}).get("audits", [])) if history else 0
        st.metric("Total Audits", count)

    with col3:
        st.metric("Features", "5 P0 Complete")

    with col4:
        st.metric("Version", "v0.1.0")

    st.divider()

    # Quick start guide
    st.subheader("🚀 Quick Start")

    st.markdown(
        """
    **1. Try QuickScan (Free)**
    - Go to **Run Audit** page
    - Enter any website URL
    - Select "QuickScan" plan
    - No API key needed!

    **2. Upgrade to Full**
    - Go to **API Keys** page
    - Generate a new key
    - Use it for Full audits
    - Get AI-powered fixes

    **3. Track Citations**
    - Go to **Citation Tracking**
    - Enter your brand name
    - See AI mentions
    - View statistics
    """
    )
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for Home page (disabled)
    display_coming_soon_overlay()

    # ==================== RUN AUDIT PAGE ====================
elif page == "🔍 Run Audit":
    st.header("🔍 Run Website Audit")

    # Plan selector
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Audit Configuration")

        # URL input
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the full URL including http:// or https://",
        )

        # Plan selection
        plan = st.selectbox(
            "Select Plan",
            ["quickscan", "full", "agency"],
            help="QuickScan is free, Full and Agency require API key",
        )

        # Pack selection
        available_packs = ["base", "aio", "ecomm", "docs"]
        if plan == "quickscan":
            packs = ["base"]
            st.info("QuickScan uses Base pack only (free tier)")
        else:
            packs = st.multiselect(
                "Rule Packs",
                available_packs,
                default=["base", "aio"],
                help="Select which rule packs to evaluate",
            )

        # API key input for paid plans
        if plan in ["full", "agency"]:
            api_key = st.text_input(
                "API Key",
                type="password",
                value=st.session_state.api_key,
                help="Required for Full and Agency plans",
            )
            if api_key:
                st.session_state.api_key = api_key
        else:
            api_key = None

    with col2:
        st.subheader("Plan Details")

        if plan == "quickscan":
            st.markdown(
                """
            **QuickScan (Free)**
            - ✅ No API key required
            - 📄 3 pages max
            - 📦 Base pack only
            - ❌ No fix generation
            - ❌ No history saved
            """
            )
        elif plan == "full":
            st.markdown(
                """
            **Full ($49)**
            - 🔑 API key required
            - 📄 12 pages max
            - 📦 All packs (Base, AI Optimization, E-comm, Docs)
            - ✅ Fix generation
            - ✅ History saved
            """
            )
        else:
            st.markdown(
                """
            **Agency ($199)**
            - 🔑 API key required
            - 📄 100 pages max
            - 📦 All packs (Base, AI Optimization, E-comm, Docs)
            - ✅ Fix generation
            - ✅ History saved
            - ✅ Priority support
            """
            )

        if plan in ["full", "agency"] and not CHATGPT_BACKEND_AVAILABLE:
            st.warning(
                "Auto-fix generation requires a RouteLLM or OpenAI API key configured via Streamlit secrets or environment."
            )

    st.divider()

    # Run audit button
    if st.button("🚀 Run Audit", type="primary", use_container_width=True):
        if not url:
            st.error("Please enter a website URL")
        elif plan in ["full", "agency"] and not api_key:
            st.error(f"{plan.title()} plan requires an API key")
        else:
            with st.spinner(
                f"Running {plan.title()} audit... This may take 10-60 seconds..."
            ):
                # Prepare request
                data = {"url": url, "plan": plan, "packs": packs}

                headers = {}
                if api_key:
                    headers["X-API-Key"] = api_key

                # Make request
                result, error = make_api_request(
                    "/audit", method="POST", data=data, headers=headers
                )

                if error:
                    st.error(f"Audit failed: {error}")
                else:
                    st.success("✅ Audit completed successfully!")
                    st.session_state.last_audit = result

                    # Display results
                    if result.get("success"):
                        audit_data = result.get("data", {})

                        # Overall score
                        st.subheader("📊 Audit Results")
                        overall_score = audit_data.get("overall_score", 0)
                        display_score_badge(overall_score)

                        # Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Pages Analyzed", audit_data.get("page_count", 0))
                        with col2:
                            findings = audit_data.get("findings", [])
                            passed = len(
                                [f for f in findings if f.get("status") == "pass"]
                            )
                            st.metric("Rules Passed", f"{passed}/{len(findings)}")
                        with col3:
                            failed = len(
                                [f for f in findings if f.get("status") == "fail"]
                            )
                            st.metric("Rules Failed", failed)
                        with col4:
                            if "audit_id" in audit_data:
                                st.metric("Audit ID", audit_data["audit_id"])

                        # Category scores
                        st.subheader("📈 Category Scores")
                        category_scores = audit_data.get("category_scores", {})

                        if category_scores:
                            cols = st.columns(len(category_scores))
                            for idx, (category, score) in enumerate(
                                category_scores.items()
                            ):
                                with cols[idx]:
                                    st.metric(category, f"{score:.1f}/100")

                        # Inline upsell if failed rules detected for free plan
                        if plan == "quickscan":
                            failed = [
                                f
                                for f in audit_data.get("findings", [])
                                if f.get("status") == "fail"
                            ]
                            if failed:
                                st.warning(
                                    "Want AI-generated fixes and saved history? Upgrade to Full to unlock fixes and persistence."
                                )
                                st.info(
                                    "Tip: Generate an API key in the 'API Keys' page, then re-run with the Full plan."
                                )

                        # Findings
                        st.subheader("🔍 Detailed Findings")

                        # Filter tabs
                        tab1, tab2, tab3, tab4 = st.tabs(
                            ["All", "✅ Pass", "❌ Fail", "⚠️ Partial"]
                        )

                        findings = audit_data.get("findings", [])

                        with tab1:
                            display_findings(findings)
                        with tab2:
                            passed_findings = [
                                f for f in findings if f.get("status") == "pass"
                            ]
                            display_findings(passed_findings)
                        with tab3:
                            failed_findings = [
                                f for f in findings if f.get("status") == "fail"
                            ]
                            display_findings(failed_findings)
                        with tab4:
                            partial_findings = [
                                f for f in findings if f.get("status") == "partial"
                            ]
                            display_findings(partial_findings)

# ==================== AUDIT HISTORY PAGE ====================
elif page == "📊 Audit History":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("📊 Audit History")

    # Fetch history
    with st.spinner("Loading audit history..."):
        result, error = make_api_request("/audit/history")

    if error:
        st.error(f"Failed to load history: {error}")
    elif result and result.get("success"):
        audits = result.get("data", {}).get("audits", [])

        if not audits:
            st.info("No audits found. Run your first audit to see it here!")
        else:
            st.success(f"Found {len(audits)} audit(s)")

            # Create DataFrame
            df_data = []
            for audit in audits:
                df_data.append(
                    {
                        "ID": audit.get("id"),
                        "Domain": audit.get("domain"),
                        "Score": f"{audit.get('overall_score', 0):.1f}",
                        "Pages": audit.get("page_count", 0),
                        "Date": audit.get("created_at", ""),
                        "URL": audit.get("url", ""),
                    }
                )

            df = pd.DataFrame(df_data)

            # Display table
            st.dataframe(df, use_container_width=True, hide_index=True)

            # View details
            st.subheader("View Audit Details")
            audit_id = st.selectbox(
                "Select Audit ID",
                options=[a.get("id") for a in audits],
                format_func=lambda x: f"Audit #{x}",
            )

            if st.button("Load Audit Details"):
                with st.spinner(f"Loading audit #{audit_id}..."):
                    detail_result, detail_error = make_api_request(f"/audit/{audit_id}")

                if detail_error:
                    st.error(f"Failed to load audit: {detail_error}")
                elif detail_result and detail_result.get("success"):
                    audit_detail = detail_result.get("data", {})

                    # Display like audit results
                    overall_score = audit_detail.get("overall_score", 0)
                    display_score_badge(overall_score)

                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Domain", audit_detail.get("domain", "N/A"))
                    with col2:
                        st.metric("Pages", audit_detail.get("page_count", 0))
                    with col3:
                        st.metric("Created", audit_detail.get("created_at", "N/A")[:10])

                    # Findings
                    st.subheader("Findings")
                    findings = audit_detail.get("findings", [])
                    display_findings(findings)
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for Audit History page (disabled)
    display_coming_soon_overlay()

# ==================== CITATION TRACKING PAGE ====================
elif page == "🤖 Citation Tracking":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("🤖 AI Citation Tracking")

    st.markdown(
        """
    Track how often AI assistants like ChatGPT and Claude mention your brand.
    This helps you understand your visibility in AI-powered search results.
    """
    )

    if not CHATGPT_BACKEND_AVAILABLE:
        st.warning(
            "Live citation tracking is disabled until a RouteLLM or OpenAI API key is configured via Streamlit secrets or environment variables."
        )
    elif not CLAUDE_BACKEND_AVAILABLE:
        st.info(
            "Claude results require an ANTHROPIC_API_KEY or RouteLLM configuration. Only ChatGPT results will be available."
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Track New Citations")

        brand = st.text_input(
            "Brand Name",
            placeholder="Visalytica",
            help="The brand or company name to track",
        )

        intent = st.text_input(
            "Search Intent/Query",
            placeholder="What is the best AI visibility tool?",
            help="The query to test (how users might search)",
        )

        assistants = st.multiselect(
            "AI Assistants",
            ["chatgpt", "claude"],
            default=["chatgpt"],
            help="Select which AI assistants to query",
        )

        if st.button("🔍 Track Citations", type="primary"):
            if not brand or not intent:
                st.error("Please enter both brand name and search intent")
            elif not assistants:
                st.error("Please select at least one AI assistant")
            else:
                with st.spinner(
                    "Querying AI assistants... This may take 10-30 seconds..."
                ):
                    data = {"brand": brand, "intent": intent, "assistants": assistants}

                    result, error = make_api_request(
                        "/citations/track", method="POST", data=data
                    )

                    if error:
                        st.error(f"Tracking failed: {error}")
                    elif result and result.get("success"):
                        st.success("✅ Citation tracking completed!")

                        results_data = result.get("data", {}).get("results", [])
                        summary = result.get("data", {}).get("summary", {})

                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Queries", summary.get("total", 0))
                        with col2:
                            st.metric("Citations Found", summary.get("cited", 0))
                        with col3:
                            rate = summary.get("rate", 0)
                            st.metric("Citation Rate", f"{rate:.1f}%")

                        # Results
                        st.subheader("Results by Assistant")
                        for result_item in results_data:
                            assistant = result_item.get("assistant", "Unknown")
                            cited = result_item.get("cited", False)
                            response = result_item.get("response", "")
                            error_msg = result_item.get("error")

                            if error_msg:
                                status = "⚠️ ERROR"
                            else:
                                status = "✅ CITED" if cited else "❌ NOT CITED"

                            with st.expander(f"{status} - {assistant}"):
                                st.markdown(
                                    f"**Brand:** {result_item.get('brand', 'N/A')}"
                                )
                                st.markdown(
                                    f"**Intent:** {result_item.get('intent', 'N/A')}"
                                )
                                st.markdown(f"**Cited:** {'Yes' if cited else 'No'}")

                                if error_msg:
                                    st.warning(f"Assistant error: {error_msg}")
                                elif response:
                                    st.markdown("**Response Preview:**")
                                    st.text_area(
                                        "", response[:500], height=150, disabled=True
                                    )

    with col2:
        st.subheader("📊 Citation Statistics")

        stats_brand = st.text_input(
            "Brand for Stats", placeholder="Visalytica", key="stats_brand"
        )

        if st.button("View Statistics"):
            if not stats_brand:
                st.error("Please enter a brand name")
            else:
                with st.spinner("Loading statistics..."):
                    data = {"brand": stats_brand}
                    result, error = make_api_request(
                        "/citations/stats", method="POST", data=data
                    )

                    if error:
                        st.warning(f"No statistics available: {error}")
                    elif result and result.get("success"):
                        stats = result.get("data", {})

                        st.metric("Total Queries", stats.get("total_queries", 0))
                        st.metric("Total Citations", stats.get("citations", 0))
                        st.metric(
                            "Citation Rate", f"{stats.get('citation_rate', 0):.1f}%"
                        )

                        # By assistant
                        by_assistant = stats.get("by_assistant", {})
                        if by_assistant:
                            st.markdown("**By Assistant:**")
                            for assistant, ast_stats in by_assistant.items():
                                st.markdown(
                                    f"**{assistant}:** {ast_stats.get('rate', 0):.1f}%"
                                )

        st.divider()

        st.subheader("📥 Export & History")
        export_brand = st.text_input("Brand for Export/History", key="export_brand")
        export_intent = st.text_input("Intent filter (optional)", key="export_intent")
        assistants = st.multiselect(
            "Assistants filter",
            ["ChatGPT", "Claude"],
            default=["ChatGPT", "Claude"],
        )
        current_context = (export_brand, export_intent, tuple(assistants))

        if "citations_csv_context" not in st.session_state:
            st.session_state["citations_csv_context"] = None
        if "citations_csv_payload" not in st.session_state:
            st.session_state["citations_csv_payload"] = None
        if "citations_history_context" not in st.session_state:
            st.session_state["citations_history_context"] = None
        if "citations_history_data" not in st.session_state:
            st.session_state["citations_history_data"] = None
        if "citations_history_status" not in st.session_state:
            st.session_state["citations_history_status"] = None

        if st.session_state.get("citations_csv_context") != current_context:
            st.session_state["citations_csv_context"] = current_context
            st.session_state["citations_csv_payload"] = None
        if st.session_state.get("citations_history_context") != current_context:
            st.session_state["citations_history_context"] = current_context
            st.session_state["citations_history_data"] = None
            st.session_state["citations_history_status"] = None

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⬇️ Prepare CSV"):
                if not export_brand:
                    st.error("Please enter a brand for export")
                else:
                    with st.spinner("Preparing CSV export..."):
                        csv_payload, csv_error = backend_client.export_citations_csv(
                            brand=export_brand,
                            assistants=assistants,
                            intent=export_intent,
                        )
                    if csv_error:
                        st.error(f"CSV export failed: {csv_error}")
                        st.session_state["citations_csv_payload"] = None
                    elif csv_payload:
                        st.session_state["citations_csv_payload"] = csv_payload
                        st.success("CSV ready. Use the download button below.")
            csv_payload = st.session_state.get("citations_csv_payload")
            if csv_payload:
                st.download_button(
                    "Download citation CSV",
                    data=csv_payload["content"],
                    file_name=csv_payload["filename"],
                    mime=csv_payload["mime"],
                    key="citations_csv_download",
                )

        with col_b:
            if st.button("🔎 View History"):
                if not export_brand:
                    st.error("Please enter a brand to view history")
                else:
                    with st.spinner("Loading citation history..."):
                        history_result, history_error = (
                            backend_client.get_citation_history(
                                brand=export_brand,
                                assistants=assistants,
                                intent=export_intent,
                                limit=75,
                            )
                        )
                    if history_error:
                        st.error(f"History request failed: {history_error}")
                        st.session_state["citations_history_data"] = None
                        st.session_state["citations_history_status"] = None
                    elif history_result:
                        history_rows = history_result.get("data", {}).get("history", [])
                        st.session_state["citations_history_data"] = history_rows
                        st.session_state["citations_history_status"] = (
                            "loaded" if history_rows else "empty"
                        )
            history_rows = st.session_state.get("citations_history_data")
            history_status = st.session_state.get("citations_history_status")
            if history_status == "loaded" and history_rows:
                history_df = pd.DataFrame(history_rows)
                st.dataframe(history_df, use_container_width=True, hide_index=True)
            elif history_status == "empty":
                st.info("No history found for given filters")
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for Citation Tracking page (disabled)
    display_coming_soon_overlay()

# ==================== ANSWER GRAPH & PLAYBOOKS ====================
elif page == "🕸️ Answer Graph & Playbooks":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("🕸️ Answer Graph & Playbooks")

    col1, col2 = st.columns([2, 1])

    with col1:
        domain = st.text_input("Domain", placeholder="example.com")
        intents_input = st.text_area(
            "Intents (one per line)",
            placeholder="best project management tools\ncompare A vs B\nhow to do X",
            height=120,
        )
        intents = [i.strip() for i in intents_input.splitlines() if i.strip()]
        packs = st.multiselect("Packs", ["base", "ecomm", "docs"], default=["base"])

        if st.button("Build Answer Graph", type="primary"):
            if not domain or not intents:
                st.error("Please enter domain and at least one intent")
            else:
                with st.spinner("Building answer graph (~10–20s)..."):
                    payload, err = make_api_request(
                        "/answer_graph/build",
                        method="POST",
                        data={
                            "domain": domain,
                            "intents": intents,
                            "packs": packs,
                        },
                    )
                if err:
                    st.error(f"Failed: {err}")
                elif payload and payload.get("success"):
                    data = payload.get("data", {})
                    st.success("✅ Graph built")
                    st.json(data.get("stats", {}))

                    # Show gaps
                    st.subheader("Detected Gaps")
                    gaps = data.get("gaps", [])
                    if not gaps:
                        st.info("No gaps detected")
                    else:
                        for g in gaps:
                            st.markdown(
                                f"- [{g.get('severity','low')}] {g.get('title')}"
                            )

                    # Simple node table fallback
                    import pandas as _pd

                    nodes = _pd.DataFrame(data.get("nodes", []))
                    st.dataframe(
                        nodes.head(50), use_container_width=True, hide_index=True
                    )

    with col2:
        st.subheader("Generate Playbook")
        intent_sel = st.text_input("Target Intent", placeholder="best X for Y")
        assistant = st.selectbox(
            "Assistant", ["chatgpt", "claude", "perplexity"], index=0
        )

        if st.button("Generate Playbook", type="secondary"):
            if not domain or not intent_sel:
                st.error("Enter domain and target intent")
            else:
                with st.spinner("Generating playbook (~5–10s)..."):
                    resp, err = make_api_request(
                        "/playbooks/generate",
                        method="POST",
                        data={
                            "domain": domain,
                            "intent": intent_sel,
                            "target_assistant": assistant,
                        },
                    )
                if err:
                    st.error(f"Failed: {err}")
                elif resp and resp.get("success"):
                    pb = resp.get("data", {})
                    st.success("✅ Playbook ready")

                    with st.expander("TL;DR"):
                        st.code(pb.get("tldr_html", ""), language="html")
                    with st.expander("FAQ"):
                        st.code(pb.get("faq_html", ""), language="html")
                    with st.expander("Organization JSON-LD"):
                        st.code(
                            json.dumps(pb.get("jsonld", {}), indent=2), language="json"
                        )
                    with st.expander("Acceptance Tests"):
                        st.code(pb.get("acceptance_tests_py", ""), language="python")

                    # Export buttons
                    st.subheader("Exports")
                    colx, coly = st.columns(2)
                    with colx:
                        md_payload, md_error = backend_client.export_playbook_md(pb)
                        if md_error:
                            st.error(f"Markdown export failed: {md_error}")
                        elif md_payload:
                            st.download_button(
                                "⬇️ Download MD",
                                data=md_payload["content"],
                                file_name=md_payload["filename"],
                                mime=md_payload["mime"],
                                key="playbook_md_download",
                            )
                    with coly:
                        docx_payload, docx_error = backend_client.export_playbook_docx(
                            pb
                        )
                        if docx_error:
                            st.error(f"DOCX export failed: {docx_error}")
                        elif docx_payload:
                            st.download_button(
                                "⬇️ Download DOCX",
                                data=docx_payload["content"],
                                file_name=docx_payload["filename"],
                                mime=docx_payload["mime"],
                                key="playbook_docx_download",
                            )
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for Answer Graph & Playbooks page (disabled)
    display_coming_soon_overlay()

# ==================== API KEYS PAGE ====================
elif page == "🔑 API Keys":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("🔑 API Key Management")

    tab1, tab2 = st.tabs(["Create New Key", "View Keys"])

    with tab1:
        st.subheader("Create New API Key")

        key_name = st.text_input(
            "Key Name",
            placeholder="My Project Key",
            help="A friendly name to identify this key",
        )

        quota = st.number_input(
            "Quota (requests per hour)",
            min_value=1,
            max_value=1000,
            value=10,
            help="How many requests per hour this key can make",
        )

        if st.button("🔑 Generate API Key", type="primary"):
            if not key_name:
                st.error("Please enter a key name")
            else:
                with st.spinner("Generating key..."):
                    data = {"name": key_name, "quota_per_hour": quota}

                    result, error = make_api_request(
                        "/keys/create", method="POST", data=data
                    )

                    if error:
                        st.error(f"Failed to create key: {error}")
                    elif result and result.get("success"):
                        key_data = result.get("data", {})
                        api_key = key_data.get("key", "")

                        st.success("✅ API key created successfully!")

                        st.code(api_key, language=None)

                        st.warning(
                            "⚠️ **IMPORTANT:** Copy this key now! You won't be able to see it again."
                        )

                        st.markdown(
                            f"""
                        **Key Details:**
                        - **Name:** {key_data.get('name')}
                        - **Quota:** {key_data.get('quota_per_hour')} requests/hour
                        - **Created:** {key_data.get('created_at', 'N/A')[:19]}
                        - **ID:** {key_data.get('id')}
                        """
                        )

                        # Save to session state
                        st.session_state.api_key = api_key

    with tab2:
        st.subheader("Your API Keys")

        if st.button("🔄 Refresh Keys"):
            with st.spinner("Loading keys..."):
                result, error = make_api_request("/keys/list")

                if error:
                    st.error(f"Failed to load keys: {error}")
                elif result and result.get("success"):
                    keys = result.get("data", {}).get("keys", [])

                    if not keys:
                        st.info(
                            "No API keys found. Create one in the 'Create New Key' tab."
                        )
                    else:
                        st.success(f"Found {len(keys)} key(s)")

                        for key in keys:
                            with st.expander(f"🔑 {key.get('name', 'Unnamed')}"):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**ID:** {key.get('id')}")
                                    st.markdown(f"**Name:** {key.get('name')}")
                                    st.markdown(
                                        f"**Key:** `{key.get('key', 'Hidden')}`"
                                    )

                                with col2:
                                    st.markdown(
                                        f"**Quota:** {key.get('quota_per_hour')} req/hr"
                                    )
                                    st.markdown(
                                        f"**Created:** {key.get('created_at', 'N/A')[:19]}"
                                    )
                                    st.markdown(
                                        f"**Last Used:** {key.get('last_used_at', 'Never')[:19] if key.get('last_used_at') else 'Never'}"
                                    )
                                    st.markdown(
                                        f"**Active:** {'✅ Yes' if key.get('is_active') else '❌ No'}"
                                    )
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for API Keys page (disabled)
    display_coming_soon_overlay()

# ==================== PLANS & PRICING PAGE ====================
elif page == "💰 Plans & Pricing":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("💰 Plans & Pricing")

    # Fetch plans
    with st.spinner("Loading plans..."):
        result, error = make_api_request("/plans")

    if error:
        st.error(f"Failed to load plans: {error}")
    elif result and result.get("success"):
        plans_data = result.get("data", {}).get("plans", {})

        # Display plans side by side
        cols = st.columns(len(plans_data))

        for idx, (plan_name, plan_details) in enumerate(plans_data.items()):
            with cols[idx]:
                # Plan card
                price = plan_details.get("price", 0)

                if price == 0:
                    price_display = "FREE"
                    color = "green"
                else:
                    price_display = f"${price}/mo"
                    color = "blue" if price < 100 else "purple"

                st.markdown(f"### {plan_name.title()}")
                st.markdown(
                    f"<h2 style='color: {color};'>{price_display}</h2>",
                    unsafe_allow_html=True,
                )

                st.markdown("**Features:**")
                st.markdown(f"- 📄 {plan_details.get('max_pages')} pages")
                st.markdown(
                    f"- 📦 Packs: {', '.join(plan_details.get('rule_packs', []))}"
                )

                features = plan_details.get("features", {})
                st.markdown(
                    f"- {'✅' if features.get('audit_history') else '❌'} Audit History"
                )
                st.markdown(
                    f"- {'✅' if features.get('fix_generation') else '❌'} Fix Generation"
                )
                st.markdown(
                    f"- {'✅' if features.get('citation_tracking') else '❌'} Citation Tracking"
                )
                st.markdown(
                    f"- {'✅' if features.get('api_access') else '❌'} API Access"
                )

                if price == 0:
                    st.button("✅ Current Plan", key=f"plan_{plan_name}", disabled=True)
                else:
                    st.button(
                        f"Upgrade to {plan_name.title()}", key=f"plan_{plan_name}"
                    )

        st.divider()

        # Comparison table
        st.subheader("📊 Feature Comparison")

        if st.button("View Detailed Comparison"):
            compare_result, compare_error = make_api_request("/plans/compare")

            if compare_error:
                st.error(f"Failed to load comparison: {compare_error}")
            elif compare_result and compare_result.get("success"):
                st.json(compare_result.get("data", {}))
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for Plans & Pricing page (disabled)
    display_coming_soon_overlay()

# ==================== ABOUT PAGE ====================
elif page == "ℹ️ About":
    st.markdown('<div class="blur-content">', unsafe_allow_html=True)
    st.header("ℹ️ About AI Visibility Audit Tool")

    st.markdown(
        """
    ## What is AI Visibility?

    AI Visibility refers to how discoverable and accurately represented your website, brand,
    or content is within AI-powered search engines and assistants like ChatGPT, Claude, Perplexity, and others.

    ## Features (P0 Complete)

    ### 🔍 P0-1: Audit Persistence & History
    - Save every audit for future reference
    - View complete audit history
    - Track improvements over time
    - Access past reports anytime

    ### 🤖 P0-2: AI Citation Tracking
    - Track ChatGPT brand mentions
    - Track Claude brand mentions
    - View citation statistics
    - Historical tracking data

    ### 🔧 P0-3: Auto-Fix Generation
    - AI-powered fix suggestions
    - Copy-paste ready code snippets
    - Automated acceptance tests
    - Context-aware recommendations

    ### 🔐 P0-4: API Keys & Rate Limiting
    - Secure key generation
    - Usage tracking
    - Rate limit enforcement
    - Key management dashboard

    ### 💰 P0-5: Plan Enforcement
    - **QuickScan (Free):** 3 pages, base pack, no auth
    - **Full ($49):** 12 pages, all packs, fixes, history
    - **Agency ($199):** 100 pages, all features, priority support

    ## Technology Stack

    - **Frontend:** Streamlit (Python)
    - **Backend:** Flask REST API
    - **Database:** SQLite (dev) / PostgreSQL (prod)
    - **AI Integration:** OpenAI GPT-3.5, Anthropic Claude
    - **Crawling:** Requests + BeautifulSoup
    - **Schema:** Extruct + JSON-LD parsing

    ## Version Information

    - **Version:** v0.1.0
    - **Release Date:** October 17, 2025
    - **Status:** Production Ready ✅
    - **Tests:** 39/39 Passing ✅
    - **GitHub:** [AP2-Labs/Vysalytica](https://github.com/AP2-Labs/Vysalytica)

    ## Contact & Support

    For questions, issues, or feature requests:
    - GitHub Issues
    - Documentation in repository

    ## License

    Proprietary - © 2025 AP2-Labs
    """
    )

    # System info
    with st.expander("🔧 System Information"):
        health, _ = make_api_request("/health")

        if health:
            st.success("✅ API Server: Online")
            st.code(json.dumps(health, indent=2), language="json")
        else:
            st.error("❌ API Server: Offline")
    st.markdown('</div>', unsafe_allow_html=True)
    # MODIFIED: Added "Coming Soon" overlay for About page (disabled)
    display_coming_soon_overlay()

# Footer
st.divider()
st.markdown(
    """
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>AI Visibility Audit Tool v0.1.0 | Built with Streamlit & Flask</p>
    <p>© 2025 AP2-Labs | All Rights Reserved</p>
</div>
""",
    unsafe_allow_html=True,
)
