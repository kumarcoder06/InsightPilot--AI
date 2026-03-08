"""pages/profile.py — Deep dataset profiling."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.data import get_df
from utils.display import safe_dataframe




# -------------------------------------------------
# THEME
# -------------------------------------------------

COLORS = dict(
    surface="#0f1117",
    border="#1a1f2e",
    accent="#00e5a0",
    accent2="#0091ff",
    accent3="#ff6b35",
    warn="#f5c542",
    purple="#a855f7",
    muted="#4a5568",
    text="#dde1ec"
)

TYPE_COLORS = {
    "int64":"#0091ff",
    "float64":"#00e5a0",
    "object":"#a855f7",
    "datetime64[ns]":"#f5c542",
    "bool":"#ff6b35",
    "int32":"#0091ff"
}

# Base layout (NO xaxis / yaxis here)
LAYOUT = dict(
    paper_bgcolor=COLORS["surface"],
    plot_bgcolor=COLORS["surface"],
    font=dict(
        family="JetBrains Mono, monospace",
        color=COLORS["muted"],
        size=11
    ),
    margin=dict(l=8, r=8, t=24, b=8),
    hoverlabel=dict(
        bgcolor=COLORS["surface"],
        bordercolor=COLORS["border"],
        font_family="JetBrains Mono"
    )
)

AXIS_STYLE = dict(
    gridcolor=COLORS["border"]
)


# -------------------------------------------------
# PAGE
# -------------------------------------------------

def render():

    st.markdown(
        '<div class="sec-hdr">◈ Profile Data — Deep Column-Level Analysis</div>',
        unsafe_allow_html=True
    )

    # SAFE DATAFRAME ACCESS
    df =get_df()

    if "clean_df" in st.session_state and st.session_state.clean_df is not None:
        df = st.session_state.clean_df
    elif "raw_df" in st.session_state and st.session_state.raw_df is not None:
        df = st.session_state.raw_df

    if df is None:
        st.info("Upload a dataset in **🧹 Data Cleaner** first.")
        return


    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()


# -------------------------------------------------
# KPIs
# -------------------------------------------------

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total Rows", f"{df.shape[0]:,}")
    c2.metric("Total Columns", df.shape[1])
    c3.metric("Numeric Cols", len(num_cols))

    nulls = df.isna().sum().sum()

    c4.metric(
        "Null Cells",
        f"{nulls:,}",
        delta=f"{nulls/df.size*100:.1f}% of all cells",
        delta_color="inverse"
    )


# -------------------------------------------------
# COLUMN FILTER
# -------------------------------------------------

    tbl_filter = st.selectbox(
        "Show columns by type",
        ["All","Numeric","Categorical","Datetime"],
        label_visibility="collapsed"
    )

    if tbl_filter == "Numeric":
        show_cols = num_cols

    elif tbl_filter == "Categorical":
        show_cols = cat_cols

    elif tbl_filter == "Datetime":
        show_cols = df.select_dtypes(include="datetime64").columns.tolist()

    else:
        show_cols = df.columns.tolist()


# -------------------------------------------------
# COLUMN CARDS
# -------------------------------------------------

    per_row = 3

    for i in range(0, len(show_cols), per_row):

        row_cols = st.columns(per_row)

        for j, col in enumerate(show_cols[i:i+per_row]):

            with row_cols[j]:

                dtype_str = str(df[col].dtype)
                tc = TYPE_COLORS.get(dtype_str, COLORS["muted"])

                null_pct = df[col].isna().sum() / len(df) * 100

                null_color = (
                    COLORS["accent"]
                    if null_pct == 0
                    else COLORS["warn"] if null_pct < 10
                    else COLORS["accent3"]
                )

                completeness = 100 - null_pct

                is_num = pd.api.types.is_numeric_dtype(df[col])

                st.markdown(f"""
                <div style="background:#0f1117;border:1px solid #1a1f2e;border-radius:10px;
                            padding:14px 16px;margin-bottom:12px">

                    <div style="font-family:JetBrains Mono,monospace;font-size:12px;
                                color:#0091ff;font-weight:500;margin-bottom:8px">
                        {col}
                    </div>

                    <div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:4px">
                        <span style="color:#4a5568">Type</span>
                        <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{tc};
                                     background:rgba(0,0,0,0.3);padding:1px 6px;border-radius:3px">
                            {dtype_str}
                        </span>
                    </div>

                    <div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:4px">
                        <span style="color:#4a5568">Unique</span>
                        <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#dde1ec">
                            {df[col].nunique():,}
                        </span>
                    </div>

                    <div style="display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:6px">
                        <span style="color:#4a5568">Null %</span>
                        <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{null_color}">
                            {null_pct:.1f}%
                        </span>
                    </div>

                    <div style="background:#090b0f;border-radius:3px;height:4px;overflow:hidden">
                        <div style="width:{completeness:.1f}%;height:100%;
                                    background:{null_color};border-radius:3px"></div>
                    </div>

                    <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#4a5568;margin-top:3px">
                        {completeness:.1f}% complete
                    </div>

                </div>
                """, unsafe_allow_html=True)


# -------------------------------------------------
# NULL COVERAGE CHART
# -------------------------------------------------

    st.markdown("---")
    st.markdown("##### Null Coverage Overview")

    null_s = (df.isna().sum() / len(df) * 100).round(2)

    fig = go.Figure(go.Bar(
        x=null_s.index.tolist(),
        y=null_s.values.tolist(),
        marker=dict(
            color=null_s.values.tolist(),
            colorscale=[
                [0,"#00e5a0"],
                [0.05,"#f5c542"],
                [0.2,"#ff6b35"],
                [1,"#7f0000"]
            ],
            cmin=0,
            cmax=30
        ),
        text=[f"{v:.1f}%" for v in null_s.values],
        textposition="outside"
    ))

    fig.update_layout(**LAYOUT, height=230)

    fig.update_xaxes(**AXIS_STYLE, tickangle=-30)

    fig.update_yaxes(
        **AXIS_STYLE,
        ticksuffix="%",
        range=[0, max(null_s.max()*1.3+2,10)]
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------
# DATA TYPE PIE
# -------------------------------------------------

    st.markdown("##### Data Type Distribution")

    dtype_counts = df.dtypes.astype(str).value_counts()

    fig_dt = go.Figure(go.Pie(
        labels=dtype_counts.index.tolist(),
        values=dtype_counts.values.tolist(),
        hole=0.5,
        marker_colors=[TYPE_COLORS.get(t, COLORS["muted"]) for t in dtype_counts.index]
    ))

    fig_dt.update_layout(**LAYOUT, height=220)

    st.plotly_chart(fig_dt, use_container_width=True)