"""pages/chat.py — Natural language to SQL using Claude API."""

import re
import json
import numpy as np
import pandas as pd
import streamlit as st
from google import genai

COLORS = dict(surface="#0f1117", border="#1a1f2e", accent="#00e5a0",
              accent2="#0091ff", accent3="#ff6b35", muted="#4a5568", text="#dde1ec")

FALLBACK_SCHEMA = """
customers(id, name, email, country, created_at, tier)
orders(id, customer_id, product_id, quantity, total_amount, status, created_at)
products(id, name, category, price, stock_qty, supplier_id)
marketing_leads(id, source, campaign, converted, cost, created_at)
revenue_monthly(year, month, revenue, orders, new_customers)
"""

QUICK = [
    "Top 10 customers by revenue",
    "Monthly revenue trend",
    "Best marketing channels",
    "Products with low stock",
    "Conversion rate by campaign",
    "Orders by status breakdown",
]


def build_schema_str() -> str:
    df = st.session_state.clean_df if st.session_state.clean_df is not None else st.session_state.raw_df
    if df is not None:
        cols = ", ".join(df.columns.tolist())
        return f"uploaded_dataset({cols})"
    return FALLBACK_SCHEMA


def call_gemini(question: str) -> dict:
    try:
        client = genai.Client(api_key=st.session_state.get("api_key", "").strip())
        schema = build_schema_str()
        prompt = f"""You are an expert PostgreSQL data analyst. Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "sql": "SELECT ...",
  "explanation": "one sentence description",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "chart_type": "bar|line|pie|area|none"
}}

Schema:
{schema}

Rules: proper PostgreSQL syntax, meaningful aliases, ORDER BY + LIMIT where sensible, CTEs for complex queries.

Question: {question}"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"sql": f"-- Parse error for: {question}", "explanation": "Could not parse response.",
                "insights": [], "chart_type": "none"}
    except Exception as e:
        return {"sql": "-- Error", "explanation": str(e), "insights": [], "chart_type": "none"}


def _process(question: str):
    if not st.session_state.api_key:
        st.error("Set your Google Gemini API key in the sidebar first.")
        return
    st.session_state.chat_messages.append({"role": "user", "text": question})
    with st.spinner("Generating SQL…"):
        res = call_gemini(question)
    st.session_state.msg_counter += 1
    st.session_state.chat_messages.append({
        "role": "ai", "type": "result", "id": st.session_state.msg_counter,
        **res
    })


def render():
    st.markdown('<div class="sec-hdr">◎ AI Query — Natural Language → PostgreSQL</div>',
                unsafe_allow_html=True)

    if not st.session_state.chat_messages:
        st.session_state.chat_messages = [{
            "role": "ai", "type": "welcome",
            "text": "Hey! Ask me anything about your data — I'll write the SQL, explain it, and surface insights. Upload a dataset to query it directly, or use the demo schema."
        }]

    # Schema info
    df = st.session_state.clean_df if st.session_state.clean_df is not None else st.session_state.raw_df
    if df is not None:
        cols_preview = ", ".join(df.columns[:8].tolist())
        if len(df.columns) > 8: cols_preview += f" + {len(df.columns)-8} more"
        st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#4a5568;margin-bottom:10px">📂 Querying: uploaded_dataset({cols_preview})</div>', unsafe_allow_html=True)

    # Quick prompts
    chip_cols = st.columns(3)
    for i, p in enumerate(QUICK):
        with chip_cols[i % 3]:
            if st.button(p, key=f"qp_{i}", use_container_width=True):
                _process(p)
                st.rerun()

    st.markdown("---")

    # Messages
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f"""<div style="background:rgba(0,145,255,0.07);border:1px solid rgba(0,145,255,0.2);
                border-radius:10px;padding:12px 15px;margin-bottom:10px;text-align:right;font-size:14px">
                👤 &nbsp;{msg['text']}</div>""", unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f'<div style="background:#0f1117;border:1px solid #1a1f2e;border-radius:10px;padding:14px 16px;margin-bottom:10px">', unsafe_allow_html=True)
                if msg.get("type") == "welcome":
                    st.markdown(f'<span style="font-size:14px;line-height:1.7">{msg["text"]}</span>', unsafe_allow_html=True)
                elif msg.get("type") == "result":
                    if msg.get("explanation"):
                        st.markdown(f'<p style="font-size:13.5px;margin-bottom:10px">{msg["explanation"]}</p>', unsafe_allow_html=True)
                    if msg.get("sql"):
                        col_hdr, col_copy = st.columns([5,1])
                        with col_hdr:
                            st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:#4a5568;letter-spacing:1px">⬡ POSTGRESQL</span>', unsafe_allow_html=True)
                        with col_copy:
                            if st.button("copy", key=f"cp_{msg.get('id','')}", help="Copy SQL"):
                                st.toast("Copied!")
                        st.code(msg["sql"], language="sql")
                    if msg.get("insights"):
                        html = '<div style="background:rgba(0,229,160,0.04);border:1px solid rgba(0,229,160,0.15);border-radius:8px;padding:12px 14px;margin-top:8px">'
                        html += '<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#00e5a0;letter-spacing:1px;margin-bottom:6px">▸ INSIGHTS</div>'
                        for ins in msg["insights"]:
                            html += f'<div style="font-size:12.5px;margin-bottom:5px">◆ &nbsp;{ins}</div>'
                        html += '</div>'
                        st.markdown(html, unsafe_allow_html=True)

                        # If uploaded dataset, run query against it
                        df = st.session_state.clean_df if st.session_state.clean_df is not None else st.session_state.raw_df
                        if df is not None and msg.get("sql") and "uploaded_dataset" in msg["sql"]:
                            try:
                                import duckdb # type: ignore
                                sql = msg["sql"].replace("uploaded_dataset", "df")
                                result = duckdb.sql(sql).df()
                                st.markdown("##### Query Results")
                                st.dataframe(result, use_container_width=True, height=320)
                            except Exception as e:
                                st.caption(f"Live query unavailable: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

    # Input
    col_in, col_send = st.columns([8, 1])
    with col_in:
        user_input = st.text_area("", placeholder="e.g. 'Show me revenue by category for the last quarter'",
                                   height=72, label_visibility="collapsed", key="q_input")
    with col_send:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↑ Send", type="primary", use_container_width=True):
            if user_input.strip():
                _process(user_input.strip())
                st.rerun()