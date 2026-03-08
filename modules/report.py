"""pages/report.py — Auto-generate business reports from uploaded or demo data."""

from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from google import genai
from utils.display import safe_dataframe
from datetime import datetime


def _summarise_df(df: pd.DataFrame) -> str:
    """Build a textual summary of the dataframe for Claude."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    lines = [
        f"Dataset: {df.shape[0]:,} rows × {df.shape[1]} columns",
        f"Numeric columns: {', '.join(num_cols[:10])}",
        f"Categorical columns: {', '.join(cat_cols[:10])}",
        f"Missing values: {df.isna().sum().sum():,} ({df.isna().sum().sum()/df.size*100:.1f}%)",
    ]
    if num_cols:
        stats = df[num_cols[:6]].describe().round(2)
        lines.append("Key statistics:\n" + stats.to_string())
    if cat_cols:
        for c in cat_cols[:3]:
            top = df[c].value_counts().head(5)
            lines.append(f"Top values in '{c}': " + ", ".join(f"{k}({v})" for k,v in top.items()))
    return "\n".join(lines)


def generate_report(prompt: str, df: pd.DataFrame | None) -> str:
    try:
        api_key = st.session_state.get("api_key", "").strip()
        client  = genai.Client(api_key=api_key)
        context = _summarise_df(df) if df is not None else \
            "Business: SaaS company, $4.68M annual revenue, 19,939 orders, 1,593 new customers, top categories: Enterprise Software (42%), Cloud Services (28%)."

        full_prompt = f"""You are a senior data analyst writing executive-grade business reports.
Write in clear, data-driven, professional markdown. Use bold for key numbers.
Be specific and quantitative. Structure with ## headings. Bullet key findings.

Data context:
{context}

Write a detailed report section on: {prompt}"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
        )
        return response.text
    except Exception as e:
        return f"Error generating report: {e}"


STATIC_REPORT = {
    "sections": [
        {"heading": "Executive Summary",
         "content": "FY2024 closed with total revenue of **$4.68M**, an **18.4% YoY increase**. Order volume reached **19,939** transactions. Customer acquisition grew **9.7% YoY** with **1,593** net new customers. December was the strongest month on record at **$497K** revenue.",
         "bullets": []},
        {"heading": "Revenue Drivers",
         "content": "",
         "bullets": [
             "Enterprise Software — top category at **42%** of sales ($1.97M)",
             "Cloud Services grew **31% YoY**, now 28% of the revenue mix",
             "AOV declined **-2.3%** due to higher small-ticket order volume in H2",
             "Q4 contributed **36%** of annual revenue — consistent with prior seasonality",
         ]},
        {"heading": "Customer & Marketing",
         "content": "Email marketing delivered the best ROI at **$3.87 CAC**, converting **22%** of leads. Paid Search CPC rose **14%** — A/B test ad copy recommended in Q1.",
         "bullets": [
             "Top 10 customers = **28% of revenue** — concentration risk to monitor",
             "USA + Germany + Japan = **61%** of enterprise revenue",
             "Referral channel: **28% conversion rate** — highest, yet under-invested",
         ]},
        {"heading": "Recommendations",
         "content": "",
         "bullets": [
             "**Scale referral program** — best CAC, highest conversion. Structured incentive could 3× volume.",
             "**Upsell Cloud Services** — target existing Enterprise customers with migration packages.",
             "**Diversify customer base** — 28% concentration in top 10 is a risk threshold.",
             "**Reallocate SEM budget** — shift 20% of Paid Search spend to SEO content.",
         ]},
    ]
}


def render():
    st.markdown('<div class="sec-hdr">≡ Report — AI-Powered Business Summary</div>', unsafe_allow_html=True)
    _c = st.session_state.get("clean_df")
    _r = st.session_state.get("raw_df")
    df = _c if _c is not None else _r
    using_upload = df is not None

    # Header
    hc1, hc2 = st.columns([3, 1])
    with hc1:
        title = "Dataset Analysis Report" if using_upload else "Business Performance Summary"
        st.markdown(f"""
        <div style="font-size:22px;font-weight:800;letter-spacing:-0.5px;margin-bottom:4px">{title}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#4a5568">
            {'Uploaded dataset · ' if using_upload else ''}Auto-generated · {datetime.now().strftime('%B %d, %Y')}
        </div>""", unsafe_allow_html=True)
    with hc2:
        st.markdown("<br>", unsafe_allow_html=True)
        # Build export content
        lines = [title, "="*50, f"Generated: {datetime.now().strftime('%B %d, %Y')}", ""]
        if not using_upload:
            for sec in STATIC_REPORT["sections"]:
                lines += [sec["heading"].upper(), "-"*len(sec["heading"])]
                if sec["content"]: lines += [sec["content"].replace("**",""), ""]
                for b in sec["bullets"]: lines += [f"  • {b.replace('**','')}"]
                lines.append("")
        st.download_button("⬇ Export .txt",
                           data="\n".join(lines).encode(),
                           file_name="report.txt", mime="text/plain",
                           use_container_width=True)

    st.markdown("---")

    # Dataset summary at top if uploaded
    if using_upload:
        st.markdown("#### Dataset Overview")
        n1, n2, n3, n4 = st.columns(4)
        n1.metric("Rows", f"{df.shape[0]:,}")
        n2.metric("Columns", df.shape[1])
        n3.metric("Numeric Cols", len(df.select_dtypes(include=[np.number]).columns))
        n4.metric("Nulls Remaining", f"{df.isna().sum().sum():,}")

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            st.markdown("##### Key Statistics")
            safe_dataframe(df[num_cols[:8]].describe().round(3).reset_index(), max_rows=20, height=280)
        st.markdown("---")

    # Static report (demo)
    if not using_upload:
        for sec in STATIC_REPORT["sections"]:
            st.markdown(f"""<div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                color:#00e5a0;letter-spacing:1.5px;text-transform:uppercase;
                padding-bottom:6px;border-bottom:1px solid #1a1f2e;margin-bottom:10px">
                {sec['heading']}</div>""", unsafe_allow_html=True)
            if sec["content"]:
                st.markdown(f'<p style="font-size:13.5px;line-height:1.8;margin-bottom:8px">{sec["content"]}</p>',
                            unsafe_allow_html=True)
            for b in sec["bullets"]:
                st.markdown(f'<div style="font-size:13px;line-height:1.8;padding-left:12px;margin-bottom:4px">◆ &nbsp;{b}</div>',
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""<div style="background:rgba(0,229,160,0.04);border:1px solid rgba(0,229,160,0.15);
            border-radius:8px;padding:12px 16px;">
            <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#00e5a0;letter-spacing:1px;margin-bottom:5px">▸ DATA SOURCES</div>
            <div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#4a5568;line-height:1.8">
            customers · orders · products · marketing_leads · revenue_monthly<br>
            PostgreSQL · ~84,200 rows · Est. query time: ~340ms
            </div></div>""", unsafe_allow_html=True)

    # AI Report Generator
    st.markdown("---")
    st.markdown("#### ✦ AI Report Section Generator")
    st.markdown('<div style="font-size:12.5px;color:#4a5568;margin-bottom:12px">Generate a custom analysis section using Claude. Works best with an uploaded dataset.</div>', unsafe_allow_html=True)

    if not st.session_state.get("api_key", "").strip():
        st.info("Set your Google Gemini API key in the sidebar to enable AI report generation.")
        return

    topic_presets = [
        "Custom…",
        "Executive summary and key KPIs",
        "Top performing segments / categories",
        "Anomalies and data quality findings",
        "Trend analysis and growth patterns",
        "Customer segmentation insights",
        "Risk areas and recommendations",
    ]
    preset = st.selectbox("Choose topic", topic_presets, label_visibility="collapsed")
    custom_topic = preset if preset != "Custom…" else st.text_input(
        "Custom topic", placeholder="e.g. 'Churn risk analysis'", label_visibility="collapsed")

    if st.button("✦ Generate Report Section", type="primary"):
        if custom_topic and custom_topic != "Custom…":
            with st.spinner("Generating…"):
                result = generate_report(custom_topic, df)
            st.markdown("""<div style="background:#0f1117;border:1px solid rgba(0,229,160,0.2);
                border-radius:10px;padding:20px;margin-top:12px">""", unsafe_allow_html=True)
            st.markdown(result)
            st.markdown("</div>", unsafe_allow_html=True)
            # Download this section
            st.download_button("⬇ Download section",
                               data=result.encode(), file_name="report_section.md",
                               mime="text/markdown")