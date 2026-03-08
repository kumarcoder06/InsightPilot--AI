"""modules/data_cleaner.py — Upload dirty data, clean it like a senior analyst."""

import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from utils.display import safe_dataframe

from utils.cleaner_engine import clean_dataframe, CleaningStep
from utils.display import safe_dataframe

COLORS = dict(
    bg="#090b0f", surface="#0f1117", border="#1a1f2e",
    accent="#00e5a0", accent2="#0091ff", accent3="#ff6b35",
    warn="#f5c542", purple="#a855f7", muted="#4a5568", text="#dde1ec",
)
LAYOUT = dict(
    paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
    font=dict(family="JetBrains Mono, monospace", color=COLORS["muted"], size=11),
    margin=dict(l=8, r=8, t=28, b=8),
    hoverlabel=dict(bgcolor=COLORS["surface"], bordercolor=COLORS["border"],
                    font_family="JetBrains Mono"),
)
SEV_COLORS = {"info":"#0091ff","warning":"#f5c542","fixed":"#00e5a0","removed":"#ff6b35"}
SEV_ICONS  = {"info":"ℹ","warning":"⚠","fixed":"✓","removed":"✕"}


def _step_badge(step: CleaningStep):
    import html as _html
    color     = SEV_COLORS.get(step.severity, COLORS["muted"])
    icon      = SEV_ICONS.get(step.severity, "·")
    cat_color = {
        "Missing Values":"#0091ff","Duplicates":"#ff6b35","Data Types":"#a855f7",
        "Outliers":"#f5c542","Column Names":"#00e5a0","String Cleaning":"#00e5a0",
        "Categorical":"#00e5a0","Empty Data":"#ff6b35"
    }.get(step.category, COLORS["muted"])

    safe_action = _html.escape(str(step.action))
    safe_detail = _html.escape(str(step.detail))
    safe_col    = _html.escape(str(step.column)) if step.column else ""

    # build col span outside f-string to avoid nested quote conflict
    col_span = (
        f'<span style="font-family:JetBrains Mono,monospace;font-size:9px;'
        f'color:{COLORS["muted"]}"> &middot; {safe_col}</span>'
        if safe_col else ""
    )

    html_block = (
        f'<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 12px;'        f'border-left:3px solid {color};background:rgba(0,0,0,0.2);'        f'border-radius:0 7px 7px 0;margin-bottom:6px">'        f'<span style="font-size:13px;color:{color};flex-shrink:0">{icon}</span>'        f'<div style="flex:1">'        f'<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:{cat_color};'        f'letter-spacing:0.5px;text-transform:uppercase">{step.category}</span>'        + col_span +
        f'<div style="font-size:12.5px;color:{COLORS["text"]};margin-top:2px">{safe_action}</div>'        f'<div style="font-size:11px;color:{COLORS["muted"]};margin-top:1px">{safe_detail}</div>'        f'</div></div>'
    )
    st.markdown(html_block, unsafe_allow_html=True)


def render():
    st.markdown('<div class="sec-hdr">🧹 Data Cleaner — Upload · Analyse · Clean · Load</div>',
                unsafe_allow_html=True)

    # ── Step 1: Upload ────────────────────────────────────────────────────────
    st.markdown("#### Step 1 — Upload your dataset")
    uploaded = st.file_uploader(
        "Drop CSV, Excel, or JSON",
        type=["csv", "xlsx", "xls", "json"],
        help="Supports CSV, Excel (.xlsx/.xls), JSON",
    )

    if uploaded is not None:
        try:
            ext = uploaded.name.split(".")[-1].lower()
            if ext == "csv":
                raw = pd.read_csv(uploaded)
            elif ext in ("xlsx", "xls"):
                raw = pd.read_excel(uploaded)
            elif ext == "json":
                raw = pd.read_json(uploaded)
            else:
                st.error("Unsupported file type.")
                return

            # Always store raw in session state so it survives reruns
            st.session_state.raw_df  = raw
            st.session_state.clean_df = None
            st.session_state.cleaning_log = []
            st.success(f"✓ Loaded **{uploaded.name}** — {raw.shape[0]:,} rows × {raw.shape[1]} columns")

        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

    # Always read raw from session state so it's available after rerun
    if st.session_state.raw_df is None:
        st.info("Upload a dataset above to begin.")
        return

    raw = st.session_state.raw_df  # ← always from session state, survives balloons() rerun

    # ── Step 2: Raw Audit ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Step 2 — Raw Data Audit")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows",    f"{raw.shape[0]:,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Missing Values", f"{raw.isna().sum().sum():,}",
              delta=f"{raw.isna().sum().sum()/raw.size*100:.1f}% of cells",
              delta_color="inverse")
    c4.metric("Duplicates", f"{raw.duplicated().sum():,}", delta_color="inverse")

    with st.expander("👁 Raw Data Preview (first 100 rows)"):
        safe_dataframe(raw, max_rows=100, height=320)

    # ── Missing Values Heatmap ────────────────────────────────────────────────
    st.markdown("#### Missing Value Map")
    null_pcts = (raw.isna().sum() / len(raw) * 100).round(2)
    fig_null = go.Figure(go.Bar(
        x=null_pcts.index.tolist(),
        y=null_pcts.values.tolist(),
        marker=dict(
            color=null_pcts.values.tolist(),
            colorscale=[[0,"#00e5a0"],[0.1,"#f5c542"],[0.4,"#ff6b35"],[1,"#7f0000"]],
            cmin=0, cmax=100,
            colorbar=dict(title="Null %", tickfont=dict(family="JetBrains Mono", size=10),
                          ticksuffix="%"),
        ),
        hovertemplate="<b>%{x}</b><br>Null: %{y:.1f}%<extra></extra>",
        text=[f"{v:.1f}%" for v in null_pcts.values],
        textposition="outside",
        textfont=dict(family="JetBrains Mono", size=9, color=COLORS["muted"]),
    ))
    fig_null.update_layout(**{
        **LAYOUT, "height": 240,
        "yaxis": dict(range=[0, min(null_pcts.max()*1.3+5, 110)],
                      ticksuffix="%", gridcolor=COLORS["border"], linecolor=COLORS["border"]),
        "xaxis": dict(tickangle=-30, gridcolor=COLORS["border"], linecolor=COLORS["border"]),
    })
    st.plotly_chart(fig_null, use_container_width=True, config={"displayModeBar": False})

    with st.expander("🔬 Column Types & Statistics"):
        dtype_df = pd.DataFrame({
            "Column":   raw.columns,
            "Dtype":    [str(raw[c].dtype) for c in raw.columns],
            "Non-Null": [raw[c].notna().sum() for c in raw.columns],
            "Null %":   [(raw[c].isna().sum()/len(raw)*100).round(2) for c in raw.columns],
            "Unique":   [raw[c].nunique() for c in raw.columns],
            "Sample":   [str(raw[c].dropna().iloc[0]) if raw[c].notna().any() else "—"
                         for c in raw.columns],
        })
        safe_dataframe(dtype_df, max_rows=200, height=300)

    # ── Step 3: Clean Button ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Step 3 — Run Cleaning Pipeline")

    col_opts, col_btn = st.columns([3, 1])
    with col_opts:
        st.markdown("""
        <div style="font-size:12.5px;color:#4a5568;line-height:1.9">
        The pipeline will automatically:<br>
        &nbsp;◆ Standardise column names to snake_case<br>
        &nbsp;◆ Remove fully empty rows &amp; columns<br>
        &nbsp;◆ Remove exact duplicate rows<br>
        &nbsp;◆ Convert numeric strings (e.g. "$1,234" → 1234)<br>
        &nbsp;◆ Parse date strings to datetime<br>
        &nbsp;◆ Impute missing values (mean/median/mode by distribution)<br>
        &nbsp;◆ Cap outliers using IQR×3 method<br>
        &nbsp;◆ Normalise categorical casing
        </div>""", unsafe_allow_html=True)
    with col_btn:
        st.markdown("<br><br>", unsafe_allow_html=True)
        run_clean = st.button("🧹 Clean Data", type="primary", use_container_width=True)

    if run_clean:
        with st.spinner("Running cleaning pipeline…"):
            clean_df, audit = clean_dataframe(raw)
        st.session_state.clean_df     = clean_df
        st.session_state.cleaning_log = audit.steps
        # NO st.balloons() — it triggers rerun which loses local vars
        st.success(f"✓ Cleaning complete — {len(audit.steps)} operations performed")

    # ── Step 4: Results (reads ONLY from session state) ───────────────────────
    clean_df = st.session_state.clean_df
    steps    = st.session_state.cleaning_log

    if clean_df is None:
        return

    st.markdown("---")
    st.markdown("#### Step 4 — Cleaning Report")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Operations", len(steps))
    r2.metric("Rows After",  f"{clean_df.shape[0]:,}",
              delta=f"{clean_df.shape[0]-raw.shape[0]:+,} rows", delta_color="off")
    r3.metric("Nulls Fixed",
              f"{raw.isna().sum().sum() - clean_df.isna().sum().sum():,}",
              delta=f"{clean_df.isna().sum().sum()} remaining", delta_color="off")
    r4.metric("Columns",     clean_df.shape[1],
              delta=f"{clean_df.shape[1]-raw.shape[1]:+} cols", delta_color="off")

    # Cleaning log
    st.markdown("##### Cleaning Log")
    severity_filter = st.multiselect(
        "Filter by type", ["fixed","removed","warning","info"],
        default=["fixed","removed","warning"],
        label_visibility="collapsed",
    )
    for step in steps:
        if step.severity in severity_filter:
            _step_badge(step)

    # Before / After null chart
    st.markdown("##### Before vs After — Null Coverage")
    before_null = (raw.isna().sum() / len(raw) * 100).round(2)
    after_null  = (clean_df.isna().sum() / len(clean_df) * 100).round(2)

    fig_ba = go.Figure()
    fig_ba.add_trace(go.Bar(
        name="Before", x=list(after_null.index),
        y=[before_null.get(c, 0) for c in after_null.index],
        marker_color=COLORS["accent3"], opacity=0.7,
        hovertemplate="<b>%{x}</b><br>Before: %{y:.1f}%<extra></extra>",
    ))
    fig_ba.add_trace(go.Bar(
        name="After", x=list(after_null.index),
        y=after_null.values.tolist(),
        marker_color=COLORS["accent"],
        hovertemplate="<b>%{x}</b><br>After: %{y:.1f}%<extra></extra>",
    ))
    fig_ba.update_layout(**{
        **LAYOUT, "height": 230, "barmode": "group",
        "xaxis": dict(tickangle=-30, gridcolor=COLORS["border"], linecolor=COLORS["border"]),
        "yaxis": dict(ticksuffix="%", gridcolor=COLORS["border"], linecolor=COLORS["border"]),
        "legend": dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
    })
    st.plotly_chart(fig_ba, use_container_width=True, config={"displayModeBar": False})

    # ── Clean Dataset Preview ─────────────────────────────────────────────────
    st.markdown("##### ✅ Clean Dataset Preview")
    st.caption(f"{clean_df.shape[0]:,} rows × {clean_df.shape[1]} columns")
    safe_dataframe(clean_df, max_rows=200, height=420)
    # Preview raw dataset
    safe_dataframe(raw, max_rows=100)



    # ── Step 5: Export ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Step 5 — Export Clean Data")
    fmt = st.radio("Format", ["CSV", "Excel", "JSON"], horizontal=True,
                   label_visibility="collapsed")

    if fmt == "CSV":
        data  = clean_df.to_csv(index=False).encode()
        fname, mime = "clean_data.csv", "text/csv"
    elif fmt == "Excel":
        buf = io.BytesIO()
        clean_df.to_excel(buf, index=False, engine="openpyxl")
        data  = buf.getvalue()
        fname = "clean_data.xlsx"
        mime  = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        data  = clean_df.to_json(orient="records", indent=2).encode()
        fname, mime = "clean_data.json", "application/json"

    col_dl, col_log = st.columns(2)
    with col_dl:
        st.download_button(f"⬇ Download {fmt}", data=data,
                           file_name=fname, mime=mime, use_container_width=True)
    with col_log:
        log_lines = [f"[{s.severity.upper()}] {s.category} | {s.action} | {s.detail}"
                     for s in steps]
        st.download_button("⬇ Download Cleaning Log",
                           data="\n".join(log_lines).encode(),
                           file_name="cleaning_log.txt", mime="text/plain",
                           use_container_width=True)

    st.info("✓ Dataset loaded into workstation — use Dataset Explorer, Charts, Profile, and Report tabs.")