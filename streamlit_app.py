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
# TAB 1: AUDIT TOOL
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
                        else:
                            st.error(data.get("error", "Unknown error"))
                    else:
                        st.error(f"API Error: {resp.status_code} - {resp.text[:300]}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================
# TAB 2: CITATION TRACKER
# ============================================
with tab2:
    st.header("AI Citation Tracker")
    st.write("Track how often your brand is cited by ChatGPT and Claude")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Track New Citations")
        with st.form("citation_form"):
            brand = st.text_input("Brand Name", placeholder="Asana")
            intent = st.text_input("Search Intent", placeholder="best project management tools")
            assistants = st.multiselect("AI Assistants", ["chatgpt", "claude"], default=["chatgpt", "claude"])
            track_btn = st.form_submit_button("Track Citations")
        
        if track_btn:
            if brand and intent:
                with st.spinner("Querying AI assistants..."):
                    try:
                        payload = {"brand": brand, "intent": intent, "assistants": assistants}
                        resp = requests.post(f"{API_BASE}/api/citations/track", json=payload, timeout=120)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                results = data["data"]["results"]
                                summary = data["data"]["summary"]
                                
                                st.success(f"Citation Rate: {summary['rate']}% ({summary['cited']}/{summary['total']})")
                                
                                for r in results:
                                    cited = "✅ Cited" if r.get("cited") else "❌ Not Cited"
                                    with st.expander(f"{r['assistant']} - {cited}"):
                                        st.write(r.get("response", "")[:500])
                            else:
                                st.error(data.get("error"))
                        else:
                            st.error(f"Error: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with col2:
        st.subheader("Citation Stats")
        stats_brand = st.text_input("Brand Name (for stats)", placeholder="Asana")
        if st.button("Get Stats"):
            if stats_brand:
                try:
                    resp = requests.get(f"{API_BASE}/api/citations/stats", params={"brand": stats_brand}, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            stats = data["data"]
                            st.metric("Overall Citation Rate", f"{stats.get('overall_rate', 0)}%")
                            st.metric("Total Queries", stats.get('total_queries', 0))
                            st.write(f"**ChatGPT Rate:** {stats.get('chatgpt_rate', 0)}%")
                            st.write(f"**Claude Rate:** {stats.get('claude_rate', 0)}%")
                        else:
                            st.error(data.get("error"))
                    else:
                        st.error(f"Error: {resp.status_code}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================
# TAB 3: ANSWER GRAPH
# ============================================
with tab3:
    st.header("Answer Graph Builder")
    st.write("Map how AI assistants answer key intents for your domain")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Build Answer Graph")
        with st.form("answer_graph_form"):
            domain = st.text_input("Domain", placeholder="example.com")
            intents_input = st.text_area("Intents (one per line)", placeholder="best project management\nproject management for teams")
            ag_packs = st.multiselect("Packs", ["base", "ecomm", "docs"], default=["base"])
            build_btn = st.form_submit_button("Build Graph")
        
        if build_btn:
            if domain and intents_input:
                intents = [i.strip() for i in intents_input.split("\n") if i.strip()]
                with st.spinner("Building answer graph..."):
                    try:
                        payload = {"domain": domain, "intents": intents, "packs": ag_packs}
                        resp = requests.post(f"{API_BASE}/api/answer_graph/build", json=payload, timeout=120)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                result = data["data"]
                                st.success("Answer graph built!")
                                st.metric("Priority Score", result.get("priority_score", 0))
                                st.json(result)
                            else:
                                st.error(data.get("error"))
                        else:
                            st.error(f"Error: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with col2:
        st.subheader("View Answer Graphs")
        view_domain = st.text_input("Domain (to view)", placeholder="example.com")
        if st.button("Load Graphs"):
            if view_domain:
                try:
                    resp = requests.get(f"{API_BASE}/api/answer_graph/", params={"domain": view_domain, "limit": 5}, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            graphs = data["data"]
                            st.write(f"Found {len(graphs)} graph(s)")
                            for g in graphs:
                                with st.expander(f"Graph {g.get('id')} - {g.get('created_at', '')}"):
                                    st.json(g)
                        else:
                            st.error(data.get("error"))
                    else:
                        st.error(f"Error: {resp.status_code}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================
# TAB 4: PLAYBOOKS
# ============================================
with tab4:
    st.header("Playbook Generator")
    st.write("Generate actionable playbooks to improve AI visibility for specific intents")
    
    with st.form("playbook_form"):
        pb_domain = st.text_input("Domain", placeholder="example.com")
        pb_intent = st.text_input("Intent", placeholder="best project management tools")
        pb_assistant = st.selectbox("Target Assistant", ["chatgpt", "claude"])
        pb_btn = st.form_submit_button("Generate Playbook")
    
    if pb_btn:
        if pb_domain and pb_intent:
            with st.spinner("Generating playbook..."):
                try:
                    payload = {"domain": pb_domain, "intent": pb_intent, "target_assistant": pb_assistant}
                    resp = requests.post(f"{API_BASE}/api/playbooks/generate", json=payload, timeout=120)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            playbook = data["data"]
                            st.success("Playbook generated!")
                            
                            st.subheader(f"Playbook: {playbook.get('intent', '')}")
                            st.write(f"**Target:** {playbook.get('target_assistant', '')}")
                            st.write(f"**Priority:** {playbook.get('priority', '')}")
                            
                            fixes = playbook.get("fixes", [])
                            st.write(f"**{len(fixes)} Fixes:**")
                            for i, fix in enumerate(fixes, 1):
                                with st.expander(f"{i}. {fix.get('title', 'Fix')}"):
                                    st.write(f"**Why:** {fix.get('why', '')}")
                                    st.write(f"**Language:** {fix.get('language', '')}")
                                    if fix.get('snippet'):
                                        st.code(fix['snippet'], language=fix.get('language', 'html'))
                            
                            # Download options
                            st.subheader("Download Playbook")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Download as Markdown"):
                                    try:
                                        dl_resp = requests.post(f"{API_BASE}/api/report/playbook_md", json={"playbook": playbook}, timeout=60)
                                        if dl_resp.status_code == 200:
                                            st.download_button("📥 Download MD", dl_resp.content, f"{pb_domain}_playbook.md", "text/markdown")
                                    except Exception as e:
                                        st.error(f"Download error: {e}")
                            with col2:
                                if st.button("Download as DOCX"):
                                    try:
                                        dl_resp = requests.post(f"{API_BASE}/api/report/playbook_docx", json={"playbook": playbook}, timeout=60)
                                        if dl_resp.status_code == 200:
                                            st.download_button("📥 Download DOCX", dl_resp.content, f"{pb_domain}_playbook.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                                    except Exception as e:
                                        st.error(f"Download error: {e}")
                        else:
                            st.error(data.get("error"))
                    else:
                        st.error(f"Error: {resp.status_code}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================
# TAB 5: REPORTS & HISTORY
# ============================================
with tab5:
    st.header("Audit History & Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Audit History")
        history_domain = st.text_input("Filter by domain (optional)")
        history_limit = st.slider("Limit", 1, 20, 10)
        
        if st.button("Load History"):
            try:
                params = {"limit": history_limit}
                if history_domain:
                    params["domain"] = history_domain
                
                resp = requests.get(f"{API_BASE}/api/audit/history", params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        audits = data["data"]
                        st.write(f"Found {len(audits)} audit(s)")
                        for audit in audits:
                            with st.expander(f"Audit #{audit.get('id')} - {audit.get('domain')} - Score: {audit.get('overall_score')}"):
                                st.write(f"**URL:** {audit.get('url')}")
                                st.write(f"**Pages:** {audit.get('page_count')}")
                                st.write(f"**Date:** {audit.get('created_at')}")
                                st.write(f"**Packs:** {', '.join(audit.get('packs', []))}")
                    else:
                        st.error(data.get("error"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("Get Audit Details")
        audit_id = st.number_input("Audit ID", min_value=1, step=1)
        
        if st.button("Load Audit"):
            try:
                resp = requests.get(f"{API_BASE}/api/audit/{audit_id}", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        audit = data["data"]
                        st.json(audit)
                    else:
                        st.error(data.get("error"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================
# TAB 6: API KEYS & PLANS
# ============================================
with tab6:
    st.header("API Keys & Plans")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create API Key")
        with st.form("api_key_form"):
            key_name = st.text_input("Key Name (optional)", placeholder="My App Key")
            quota = st.number_input("Quota per hour", min_value=1, max_value=1000, value=10)
            create_key_btn = st.form_submit_button("Create Key")
        
        if create_key_btn:
            try:
                payload = {"name": key_name, "quota_per_hour": quota}
                resp = requests.post(f"{API_BASE}/api/keys/create", json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        key_data = data["data"]
                        st.success("API Key created!")
                        st.code(key_data.get("key"), language="text")
                        st.caption("⚠️ Save this key - it won't be shown again")
                    else:
                        st.error(data.get("error"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.subheader("List API Keys")
        if st.button("Load Keys"):
            try:
                resp = requests.get(f"{API_BASE}/api/keys/list", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        keys = data["data"]
                        for key in keys:
                            st.write(f"**{key.get('name', 'Unnamed')}** - {key.get('key')} - Active: {key.get('is_active')}")
                    else:
                        st.error(data.get("error"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("Available Plans")
        if st.button("Load Plans"):
            try:
                resp = requests.get(f"{API_BASE}/api/plans", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        plans = data["data"]
                        for plan in plans:
                            with st.expander(f"{plan.get('name')} - ${plan.get('price')}"):
                                st.json(plan)
                    else:
                        st.error(data.get("error"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.subheader("Compare Plans")
        if st.button("Show Comparison"):
            try:
                resp = requests.get(f"{API_BASE}/api/plans/compare", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        comparison = data["data"]
                        st.json(comparison)
                    else:
                        st.error(data.get("error"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
