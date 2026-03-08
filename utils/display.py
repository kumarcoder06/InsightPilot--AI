"""
utils/display.py
Stable dataframe renderer — uses st.components.v1.html (iframe).
Bypasses both Arrow serialisation AND Streamlit HTML sanitiser.
Works with any dtype: datetime64, mixed numpy, lists, dicts.
"""

import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components


def safe_dataframe(df: pd.DataFrame, max_rows: int = 200, height: int = 420):
    if df is None:
        st.warning("No dataset loaded.")
        return
    if not isinstance(df, pd.DataFrame):
        st.error("Object is not a DataFrame.")
        return
    if df.empty:
        st.info("Dataset contains no rows.")
        return

    preview = df.head(max_rows).copy().reset_index(drop=True)

    # Normalise every column to a safe string
    for col in preview.columns:
        if pd.api.types.is_datetime64_any_dtype(preview[col]):
            preview[col] = preview[col].dt.strftime("%Y-%m-%d").fillna("")
        elif pd.api.types.is_float_dtype(preview[col]):
            preview[col] = preview[col].apply(
                lambda x: "" if pd.isna(x) else f"{x:,.4f}".rstrip("0").rstrip(".")
            )
        elif pd.api.types.is_integer_dtype(preview[col]):
            preview[col] = preview[col].apply(
                lambda x: "" if pd.isna(x) else f"{int(x):,}"
            )
        else:
            preview[col] = preview[col].apply(
                lambda x: str(x) if isinstance(x, (list, dict, np.ndarray)) else x
            )
            preview[col] = preview[col].fillna("").astype(str)

    # Build HTML table
    header = "<th>#</th>" + "".join(f"<th>{c}</th>" for c in preview.columns)
    rows = ""
    for i, (_, row) in enumerate(preview.iterrows()):
        bg = "#0f1117" if i % 2 == 0 else "#0a0d14"
        cells = f'<td class="idx">{i+1}</td>' + "".join(
            f"<td>{str(v)}</td>" for v in row
        )
        rows += f'<tr style="background:{bg}">{cells}</tr>'

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f1117;font-family:'JetBrains Mono','Courier New',monospace;font-size:11px;color:#dde1ec}}
.wrap{{overflow:auto;max-height:{height-30}px;border:1px solid #1a1f2e;border-radius:8px}}
table{{width:100%;border-collapse:collapse;background:#0f1117}}
thead tr{{background:#0a0d14!important;border-bottom:2px solid #1a1f2e;position:sticky;top:0;z-index:10}}
th{{padding:8px 12px;text-align:left;color:#00e5a0;font-size:10px;letter-spacing:.5px;white-space:nowrap;border-right:1px solid #1a1f2e}}
th:first-child{{color:#4a5568}}
td{{padding:6px 12px;border-right:1px solid #1a1f2e;border-bottom:1px solid #13161f;white-space:nowrap;max-width:220px;overflow:hidden;text-overflow:ellipsis}}
td.idx{{color:#4a5568;font-size:10px}}
tr:hover{{background:#161924!important}}
.info{{font-size:10px;color:#4a5568;padding:4px 2px}}
</style></head><body>
<div class="wrap"><table>
<thead><tr>{header}</tr></thead>
<tbody>{rows}</tbody>
</table></div>
<div class="info">Showing {min(max_rows,len(df)):,} of {len(df):,} rows &times; {len(df.columns)} columns</div>
</body></html>"""

    components.html(html, height=height, scrolling=False)