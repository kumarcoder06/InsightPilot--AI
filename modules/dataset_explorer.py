"""pages/dataset_explorer.py — Dataset explorer with terminal debug"""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.data import get_df
from utils.display import safe_dataframe


def render():

    st.title("📂 Dataset Explorer")

    df = get_df()

    if df is None:
        st.warning("Upload a dataset in Data Cleaner.")
        return

    st.subheader("Dataset Preview")

    safe_dataframe(df, max_rows=500)

    st.subheader("Dataset Summary")

    c1, c2, c3 = st.columns(3)

    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    c3.metric("Null Values", f"{df.isna().sum().sum():,}")

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if num_cols:

        st.subheader("Numeric Distribution")

        col = st.selectbox("Select numeric column", num_cols)

        fig = go.Figure()

        fig.add_trace(
            go.Histogram(
                x=df[col].dropna(),
                nbinsx=40
            )
        )

        fig.update_layout(height=350)

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No numeric columns detected.")