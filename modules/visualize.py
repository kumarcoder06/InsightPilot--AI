"""pages/visualize.py — Power BI–style charts. Uses uploaded data if available."""

from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

# ── Theme ─────────────────────────────────────────────────────────────────────
COLORS = dict(
    bg="#090b0f", surface="#0f1117", border="#1a1f2e",
    accent="#00e5a0", accent2="#0091ff", accent3="#ff6b35",
    warn="#f5c542", purple="#a855f7", muted="#4a5568", text="#dde1ec",
)
PALETTE = [COLORS["accent"], COLORS["accent2"], COLORS["accent3"],
           COLORS["warn"], COLORS["purple"], "#ec4899", "#14b8a6", "#6366f1"]

LAYOUT = dict(
    paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
    font=dict(family="JetBrains Mono, monospace", color=COLORS["muted"], size=11),
    margin=dict(l=8, r=8, t=32, b=8),
    hoverlabel=dict(bgcolor=COLORS["surface"], bordercolor=COLORS["border"],
                    font_family="JetBrains Mono"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"],
                font_color=COLORS["muted"]),
)
AXIS = dict(gridcolor=COLORS["border"], linecolor=COLORS["border"])

def _layout(fig, **kw):
    fig.update_layout(**{**LAYOUT, **kw})

# ── Demo data (fallback only) ─────────────────────────────────────────────────
DEMO_REV = pd.DataFrame({
    "month": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
    "revenue": [284000,311000,298000,342000,375000,391000,368000,414000,438000,402000,461000,497000],
    "orders":  [1240,1380,1310,1510,1645,1720,1612,1809,1932,1774,2021,2186],
})
DEMO_CAT = pd.DataFrame({
    "category": ["Enterprise Software","Cloud Services","Hardware","Consulting","Support Plans"],
    "revenue":  [1970000,1310000,700000,468000,234000],
})

# ── Smart column detector ─────────────────────────────────────────────────────
def _find_col(df: pd.DataFrame, hints: list[str]) -> str | None:
    """Return first column whose name contains any hint (case-insensitive)."""
    for h in hints:
        for c in df.columns:
            if h.lower() in c.lower():
                return c
    return None

def _smart_date_col(df: pd.DataFrame) -> str | None:
    """Find date col: first checks parsed datetime64, then tries to parse string cols."""
    # 1. already parsed
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    # 2. name-hinted string cols — try parsing a sample
    hints = ["date","time","month","year","week","day","period","timestamp","created","updated"]
    for h in hints:
        for c in df.columns:
            if h.lower() in c.lower() and df[c].dtype == object:
                try:
                    sample = pd.to_datetime(df[c].dropna().head(10), errors="raise")
                    if len(sample) > 0:
                        return c
                except Exception:
                    pass
    return None

def _num_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()

def _cat_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="object").columns.tolist()

def _date_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["datetime64"]).columns.tolist()

# ── KPI builder from real data ────────────────────────────────────────────────
def _build_kpis(df: pd.DataFrame) -> list[dict]:
    kpis = []
    nums = _num_cols(df)
    for col in nums[:4]:
        val = df[col].sum()
        mean = df[col].mean()
        label = col.replace("_", " ").title()
        if val > 1_000_000:
            display = f"${val/1_000_000:.2f}M"
        elif val > 1_000:
            display = f"{val:,.0f}"
        else:
            display = f"{val:.2f}"
        kpis.append({"label": label, "value": display, "delta": f"mean {mean:.2f}"})
    return kpis

# ── Chart builders ────────────────────────────────────────────────────────────

def _chart_trend(df: pd.DataFrame):
    """Line/area trend — date vs numeric, or index vs numeric."""
    date_col = _smart_date_col(df)
    nums = _num_cols(df)
    if not nums:
        return None, "No numeric columns for trend chart."

    y_col = nums[0]
    # prefer revenue/sales/amount/total as primary
    for hint in ["revenue","sales","amount","total","price","value","income"]:
        c = _find_col(df, [hint])
        if c and c in nums:
            y_col = c
            break

    if date_col:
        tmp = df[[date_col, y_col]].copy().dropna()
        # parse if still string
        if tmp[date_col].dtype == object:
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp = tmp.dropna(subset=[date_col])
        tmp = tmp.sort_values(date_col)
        x_vals = tmp[date_col].astype(str)
        y_vals = tmp[y_col]
        df_sorted = tmp
        x_title = date_col.replace("_"," ").title()
    else:
        # use row index
        df_agg = df[y_col].dropna().reset_index(drop=True)
        x_vals = df_agg.index
        y_vals = df_agg.values
        x_title = "Row"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, fill="tozeroy",
        name=y_col.replace("_"," ").title(),
        line=dict(color=COLORS["accent"], width=2),
        hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y:,.2f}}<extra></extra>",
    ))

    # overlay second numeric as bar on secondary y
    if len(nums) > 1:
        y2_col = [c for c in nums if c != y_col][0]
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(
            x=x_vals, y=y_vals, fill="tozeroy",
            name=y_col.replace("_"," ").title(),
            line=dict(color=COLORS["accent"], width=2),
        ), secondary_y=False)
        if date_col:
            # pull y2 from df aligned to the same date-filtered rows
            df_full = df[[date_col, y_col, y2_col]].dropna().sort_values(date_col)
            x_vals  = df_full[date_col].astype(str)
            y_vals  = df_full[y_col]
            y2_vals = df_full[y2_col]
        else:
            df_full = df[[y_col, y2_col]].dropna().reset_index(drop=True)
            x_vals  = df_full.index
            y_vals  = df_full[y_col]
            y2_vals = df_full[y2_col]
        fig2.add_trace(go.Bar(
            x=x_vals, y=y2_vals,
            name=y2_col.replace("_"," ").title(),
            marker_color=COLORS["accent2"], opacity=0.4,
        ), secondary_y=True)
        _layout(fig2, height=280,
                title=dict(text=f"{y_col.replace('_',' ').title()} & {y2_col.replace('_',' ').title()} Trend",
                           font_size=12, x=0))
        fig2.update_xaxes(**AXIS, title=x_title)
        fig2.update_yaxes(**AXIS)
        return fig2, None

    _layout(fig, height=280,
            title=dict(text=f"{y_col.replace('_',' ').title()} Over Time",
                       font_size=12, x=0))
    fig.update_xaxes(**AXIS, title=x_title)
    fig.update_yaxes(**AXIS)
    return fig, None


def _chart_distribution(df: pd.DataFrame):
    """Donut / pie — best categorical column by value counts or numeric sum."""
    cats = _cat_cols(df)
    nums = _num_cols(df)

    # Try: category col + numeric col (e.g. category + revenue)
    cat_col = _find_col(df, ["category","type","segment","region","channel",
                              "status","product","department","group","name"])
    num_col = _find_col(df, ["revenue","sales","amount","total","value","sum","count"])

    if cat_col and num_col and num_col in nums:
        agg = df.groupby(cat_col)[num_col].sum().nlargest(8).reset_index()
        labels = agg[cat_col].astype(str).tolist()
        values = agg[num_col].tolist()
        title  = f"{num_col.replace('_',' ').title()} by {cat_col.replace('_',' ').title()}"
    elif cat_col:
        vc = df[cat_col].value_counts().head(8)
        labels = vc.index.astype(str).tolist()
        values = vc.values.tolist()
        title  = f"Distribution of {cat_col.replace('_',' ').title()}"
    elif cats:
        vc = df[cats[0]].value_counts().head(8)
        labels = vc.index.astype(str).tolist()
        values = vc.values.tolist()
        title  = f"Distribution of {cats[0].replace('_',' ').title()}"
    else:
        return None, "No categorical columns for distribution chart."

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker_colors=PALETTE[:len(labels)],
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>",
    ))
    _layout(fig, height=260,
            title=dict(text=title, font_size=12, x=0))
    return fig, None


def _chart_top_n(df: pd.DataFrame):
    """Horizontal bar — top N of a category by a numeric metric."""
    cats = _cat_cols(df)
    nums = _num_cols(df)
    if not cats or not nums:
        return None, "Need at least one categorical and one numeric column."

    cat_col = _find_col(df, ["name","category","product","channel","region",
                              "segment","department","type","group"])
    if not cat_col:
        cat_col = cats[0]

    num_col = _find_col(df, ["revenue","sales","amount","total","value","quantity","count"])
    if not num_col or num_col not in nums:
        num_col = nums[0]

    agg = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
    agg = agg.sort_values(num_col)

    fig = go.Figure(go.Bar(
        y=agg[cat_col].astype(str),
        x=agg[num_col],
        orientation="h",
        marker=dict(
            color=agg[num_col],
            colorscale=[[0, COLORS["accent2"]], [1, COLORS["accent"]]],
        ),
        hovertemplate=f"<b>%{{y}}</b><br>{num_col}: %{{x:,.2f}}<extra></extra>",
        text=agg[num_col].apply(lambda v: f"{v:,.0f}"),
        textposition="outside",
    ))
    _layout(fig, height=max(280, len(agg)*32),
            title=dict(text=f"Top {len(agg)} {cat_col.replace('_',' ').title()} by {num_col.replace('_',' ').title()}",
                       font_size=12, x=0))
    fig.update_xaxes(**AXIS)
    fig.update_yaxes(**AXIS)
    return fig, None


def _chart_scatter(df: pd.DataFrame):
    """Scatter — two numeric columns, optionally coloured by category."""
    nums = _num_cols(df)
    if len(nums) < 2:
        return None, "Need at least 2 numeric columns for scatter chart."

    x_col = nums[0]
    y_col = nums[1]
    # prefer meaningful pairs
    for xh in ["revenue","sales","amount","price","cost"]:
        c = _find_col(df, [xh])
        if c and c in nums:
            x_col = c
            break
    for yh in ["profit","margin","quantity","orders","count"]:
        c = _find_col(df, [yh])
        if c and c in nums and c != x_col:
            y_col = c
            break

    cats = _cat_cols(df)
    color_col = _find_col(df, ["category","segment","type","region","channel","status"])
    if not color_col and cats:
        color_col = cats[0]

    sample = df[[x_col, y_col]].dropna()
    if len(sample) > 500:
        sample = sample.sample(500, random_state=42)

    if color_col and color_col in df.columns:
        sample = sample.join(df[color_col].str[:20], how="left")
        groups = sample[color_col].unique()
        fig = go.Figure()
        for i, grp in enumerate(groups[:8]):
            mask = sample[color_col] == grp
            fig.add_trace(go.Scatter(
                x=sample.loc[mask, x_col], y=sample.loc[mask, y_col],
                mode="markers", name=str(grp),
                marker=dict(color=PALETTE[i % len(PALETTE)], size=7, opacity=0.7),
                hovertemplate=f"<b>{grp}</b><br>{x_col}: %{{x:,.2f}}<br>{y_col}: %{{y:,.2f}}<extra></extra>",
            ))
    else:
        fig = go.Figure(go.Scatter(
            x=sample[x_col], y=sample[y_col], mode="markers",
            marker=dict(color=COLORS["accent"], size=6, opacity=0.6),
            hovertemplate=f"{x_col}: %{{x:,.2f}}<br>{y_col}: %{{y:,.2f}}<extra></extra>",
        ))

    _layout(fig, height=300,
            title=dict(text=f"{x_col.replace('_',' ').title()} vs {y_col.replace('_',' ').title()}",
                       font_size=12, x=0))
    fig.update_xaxes(**AXIS, title=x_col.replace("_"," ").title())
    fig.update_yaxes(**AXIS, title=y_col.replace("_"," ").title())
    return fig, None


def _chart_histogram(df: pd.DataFrame, col: str):
    """Histogram of a single numeric column."""
    data = df[col].dropna()
    fig = go.Figure(go.Histogram(
        x=data, nbinsx=30,
        marker_color=COLORS["accent2"], opacity=0.8,
        hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>",
    ))
    _layout(fig, height=260,
            title=dict(text=f"Distribution of {col.replace('_',' ').title()}",
                       font_size=12, x=0))
    fig.update_xaxes(**AXIS)
    fig.update_yaxes(**AXIS)
    return fig


def _chart_correlation(df: pd.DataFrame):
    """Correlation heatmap of numeric columns."""
    nums = _num_cols(df)
    if len(nums) < 2:
        return None
    cols = nums[:10]
    corr = df[cols].corr().round(2)
    fig = go.Figure(go.Heatmap(
        z=corr.values.tolist(),
        x=cols, y=cols,
        colorscale=[[0, COLORS["accent3"]], [0.5, COLORS["surface"]], [1, COLORS["accent"]]],
        zmid=0,
        text=corr.round(2).values.tolist(),
        texttemplate="%{text}",
        hovertemplate="<b>%{y} × %{x}</b><br>r = %{z:.2f}<extra></extra>",
    ))
    _layout(fig, height=max(300, len(cols)*45),
            title=dict(text="Correlation Matrix", font_size=12, x=0))
    return fig


# ── Auto insight text ─────────────────────────────────────────────────────────
def _auto_insights(df: pd.DataFrame) -> list[str]:
    insights = []
    nums = _num_cols(df)
    cats = _cat_cols(df)

    for col in nums[:4]:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        insights.append(
            f"**{col.replace('_',' ').title()}** — "
            f"Total: `{s.sum():,.2f}` | Mean: `{s.mean():,.2f}` | "
            f"Min: `{s.min():,.2f}` | Max: `{s.max():,.2f}`"
        )

    for col in cats[:2]:
        top = df[col].value_counts().iloc[0]
        top_val = df[col].value_counts().index[0]
        pct = top / len(df) * 100
        insights.append(
            f"**{col.replace('_',' ').title()}** — "
            f"Top value: `{top_val}` ({pct:.1f}% of rows) | "
            f"{df[col].nunique()} unique values"
        )

    null_pct = df.isna().sum().sum() / df.size * 100
    insights.append(f"**Data Quality** — {df.shape[0]:,} rows × {df.shape[1]} columns | "
                    f"Null cells: `{null_pct:.1f}%`")
    return insights


# ── Main render ───────────────────────────────────────────────────────────────
def render():
    st.markdown('<div class="sec-hdr">📊 Power BI–Style Charts — Dynamic Insights from Your Data</div>',
                unsafe_allow_html=True)

    _clean = st.session_state.get("clean_df")
    _raw   = st.session_state.get("raw_df")
    user_df = _clean if _clean is not None else _raw

    using_upload = user_df is not None

    # ── Mode banner ───────────────────────────────────────────────────────────
    if using_upload:
        st.success(f"✓ Using your uploaded dataset — {user_df.shape[0]:,} rows × {user_df.shape[1]} columns")
        df = user_df
    else:
        st.info("No dataset uploaded — showing demo dashboard. Upload data in 🧹 Data Cleaner to see your insights.")
        df = None

    # ── Tabs: Dynamic vs Demo ─────────────────────────────────────────────────
    if using_upload:
        tab1, tab2, tab3 = st.tabs(["📈 Auto Dashboard", "🔧 Custom Chart Builder", "📋 Demo Dashboard"])
    else:
        tab1, tab2, tab3 = st.tabs(["📋 Demo Dashboard", "📈 Auto Dashboard (upload data)", "🔧 Custom Chart Builder"])

    # ════════════════════════════════════════════════════════════
    # TAB: AUTO DYNAMIC DASHBOARD (uploaded data)
    # ════════════════════════════════════════════════════════════
    with (tab1 if using_upload else tab2):
        if not using_upload:
            st.info("Upload a dataset in 🧹 Data Cleaner to generate your dynamic dashboard.")
        else:
            nums = _num_cols(df)
            cats = _cat_cols(df)

            # ── KPIs ──────────────────────────────────────────────────────────
            st.markdown("### 📌 Key Metrics")
            kpis = _build_kpis(df)
            if kpis:
                cols = st.columns(len(kpis))
                for i, kpi in enumerate(kpis):
                    cols[i].metric(kpi["label"], kpi["value"], kpi["delta"])
            st.markdown("---")

            # ── Auto Insights Text ────────────────────────────────────────────
            st.markdown("### 💡 Auto Insights")
            for ins in _auto_insights(df):
                st.markdown(f"◆ {ins}")
            st.markdown("---")

            # ── Trend Chart ───────────────────────────────────────────────────
            st.markdown("### 📈 Trend")
            fig, err = _chart_trend(df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption(err)

            # ── Distribution + Top N side by side ────────────────────────────
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("### 🍩 Distribution")
                fig, err = _chart_distribution(df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption(err)

            with col_r:
                st.markdown("### 🏆 Top N")
                fig, err = _chart_top_n(df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption(err)

            # ── Scatter ───────────────────────────────────────────────────────
            if len(nums) >= 2:
                st.markdown("### 🔵 Scatter Analysis")
                fig, err = _chart_scatter(df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption(err)

            # ── Correlation Heatmap ───────────────────────────────────────────
            if len(nums) >= 2:
                st.markdown("### 🔥 Correlation Heatmap")
                fig = _chart_correlation(df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

            # ── Per-column histograms ─────────────────────────────────────────
            if nums:
                st.markdown("### 📊 Column Distributions")
                sel = st.selectbox("Select numeric column", nums, key="hist_col")
                st.plotly_chart(_chart_histogram(df, sel), use_container_width=True)

    # ════════════════════════════════════════════════════════════
    # TAB: CUSTOM CHART BUILDER
    # ════════════════════════════════════════════════════════════
    with (tab2 if using_upload else tab3):
        st.markdown("### 🔧 Custom Chart Builder")
        if not using_upload:
            st.info("Upload a dataset first to use the custom chart builder.")
        else:
            all_cols = df.columns.tolist()
            nums = _num_cols(df)
            cats = _cat_cols(df)

            b1, b2, b3 = st.columns(3)
            chart_type = b1.selectbox("Chart type", ["Bar","Line","Area","Scatter","Histogram","Box","Pie"], key="cb_type")
            x_col = b2.selectbox("X axis", all_cols, key="cb_x")
            y_col = b3.selectbox("Y axis (numeric)", nums, key="cb_y") if nums else None

            color_col = st.selectbox("Color by (optional)", ["None"] + cats, key="cb_color")
            color_col = None if color_col == "None" else color_col

            agg = st.selectbox("Aggregation", ["None","Sum","Mean","Count","Max","Min"], key="cb_agg")

            if st.button("Generate Chart", type="primary"):
                try:
                    plot_df = df[[x_col] + ([y_col] if y_col else []) + ([color_col] if color_col else [])].dropna()

                    if agg != "None" and y_col:
                        grp_cols = [x_col] + ([color_col] if color_col else [])
                        agg_fn = {"Sum":"sum","Mean":"mean","Count":"count","Max":"max","Min":"min"}[agg]
                        plot_df = plot_df.groupby(grp_cols)[y_col].agg(agg_fn).reset_index()

                    if chart_type == "Bar":
                        fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col,
                                     color_discrete_sequence=PALETTE)
                    elif chart_type == "Line":
                        fig = px.line(plot_df, x=x_col, y=y_col, color=color_col,
                                      color_discrete_sequence=PALETTE)
                    elif chart_type == "Area":
                        fig = px.area(plot_df, x=x_col, y=y_col, color=color_col,
                                      color_discrete_sequence=PALETTE)
                    elif chart_type == "Scatter":
                        fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col,
                                         color_discrete_sequence=PALETTE)
                    elif chart_type == "Histogram":
                        fig = px.histogram(plot_df, x=x_col, color=color_col,
                                           color_discrete_sequence=PALETTE)
                    elif chart_type == "Box":
                        fig = px.box(plot_df, x=x_col, y=y_col, color=color_col,
                                     color_discrete_sequence=PALETTE)
                    elif chart_type == "Pie":
                        fig = px.pie(plot_df, names=x_col, values=y_col,
                                     color_discrete_sequence=PALETTE)

                    _layout(fig, height=380)
                    fig.update_xaxes(**AXIS)
                    fig.update_yaxes(**AXIS)
                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Chart error: {e}")

    # ════════════════════════════════════════════════════════════
    # TAB: DEMO DASHBOARD (static)
    # ════════════════════════════════════════════════════════════
    with (tab3 if using_upload else tab1):
        st.markdown("### Demo Dashboard — SaaS Business Sample Data")
        st.caption("This is sample data. Upload your dataset to see real insights.")

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Revenue YTD","$4.68M","+18.4%")
        k2.metric("Orders","19,939","+12.1%")
        k3.metric("Customers","1,593","+9.7%")
        k4.metric("Avg Order Value","$234.8","-2.3%")
        st.markdown("---")

        fig_rev = make_subplots(specs=[[{"secondary_y": True}]])
        fig_rev.add_trace(go.Scatter(x=DEMO_REV["month"], y=DEMO_REV["revenue"],
            name="Revenue", fill="tozeroy", line=dict(color=COLORS["accent"], width=2)),
            secondary_y=False)
        fig_rev.add_trace(go.Bar(x=DEMO_REV["month"], y=DEMO_REV["orders"],
            name="Orders", marker_color=COLORS["accent2"], opacity=0.4),
            secondary_y=True)
        _layout(fig_rev, height=260)
        fig_rev.update_xaxes(**AXIS)
        fig_rev.update_yaxes(**AXIS)
        st.plotly_chart(fig_rev, use_container_width=True)

        col_d, col_b = st.columns(2)
        with col_d:
            fig_donut = go.Figure(go.Pie(
                labels=DEMO_CAT["category"], values=DEMO_CAT["revenue"],
                hole=0.55, marker_colors=PALETTE))
            _layout(fig_donut, height=260)
            st.plotly_chart(fig_donut, use_container_width=True)
        with col_b:
            fig_bar = go.Figure(go.Bar(
                y=DEMO_CAT["category"], x=DEMO_CAT["revenue"],
                orientation="h",
                marker=dict(color=DEMO_CAT["revenue"],
                            colorscale=[[0,COLORS["accent2"]],[1,COLORS["accent"]]]),
            ))
            _layout(fig_bar, height=260)
            fig_bar.update_xaxes(**AXIS)
            fig_bar.update_yaxes(**AXIS)
            st.plotly_chart(fig_bar, use_container_width=True)