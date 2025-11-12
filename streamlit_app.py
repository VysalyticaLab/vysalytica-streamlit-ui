import os
import requests
import streamlit as st
import json

st.set_page_config(page_title="Vysalytica Platform", page_icon="🔎", layout="wide")

# API base
API_BASE = os.getenv("API_BASE", "https://vysalytica-api.onrender.com")

st.title("🔎 Vysalytica - AI Visibility Platform")
st.caption("Test all features for free")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Audit Tool", 
    "📊 Citation Tracker", 
    "🗺️ Answer Graph", 
    "📋 Playbooks", 
    "📄 Reports & History",
    "🔑 API Keys & Plans"
])

# ============================================
# TAB 1: AUDIT TOOL (FULLY FUNCTIONAL - NO CHANGES)
# ============================================
with tab1:
    st.header("AI Visibility Audit")
    
    with st.form("audit_form"):
        url = st.text_input("Website URL", placeholder="https://example.com")
        plan = st.selectbox("Plan", ["quickscan", "full", "agency"])
        packs = st.multiselect("Rule Packs", ["base", "ecomm", "docs"], default=["base"])
        api_key = st.text_input("API Key (required for Full/Agency)", type="password")
        submitted = st.form_submit_button("Run Audit")
    
    if submitted:
        if not url or not url.startswith("http"):
            st.error("Please enter a valid URL")
        else:
            with st.spinner(f"Running {plan} audit..."):
                try:
                    headers = {"Content-Type": "application/json"}
                    if api_key:
                        headers["X-API-Key"] = api_key
                    
                    payload = {"url": url, "plan": plan, "packs": packs}
                    resp = requests.post(f"{API_BASE}/api/audit", json=payload, headers=headers, timeout=120)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            result = data["data"]
                            
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Overall Score", f"{int(result.get('scores', {}).get('overall', 0))}/100")
                            col2.metric("Pages Scanned", result.get("page_count", 0))
                            col3.metric("Audit ID", result.get("audit_id", "N/A"))
                            
                            st.subheader("Findings")
                            findings = result.get("findings", [])
                            for i, f in enumerate(findings[:10], 1):
                                with st.expander(f"{i}. {f.get('title', 'Issue')} - {f.get('status', '')}"):
                                    st.write(f"**Category:** {f.get('category', '')}")
                                    st.write(f"**Why:** {f.get('why', '')}")
                                    st.write(f"**Fix:** {f.get('fix', '')}")
                                    if f.get('fix_snippet'):
                                        st.code(f['fix_snippet'][:500], language="html")
                                    if f.get('evidence'):
                                        st.write(f"**Evidence:** {f.get('evidence')}")
                        else:
                            st.error(data.get("error", "Unknown error"))
                    else:
                        st.error(f"API Error: {resp.status_code} - {resp.text[:300]}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================
# TAB 2: CITATION TRACKER (HIDDEN)
# ============================================
with tab2:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ============================================
# TAB 3: ANSWER GRAPH (HIDDEN)
# ============================================
with tab3:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ============================================
# TAB 4: PLAYBOOKS (HIDDEN)
# ============================================
with tab4:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ============================================
# TAB 5: REPORTS & HISTORY (HIDDEN)
# ============================================
with tab5:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ============================================
# TAB 6: API KEYS & PLANS (HIDDEN)
# ============================================
with tab6:
    st.markdown("""
        <style>
        [data-testid="stVerticalBlock"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
