import os
import requests
import streamlit as st

st.set_page_config(page_title="Vysalytica QuickScan", page_icon="🔎", layout="centered")

st.title("Vysalytica QuickScan 🔎")
st.write("Paste a public URL. We'll run an AI visibility QuickScan via our API and show key findings in ~10–30s.")

# API base (Render) - as requested, defaults to your Render URL
API_BASE = os.getenv("API_BASE", "https://vysalytica-api.onrender.com")

# Simple form
with st.form("quickscan_form"):
    url = st.text_input("Page URL", placeholder="https://example.com/blog/my-article")
    email = st.text_input("Email (optional for full report delivery)")
    submitted = st.form_submit_button("Run QuickScan")

if submitted:
    if not url or not url.startswith("http"):
        st.error("Please enter a valid URL starting with http or https.")
    else:
        with st.spinner("Running QuickScan..."):
            try:
                headers = {"Content-Type": "application/json"}
                payload = {
                    "url": url,
                    "plan": "quickscan"
                }
                resp = requests.post(
                    f"{API_BASE}/api/audit",
                    json=payload,
                    timeout=90,
                    headers=headers
                )
                if resp.status_code != 200:
                    st.error(f"API error: {resp.status_code} {resp.text[:300]}")
                else:
                    data = resp.json()
                    if not data.get("success"):
                        st.error(f"Scan failed: {data.get('error', 'Unknown error')}")
                    else:
                        st.success("QuickScan complete!")
                        result = data.get("data", {})

                        st.subheader("Summary")
                        st.write(f"**URL:** {result.get('url')}")
                        st.write(f"**Pages scanned:** {result.get('page_count')}")
                        st.write(f"**Plan:** {result.get('plan')}")
                        st.write(f"**Domain:** {result.get('domain')}")

                        # Score
                        scores = result.get("scores", {})
                        if "overall" in scores:
                            st.metric("AI Visibility Score", f"{int(scores['overall'])}/100")

                        # Key findings
                        findings = result.get("findings", [])
                        if findings:
                            st.subheader("Top Issues")
                            for i, finding in enumerate(findings[:5], start=1):
                                with st.expander(f"{i}. {finding.get('title', 'Issue')}", expanded=False):
                                    st.write(f"**Status:** {finding.get('status', '')}")
                                    st.write(f"**Category:** {finding.get('category', '')}")
                                    why = finding.get("why", "")
                                    if why:
                                        st.write(f"**Why:** {why}")
                                    fix_text = finding.get("fix", "")
                                    if fix_text:
                                        st.write(f"**Fix:** {fix_text}")
                                    fix_snippet = finding.get("fix_snippet")
                                    if fix_snippet:
                                        st.code(fix_snippet[:800] + ("..." if len(fix_snippet) > 800 else ""), language="html")

                        st.divider()
                        st.subheader("Upgrade for Full Report")
                        st.write(
                            "Unlock full fixes, downloadable report, and automated tests.\n\n"
                            "- **One-off Full Report:** $49\n"
                            "- **Agency Pilot** (5 clients): $199/mo (white-label)\n"
                        )
                        
                        # Optional: Add payment CTA button
                        if st.button("Get Full Report ($49)"):
                            st.info("Payment integration coming soon. We'll email you details at: " + (email if email else "your email"))

            except requests.exceptions.Timeout:
                st.error("The API request timed out. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
