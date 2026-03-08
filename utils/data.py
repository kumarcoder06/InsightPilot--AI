"""utils/data.py — Central dataset loader"""

import streamlit as st
import pandas as pd


def get_df() -> pd.DataFrame | None:
    """
    Returns cleaned dataset if available,
    otherwise raw dataset.
    """

    if "clean_df" in st.session_state and st.session_state.clean_df is not None:
        return st.session_state.clean_df

    if "raw_df" in st.session_state and st.session_state.raw_df is not None:
        return st.session_state.raw_df

    return None