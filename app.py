import streamlit as st

st.set_page_config(
    page_title="InsightAI · Analyst Workstation",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Syne', sans-serif !important;
    background-color: #090b0f !important;
    color: #dde1ec !important;
}
[data-testid="stSidebar"] {
    background-color: #0f1117 !important;
    border-right: 1px solid #1a1f2e !important;
}
[data-testid="stSidebar"] * { color: #dde1ec !important; }
.main .block-container { padding: 1.2rem 1.8rem !important; max-width: 100% !important; }

/* Buttons */
.stButton > button {
    background: #0f1117 !important; color: #dde1ec !important;
    border: 1px solid #1a1f2e !important; border-radius: 7px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { border-color: #00e5a0 !important; color: #00e5a0 !important; }
.stButton > button[kind="primary"] {
    background: #00e5a0 !important; color: #000 !important;
    border-color: #00e5a0 !important;
}
.stButton > button[kind="primary"]:hover { background: #00ffb3 !important; }

/* Inputs */
.stTextArea textarea, .stTextInput input, .stNumberInput input {
    background: #0f1117 !important; border: 1px solid #1a1f2e !important;
    color: #dde1ec !important; border-radius: 7px !important;
    font-family: 'Syne', sans-serif !important;
}
.stTextArea textarea:focus, .stTextInput input:focus { border-color: #00e5a0 !important; box-shadow: 0 0 0 1px #00e5a0 !important; }

/* Selectbox / multiselect */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: #0f1117 !important; border: 1px solid #1a1f2e !important;
    color: #dde1ec !important; border-radius: 7px !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: #0f1117 !important; border: 1px solid #1a1f2e !important;
    border-radius: 10px !important; padding: 14px 16px !important;
}
[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; color: #dde1ec !important; }
[data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; font-size: 11px !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #1a1f2e !important; border-radius: 8px !important; overflow: hidden; }
.dvn-scroller { background: #0f1117 !important; }

/* Tabs */
[data-baseweb="tab-list"] { background: #0f1117 !important; border-bottom: 1px solid #1a1f2e !important; gap: 0 !important; }
[data-baseweb="tab"] { background: transparent !important; color: #4a5568 !important; font-family: 'Syne', sans-serif !important; font-weight: 600 !important; }
[aria-selected="true"][data-baseweb="tab"] { color: #00e5a0 !important; border-bottom: 2px solid #00e5a0 !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: #0f1117 !important; border: 2px dashed #1a1f2e !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #00e5a0 !important; }

/* Expander */
.streamlit-expanderHeader {
    background: #0f1117 !important; border: 1px solid #1a1f2e !important;
    border-radius: 7px !important; font-weight: 600 !important;
    color: #dde1ec !important;
}
.streamlit-expanderContent { background: #0a0c12 !important; border: 1px solid #1a1f2e !important; border-top: none !important; }

/* Progress bar */
.stProgress > div > div { background: #00e5a0 !important; }

/* Alerts */
.stSuccess { background: rgba(0,229,160,0.08) !important; border: 1px solid rgba(0,229,160,0.3) !important; border-radius: 8px !important; }
.stWarning { background: rgba(245,197,66,0.08) !important; border: 1px solid rgba(245,197,66,0.3) !important; border-radius: 8px !important; }
.stError   { background: rgba(255,107,53,0.08) !important; border: 1px solid rgba(255,107,53,0.3) !important; border-radius: 8px !important; }
.stInfo    { background: rgba(0,145,255,0.08) !important; border: 1px solid rgba(0,145,255,0.3) !important; border-radius: 8px !important; }

/* Divider */
hr { border-color: #1a1f2e !important; margin: 12px 0 !important; }

/* Code */
code, pre { font-family: 'JetBrains Mono', monospace !important; background: #080a10 !important; color: #7dd3fc !important; border: 1px solid #1a1f2e !important; border-radius: 6px !important; }

/* Radio */
.stRadio > div { gap: 4px !important; }
.stRadio label { font-family: 'Syne', sans-serif !important; }

/* Checkbox */
.stCheckbox label { font-family: 'Syne', sans-serif !important; }

/* Section headers */
.sec-hdr {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; color: #4a5568; letter-spacing: 2px;
    text-transform: uppercase; padding-bottom: 8px;
    border-bottom: 1px solid #1a1f2e; margin-bottom: 14px; font-weight: 500;
}
.card {
    background: #0f1117; border: 1px solid #1a1f2e; border-radius: 10px;
    padding: 16px 18px; margin-bottom: 14px;
}
.badge {
    display: inline-block; font-family: 'JetBrains Mono', monospace;
    font-size: 10px; padding: 2px 8px; border-radius: 4px;
    background: #161c28; border: 1px solid #1a1f2e; color: #4a5568;
}
</style>
""", unsafe_allow_html=True)

# ── Session defaults ──────────────────────────────────────────────────────────
for key, val in {
    "api_key":        "",
    "raw_df":         None,   # uploaded raw dataframe
    "clean_df":       None,   # cleaned dataframe
    "cleaning_log":   [],     # list of cleaning steps
    "chat_messages":  [],
    "pg_connected":   False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Imports ───────────────────────────────────────────────────────────────────
from pages import chat, visualize, profile, report, data_cleaner, dataset_explorer

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:8px 0 18px 0;border-bottom:1px solid #1a1f2e;margin-bottom:18px">
  <div style="font-size:20px;font-weight:800;letter-spacing:-0.5px">◈ <span style="color:#00e5a0">Insight</span>AI</div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;background:#101520;color:#00e5a0;
              padding:3px 10px;border-radius:20px;border:1px solid #1a1f2e;letter-spacing:1px">
    ANALYST WORKSTATION
  </div>
  <div style="margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:10px;color:#4a5568;
              background:#0f1117;border:1px solid #1a1f2e;padding:4px 12px;border-radius:6px">
    <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#00e5a0;
                 margin-right:6px;box-shadow:0 0 6px #00e5a0"></span>
    Python · Streamlit · Pandas · NumPy
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ InsightAI")
    st.markdown('<div class="sec-hdr" style="margin-top:10px">Navigation</div>', unsafe_allow_html=True)

    page = st.radio("", [
        "🧹  Data Cleaner",
        "📂  Dataset Explorer",
        "◎   AI Query (NL→SQL)",
        "📊  Power BI Charts",
        "◈   Profile Data",
        "≡   Report",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="sec-hdr">API Key</div>', unsafe_allow_html=True)
    api_key = st.text_input(
    "Gemini API Key",
    type="password",
    value=st.session_state.api_key,
    placeholder="AIza...",
    label_visibility="collapsed"
)
if api_key:
    st.session_state.api_key = api_key
    st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#00e5a0">✓ Gemini API key set</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Dataset status
    st.markdown('<div class="sec-hdr">Dataset Status</div>', unsafe_allow_html=True)
    if st.session_state.raw_df is not None:
        df = st.session_state.clean_df if st.session_state.clean_df is not None else st.session_state.raw_df
        st.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;line-height:1.9;color:#4a5568">
          <span style="color:#00e5a0">✓</span> Dataset loaded<br>
          Rows: <span style="color:#dde1ec">{df.shape[0]:,}</span><br>
          Cols: <span style="color:#dde1ec">{df.shape[1]}</span><br>
          Cleaned: <span style="color:{'#00e5a0' if st.session_state.clean_df is not None else '#ff6b35'}">
            {'Yes' if st.session_state.clean_df is not None else 'No'}</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#4a5568">No dataset loaded</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:#2a3040">v2.0 · Python + Streamlit</span>', unsafe_allow_html=True)

# ── Route ─────────────────────────────────────────────────────────────────────
if   "Cleaner"   in page: data_cleaner.render()
elif "Explorer"  in page: dataset_explorer.render()
elif "AI Query"  in page: chat.render()
elif "Power BI"  in page: visualize.render()
elif "Profile"   in page: profile.render()
elif "Report"    in page: report.render()
