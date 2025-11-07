import os
import requests
import streamlit as st

st.set_page_config(page_title="Vysalytica QuickScan", page_icon="🔎", layout="centered")

st.title("Vysalytica QuickScan 🔎")
st.write("Paste a public URL. We’ll run an AI visibility QuickScan via our API and show key findings in ~10–30s.")

# API base (Render)
#API_BASE = os.getenv("API_BASE", "https://vysalytica-api.onrender.com")  # fixed per your instruction
with st.spinner("Running QuickScan..."):
    try:
        # Try common endpoint patterns in order
        headers = {"Content-Type": "application/json"}
        payload = {"url": url, "email": email or None}

        endpoints = [
            ("POST", f"{API_BASE}/api/quickscan"),
            ("POST", f"{API_BASE}/quickscan"),
            ("GET",  f"{API_BASE}/api/quickscan"),
            ("GET",  f"{API_BASE}/quickscan"),
        ]

        data = None
        last_err = None
        for method, ep in endpoints:
            try:
                if method == "POST":
                    resp = requests.post(ep, json=payload, timeout=90, headers=headers)
                else:
                    resp = requests.get(ep, params=payload, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    break
                else:
                    last_err = f"{method} {ep} -> {resp.status_code} {resp.text[:200]}"
            except Exception as inner_e:
                last_err = f"{method} {ep} -> {inner_e}"

        if data is None:
            raise RuntimeError(f"No working endpoint. Last error: {last_err}")

        st.success("QuickScan complete!")

        # Summary
        st.subheader("Summary")
        st.write(data.get("summary", "No summary returned."))

        # Score
        score = data.get("score")
        if isinstance(score, (int, float)):
            st.metric("AI Visibility Score", f"{int(score)}/100")

        # Issues
        issues = data.get("issues", [])
        if issues:
            st.subheader("Top Issues")
            for i, issue in enumerate(issues[:5], start=1):
                title = issue.get("title", f"Issue {i}")
                with st.expander(f"{i}. {title}", expanded=False):
                    impact = issue.get("impact")
                    if impact:
                        st.write(f"Impact: {impact}")
                    desc = issue.get("description", "")
                    if desc:
                        st.write(desc)
                    fix = issue.get("fix_snippet")
                    if fix:
                        snippet = fix if isinstance(fix, str) else str(fix)
                        st.code(snippet[:800] + ("..." if len(snippet) > 800 else ""), language="html")

        # CTA / upsell
        st.divider()
        st.subheader("Upgrade for Full Report")
        st.write(
            "Unlock full fixes, downloadable report, and automated tests.\n"
            "- One-off Full Report: $49\n"
            "- Agency Pilot (5 clients): $199/mo (white-label)\n"
        )
        if st.button("Get Full Report ($49)"):
            try:
                pay_endpoints = [
                    ("POST", f"{API_BASE}/api/checkout/full_report"),
                    ("POST", f"{API_BASE}/checkout/full_report"),
                ]
                link = None
                for m, pep in pay_endpoints:
                    try:
                        pay_resp = requests.post(pep, json={"url": url, "email": email or None}, timeout=60)
                        if pay_resp.status_code == 200:
                            link = pay_resp.json().get("checkout_url")
                            if link:
                                break
                    except Exception:
                        continue
                if link:
                    st.markdown(f"[Complete purchase here]({link})")
                else:
                    st.info("We’ll email you payment details shortly.")
            except Exception as e:
                st.error(f"Payment init failed: {e}")

        hint = data.get("upgrade_hint")
        if hint:
            st.caption(hint)

    except Exception as e:
        st.error(str(e))

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
                # Adjust to your actual API contract if needed
                resp = requests.get(f"{API_BASE}/quickscan", params={"url": url, "email": email}, timeout=90)
                resp.raise_for_status()
                data = resp.json()

                st.success("QuickScan complete!")

                # Summary
                st.subheader("Summary")
                st.write(data.get("summary", "No summary returned."))

                # Score
                score = data.get("score")
                if isinstance(score, (int, float)):
                    st.metric("AI Visibility Score", f"{int(score)}/100" if isinstance(score, (int, float)) else str(score))

                # Issues
                issues = data.get("issues", [])
                if issues:
                    st.subheader("Top Issues")
                    for i, issue in enumerate(issues[:5], start=1):
                        title = issue.get("title", f"Issue {i}")
                        with st.expander(f"{i}. {title}", expanded=False):
                            impact = issue.get("impact")
                            if impact:
                                st.write(f"Impact: {impact}")
                            desc = issue.get("description", "")
                            if desc:
                                st.write(desc)
                            fix = issue.get("fix_snippet")
                            if fix:
                                snippet = fix if isinstance(fix, str) else str(fix)
                                st.code(snippet[:800] + ("..." if len(snippet) > 800 else ""), language="html")

                # CTA / upsell
                st.divider()
                st.subheader("Upgrade for Full Report")
                st.write(
                    "Unlock full fixes, downloadable report, and automated tests.\n"
                    "- One-off Full Report: $49\n"
                    "- Agency Pilot (5 clients): $199/mo (white-label)\n"
                )
                if st.button("Get Full Report ($49)"):
                    try:
                        pay = requests.post(
                            f"{API_BASE}/checkout/full_report",
                            json={"url": url, "email": email},
                            timeout=60
                        )
                        pay.raise_for_status()
                        link = pay.json().get("checkout_url")
                        if link:
                            st.markdown(f"[Complete purchase here]({link})")
                        else:
                            st.info("We’ll email you payment details shortly.")
                    except Exception as e:
                        st.error(f"Payment init failed: {e}")

                hint = data.get("upgrade_hint")
                if hint:
                    st.caption(hint)

            except requests.exceptions.HTTPError as e:
                body = ""
                try:
                    body = resp.text[:300]
                except Exception:
                    pass
                st.error(f"API error: {e} | {body}")
            except requests.exceptions.Timeout:
                st.error("The API timed out. Please try again.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
