## Data cleaning and preparation

### Common data problems

```python
from typing import Any

import pandas as pd
import numpy as np
from rapidfuzz import fuzz
from itertools import combinations

# Inflation adjustment
import cpi
import wbdata

def standardize_name(name: Any) -> str | None:
    """Standardize name format to 'First Last'."""
    if pd.isna(name):
        return None
    name = str(name).strip().upper()
    # Handle "LAST, FIRST" format
    if ',' in name:
        parts = name.split(',')
        name = f"{parts[1].strip()} {parts[0].strip()}"
    return name

def parse_date(date_str: Any) -> pd.Timestamp | None:
    """Parse dates in various formats."""
    if pd.isna(date_str):
        return None

    formats = [
        '%m/%d/%Y', '%Y-%m-%d', '%B %d, %Y',
        '%d-%b-%y', '%m-%d-%Y', '%Y/%m/%d'
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue

    # Fall back to pandas parser
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def handle_missing(
    df: pd.DataFrame,
    thresh: int | None = None,
    per_thresh: float | None = None,
    required_col: str | None = None,
) -> pd.DataFrame:
    """Drop rows missing values in `required_col` if missingness exceeds either threshold."""
    if required_col is None or df.empty:
        return df
    if required_col not in df.columns:
        return df

    missing = df[required_col].isna().sum()

    if thresh is not None and missing >= thresh:
        return df.dropna(subset=[required_col]).reset_index(drop=True).copy()

    if per_thresh is not None and (missing / len(df) * 100) >= per_thresh:
        return df.dropna(subset=[required_col]).reset_index(drop=True).copy()

    return df


def handle_duplicates(df: pd.DataFrame, thresh: int | None = None) -> pd.DataFrame:
    """Drop duplicate rows when count exceeds `thresh`."""
    if thresh is not None and df.duplicated().sum() >= thresh:
        return df.drop_duplicates().reset_index(drop=True).copy()
    return df


def flag_similar_names(df: pd.DataFrame, name_col: str, threshold: int = 85) -> pd.DataFrame:
    """Flag rows that have potential duplicate names using vectorized comparison."""

    names = df[name_col].dropna().unique()

    # Use combinations() to avoid nested loop and duplicate comparisons
    dup_names: set[Any] = {
        name
        for name1, name2 in combinations(names, 2)
        if fuzz.ratio(str(name1).lower(), str(name2).lower()) >= threshold
        for name in (name1, name2)
    }

    df['has_similar_name'] = df[name_col].isin(dup_names)
    return df


def flag_outliers(series: pd.Series, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
    """Flag statistical outliers."""
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - threshold * IQR
        upper = Q3 + threshold * IQR
        return (series < lower) | (series > upper)
    elif method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold



# use descriptive variable names and chain methods
data_clean = (pd

            # Load messy data, raw_data is a placeholder
            # Be sure to use the right reader for the filetype
            .read_csv('..data/raw/raw_data.csv')

            # DATA TYPE CORRECTIONS
            # Ensure proper types for analysis
            .assign(# Convert to numeric (handling errors)
                    amount = lambda x: pd.to_numeric(x['amount'], errors='coerce'),

                    # Convert to categorical (saves memory, enables ordering)
                    status = lambda x: pd.Categorical(x['status']))

            .assign(
                    # INCONSISTENT FORMATTING
                    # Problem: Names in different formats
                    # e.g., "SMITH, JOHN" vs "John Smith" vs "smith john"
                    name_clean = lambda x: standardize_name(x['name']),

                    # DATE INCONSISTENCIES
                    # Problem: Dates in multiple formats
                    # e.g., "01/15/2024", "2024-01-15", "January 15, 2024", "15-Jan-24"
                    parse_date = lambda x: parse_date(x['date']),

                    # OUTLIERS
                    # Identify potential data entry errors
                    amount_outlier = lambda x: flag_outliers(x['amount']),

                    )

            # Fuzzy duplicates (similar but not identical)
            # Use record linkage or manual review
            .pipe(flag_similar_names, name_col='name_clean', threshold=85)

            # MISSING VALUES
            # Strategy depends on context, set required_col when you need to drop incomplete rows
            .pipe(handle_missing, required_col='amount', per_thresh=20.0)

            # DUPLICATES, Find and handle duplicates
            .pipe(handle_duplicates, thresh=1)

            .reset_index(drop=True)
            .copy())


```

### Data validation checklist

```markdown
## Pre-analysis data validation

### Structural checks
- [ ] Row count matches expected
- [ ] Column count and names correct
- [ ] Data types appropriate
- [ ] No unexpected null columns

### Content checks
- [ ] Date ranges make sense
- [ ] Numeric values within expected bounds
- [ ] Categorical values match expected options
- [ ] Geographic data resolves correctly
- [ ] IDs are unique where expected

### Consistency checks
- [ ] Totals add up to expected values
- [ ] Cross-tabulations balance
- [ ] Related fields are consistent
- [ ] Time series is continuous

### Source verification
- [ ] Can trace back to original source
- [ ] Methodology documented
- [ ] Known limitations noted
- [ ] Update frequency understood
```

## AI-assisted analysis: cautions

AI tools can speed up exploration, code generation, and pattern surfacing, but they have specific failure modes that journalists must guard against. *Mata v. Avianca* (2023, fabricated court citations sanctioned in federal court) and the Air Canada chatbot ruling (2024, hallucinated refund policy ruled binding on the airline) are the canonical cases of LLM fabrication treated as published fact.

### What LLMs reliably get wrong

- **Calculations at scale**, A model may produce a confident-looking sum, percentage, or rate that's off by 1-15%. Re-run any LLM-produced number in pandas, SQL, or R yourself before publishing.
- **Source citations**, Models hallucinate plausible URLs, paper titles, dataset names, and FOIA exemptions that don't exist. Verify every cited source by visiting it.
- **Dataset columns**, When asked to describe a dataset's structure, an LLM may invent columns that aren't there. Cross-check against the actual schema (`df.dtypes`, `df.columns.tolist()`).
- **Statistical reasoning**, LLMs confuse correlation with causation, conflate sample statistics with population parameters, and misapply tests. Treat any analytical claim as a hypothesis to verify, not a finding.

### Methodology disclosure

When AI was used in any stage (data cleaning, analysis, visualization, drafting), disclose it in the methodology box. Editors and readers need to know which steps had a human in the loop and which were automated.

- State the tool and version (e.g., "We used Claude 4.7 to draft the cleaning pipeline; the code was reviewed and run by [reporter]").
- State what was verified (e.g., "All numerical results were re-computed in pandas; all source citations were independently confirmed").
- State what was not verified (if relevant).

### Reproducibility

When using AI to generate analysis code, save the prompt, the model name, and the version alongside the code. AI-generated code is part of your methodology and should be reproducible by another reporter on the same data.
