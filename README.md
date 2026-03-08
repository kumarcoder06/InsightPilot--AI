# ◈ InsightAI v2 — AI Analyst Workstation
### Python · Streamlit · Pandas · NumPy · Plotly ·Gemini· PostgreSQL

A professional data analyst workstation with 6 integrated modules:
dirty data cleaning, dataset exploration, NL→SQL, Power BI–style charts,
column profiling, and AI report generation.

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run
streamlit run app.py

# 3. Open
http://localhost:8501
```

---

## 📁 Project Structure

```
insightai/
├── app.py                         # Main entry + sidebar + routing
├── requirements.txt
├── README.md
├── pages/
│   ├── data_cleaner.py            # Upload dirty data → auto-clean pipeline
│   ├── dataset_explorer.py        # Stats, calcs, pivot, correlation, distribution
│   ├── chat.py                    # NL → SQL via Gemini API
│   ├── visualize.py               # Power BI–style Plotly charts
│   ├── profile.py                 # Deep column profiling
│   └── report.py                  # AI-generated business reports
└── utils/
    └── cleaner_engine.py          # Core cleaning pipeline (pandas + numpy)
```

---

## 🧹 Data Cleaner Pipeline

The cleaner (`utils/cleaner_engine.py`) runs these steps automatically:

| Step | What it does |
|------|-------------|
| Column Names | Renames to snake_case |
| Empty Data | Drops fully-empty rows and columns |
| Duplicates | Removes exact duplicate rows |
| Data Types | Detects numeric strings ($1,234 → 1234), parses dates |
| String Cleaning | Strips whitespace, replaces NULL/N/A/"" with NaN |
| Categorical | Normalises casing (ACTIVE → Active) |
| Missing Values | Imputes: mean (normal dist), median (skewed), mode (categorical) |
| Outliers | IQR×3 method — caps extreme values, preserves distribution |

Generates a full audit log with before/after metrics for every operation.

---

## 📊 Power BI–Style Charts

Built with Plotly to mimic Power BI visuals:
- Area + Bar combo (dual Y-axis)
- Donut / Ring chart
- Horizontal bar with conditional colour
- Waterfall (QoQ change)
- Scatter bubble chart
- KPI Gauge indicators
- Custom chart builder (any uploaded dataset)

---

## 🔑 API Key

Set in the sidebar. Get one at: https://aistudio.google.com/

---

## 🗄️ Connect PostgreSQL

Add to `utils/db.py`:

```python
import psycopg2, pandas as pd

def run_query(sql: str) -> pd.DataFrame:
    conn = psycopg2.connect(host="localhost", dbname="business_db",
                             user="postgres", password="your_pw")
    df = pd.read_sql(sql, conn)
    conn.close()
    return df
```

Then call `run_query(msg["sql"])` in `pages/chat.py` after Gemini generates the SQL.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Streamlit | Web UI framework |
| Pandas | Data manipulation & cleaning |
| NumPy | Numerical operations, IQR outlier detection |
| Plotly | Power BI–style interactive charts |
| Google SDK | NL→SQL, AI report generation |
| DuckDB | In-memory SQL on uploaded DataFrames |
| psycopg2 | PostgreSQL connection |
| SciPy | Statistical tests |
| scikit-learn | Preprocessing, clustering |
| openpyxl | Excel read/write |
