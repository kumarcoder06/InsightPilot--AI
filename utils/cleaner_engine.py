"""
utils/cleaner_engine.py
────────────────────────
Professional data cleaning pipeline using Pandas + NumPy.
Mimics a senior data analyst's ETL workflow:
  1. Audit raw data
  2. Fix dtypes
  3. Handle duplicates
  4. Handle missing values (smart imputation)
  5. Fix string / categorical inconsistencies
  6. Detect & cap outliers (IQR method)
  7. Standardise column names
  8. Generate a full cleaning report
"""

from __future__ import annotations
import re
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Optional


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class CleaningStep:
    category: str        # e.g. "Missing Values", "Duplicates"
    column:   str | None # None = whole-dataset operation
    action:   str        # what was done
    detail:   str        # human-readable detail
    before:   Any = None
    after:    Any = None
    severity: str = "info"   # info | warning | fixed | removed


@dataclass
class AuditReport:
    shape_raw:         tuple
    shape_clean:       tuple
    missing_summary:   pd.DataFrame
    duplicate_count:   int
    dtype_issues:      list[str]
    outlier_summary:   dict
    steps:             list[CleaningStep] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snake(name: str) -> str:
    """Convert column name to snake_case."""
    name = str(name).strip()
    name = re.sub(r'[\s\-\.]+', '_', name)
    name = re.sub(r'[^\w]', '', name)
    name = re.sub(r'_+', '_', name)
    return name.lower().strip('_')


def _is_numeric_string(series: pd.Series) -> bool:
    """Check if an object column actually holds numbers."""
    sample = series.dropna().head(200).astype(str)
    cleaned = sample.str.replace(r'[\$,€£%\s]', '', regex=True)
    converted = pd.to_numeric(cleaned, errors='coerce')
    # Consider numeric if >90% of non-null values parse successfully
    return converted.notna().mean() > 0.90


def _is_date_string(series: pd.Series) -> bool:
    """Quick heuristic: does column name or values look like dates?"""
    name_hints = ['date', 'time', 'dt', 'day', 'month', 'year', 'created', 'updated', 'at']
    col = series.name.lower() if series.name else ''
    if any(h in col for h in name_hints):
        return True
    sample = series.dropna().astype(str).head(30)
    date_pattern = re.compile(r'\d{2,4}[-/\.]\d{1,2}[-/\.]\d{1,4}')
    return sample.apply(lambda x: bool(date_pattern.search(x))).mean() > 0.6


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def clean_dataframe(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, AuditReport]:
    """
    Full cleaning pipeline. Returns (cleaned_df, audit_report).
    Non-destructive: works on a copy.
    """
    df = df_raw.copy()
    steps: list[CleaningStep] = []

    # ── 0. Standardise column names ───────────────────────────────────────────
    original_cols = df.columns.tolist()
    df.columns = [_snake(c) for c in df.columns]
    renamed = [(o, n) for o, n in zip(original_cols, df.columns.tolist()) if o != n]
    if renamed:
        for o, n in renamed:
            steps.append(CleaningStep(
                "Column Names", None,
                f'Renamed "{o}" → "{n}"',
                "Standardised to snake_case", severity="fixed"
            ))

    # ── 1. Remove fully empty rows/columns ────────────────────────────────────
    before_rows = df.shape[0]
    df = df.dropna(how='all')
    dropped_rows = before_rows - df.shape[0]
    if dropped_rows:
        steps.append(CleaningStep("Empty Data", None,
            f"Removed {dropped_rows} fully-empty rows",
            f"{dropped_rows} rows had no data at all", severity="removed"))

    before_cols = df.shape[1]
    df = df.dropna(axis=1, how='all')
    dropped_cols = before_cols - df.shape[1]
    if dropped_cols:
        steps.append(CleaningStep("Empty Data", None,
            f"Removed {dropped_cols} fully-empty columns",
            "Columns with zero non-null values dropped", severity="removed"))

    # ── 2. Duplicates ─────────────────────────────────────────────────────────
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        steps.append(CleaningStep("Duplicates", None,
            f"Removed {dup_count} duplicate rows",
            f"{dup_count} exact-duplicate rows detected and removed",
            before=dup_count, after=0, severity="removed"))

    # ── 3. Fix data types ─────────────────────────────────────────────────────
    dtype_issues = []
    for col in df.columns:
        if df[col].dtype == object:
            # Try numeric
            if _is_numeric_string(df[col]):
                cleaned_series = df[col].astype(str)\
                    .str.replace(r'[\$,€£%\s]', '', regex=True)\
                    .str.strip()
                converted = pd.to_numeric(cleaned_series, errors='coerce')
                null_increase = converted.isna().sum() - df[col].isna().sum()
                if null_increase / max(len(df), 1) < 0.05:   # allow <5% new nulls
                    old_dtype = str(df[col].dtype)
                    df[col] = converted
                    steps.append(CleaningStep("Data Types", col,
                        f'Converted "{col}" object → numeric',
                        f"Detected numeric strings (e.g. $1,234 → 1234)",
                        before=old_dtype, after=str(df[col].dtype), severity="fixed"))
                    dtype_issues.append(col)
            # Try datetime
            elif _is_date_string(df[col]):
                try:
                    converted = pd.to_datetime(df[col], errors='coerce')
                    parse_rate = converted.notna().sum() / max(df[col].notna().sum(), 1)
                    if parse_rate > 0.8:
                        df[col] = converted
                        steps.append(CleaningStep("Data Types", col,
                            f'Converted "{col}" → datetime',
                            f"Parse success rate: {parse_rate:.0%}",
                            before="object", after="datetime64", severity="fixed"))
                except Exception:
                    pass

    # ── 4. Strip whitespace from string columns ────────────────────────────────
    for col in df.select_dtypes(include='object').columns:
        before_nulls = df[col].isna().sum()
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'nan': np.nan, 'None': np.nan, 'NULL': np.nan,
                                    'null': np.nan, 'N/A': np.nan, 'n/a': np.nan,
                                    'NA': np.nan, '#N/A': np.nan, '': np.nan})
        after_nulls = df[col].isna().sum()
        if after_nulls != before_nulls:
            steps.append(CleaningStep("String Cleaning", col,
                f'Standardised {after_nulls - before_nulls} pseudo-null strings → NaN',
                'Values like "NULL", "N/A", "" replaced with proper NaN',
                severity="fixed"))

    # ── 5. Standardise categorical text ───────────────────────────────────────
    for col in df.select_dtypes(include='object').columns:
        if df[col].nunique() < 30:   # likely categorical
            original = df[col].copy()
            df[col] = df[col].str.lower().str.strip()
            # Title-case for names / categories
            if any(h in col for h in ['name','status','category','type','gender','country','city']):
                df[col] = df[col].str.title()
            changed = (original != df[col]).sum()
            if changed > 0:
                steps.append(CleaningStep("Categorical", col,
                    f'Normalised casing for {changed} values in "{col}"',
                    "Inconsistent casing standardised (e.g. 'ACTIVE' → 'Active')",
                    severity="fixed"))

    # ── 6. Missing value imputation ───────────────────────────────────────────
    for col in df.columns:
        null_count = df[col].isna().sum()
        if null_count == 0:
            continue
        null_pct = null_count / len(df)

        if null_pct > 0.60:
            # Too many nulls — flag for user, don't impute
            steps.append(CleaningStep("Missing Values", col,
                f'⚠ "{col}" has {null_pct:.0%} nulls — flagged, not imputed',
                "High null ratio. Manual review recommended.",
                before=null_count, severity="warning"))
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            skewness = df[col].skew()
            if abs(skewness) > 1.0:
                fill_val = df[col].median()
                method = "median (skewed distribution)"
            else:
                fill_val = df[col].mean()
                method = "mean (normal distribution)"
            df[col] = df[col].fillna(fill_val)
            steps.append(CleaningStep("Missing Values", col,
                f'Imputed {null_count} nulls in "{col}" with {method}',
                f"Fill value: {fill_val:.4g}  |  Skewness: {skewness:.2f}",
                before=null_count, after=0, severity="fixed"))

        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            fill_val = df[col].median()
            df[col] = df[col].fillna(fill_val)
            steps.append(CleaningStep("Missing Values", col,
                f'Imputed {null_count} datetime nulls with median date',
                f"Median: {fill_val}", before=null_count, after=0, severity="fixed"))

        else:
            fill_val = df[col].mode()[0] if len(df[col].mode()) > 0 else "Unknown"
            df[col] = df[col].fillna(fill_val)
            steps.append(CleaningStep("Missing Values", col,
                f'Imputed {null_count} nulls in "{col}" with mode',
                f'Most frequent value: "{fill_val}"',
                before=null_count, after=0, severity="fixed"))

    # ── 7. Outlier detection & capping (IQR method) ───────────────────────────
    outlier_summary = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 3.0 * IQR   # use 3× IQR (conservative)
        upper = Q3 + 3.0 * IQR
        outliers = ((df[col] < lower) | (df[col] > upper)).sum()
        if outliers > 0:
            df[col] = df[col].clip(lower=lower, upper=upper)
            outlier_summary[col] = {"count": int(outliers), "lower": lower, "upper": upper}
            steps.append(CleaningStep("Outliers", col,
                f'Capped {outliers} outliers in "{col}" (IQR×3)',
                f"Bounds: [{lower:.4g}, {upper:.4g}]",
                before=outliers, after=0, severity="fixed"))

    # ── 8. Reset index ────────────────────────────────────────────────────────
    df = df.reset_index(drop=True)

    # ── Build audit ───────────────────────────────────────────────────────────
    missing_summary = pd.DataFrame({
        "column":    df.columns,
        "dtype":     [str(df[c].dtype) for c in df.columns],
        "null_count":[df[c].isna().sum() for c in df.columns],
        "null_pct":  [(df[c].isna().sum() / len(df) * 100).round(2) for c in df.columns],
        "nunique":   [df[c].nunique() for c in df.columns],
    })

    audit = AuditReport(
        shape_raw         = df_raw.shape,
        shape_clean       = df.shape,
        missing_summary   = missing_summary,
        duplicate_count   = dup_count,
        dtype_issues      = dtype_issues,
        outlier_summary   = outlier_summary,
        steps             = steps,
    )
    return df, audit