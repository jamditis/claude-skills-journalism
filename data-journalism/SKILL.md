---
name: data-journalism
description: Data journalism workflows for analysis, visualization, and storytelling. Use when analyzing datasets, creating charts and maps, cleaning messy data, calculating statistics, or building data-driven stories. Essential for reporters, newsrooms, and researchers working with quantitative information.
---

# Data journalism methodology

Systematic approaches for finding, analyzing, and presenting data in journalism.

## Data acquisition

### Public data sources

```markdown
## Federal data sources

### General
- Data.gov - Federal open data portal
- Census Bureau (census.gov) - Demographics, economic data
- BLS (bls.gov) - Employment, inflation, wages
- BEA (bea.gov) - GDP, economic accounts
- Federal Reserve (federalreserve.gov) - Financial data
- SEC EDGAR - Corporate filings

### Specific domains
- EPA (epa.gov/data) - Environmental data
- FDA (fda.gov/data) - Drug approvals, recalls, adverse events
- CDC WONDER - Health statistics
- NHTSA - Vehicle safety data
- DOT - Transportation statistics
- FEC - Campaign finance
- USASpending.gov - Federal contracts and grants

### State and local
- State open data portals (search: "[state] open data")
- Socrata-powered sites (many cities/states)
- OpenStreets, municipal GIS portals
- State comptroller/auditor reports
```

### Data request strategies

```markdown
## Getting data that isn't public

### FOIA for datasets
- Request databases, not just documents
- Ask for data dictionary/schema
- Request in native format (CSV, SQL dump)
- Specify field-level needs

### Building your own dataset
- Scraping public information
- Crowdsourcing from readers
- Systematic document review
- Surveys (with proper methodology)

### Commercial data sources (for newsrooms)
- LexisNexis
- Refinitiv
- Bloomberg
- Industry-specific databases
```

## Data cleaning and preparation

### Common data problems

```python
import pandas as pd
import numpy as np

# Load messy data
df = pd.read_csv('raw_data.csv')

# 1. INCONSISTENT FORMATTING
# Problem: Names in different formats
# "SMITH, JOHN" vs "John Smith" vs "smith john"

def standardize_name(name):
    """Standardize name format to 'First Last'."""
    if pd.isna(name):
        return None
    name = str(name).strip().lower()
    # Handle "LAST, FIRST" format
    if ',' in name:
        parts = name.split(',')
        name = f"{parts[1].strip()} {parts[0].strip()}"
    return name.title()

df['name_clean'] = df['name'].apply(standardize_name)


# 2. DATE INCONSISTENCIES
# Problem: Dates in multiple formats
# "01/15/2024", "2024-01-15", "January 15, 2024", "15-Jan-24"

def parse_date(date_str):
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

df['date_clean'] = df['date'].apply(parse_date)


# 3. MISSING VALUES
# Strategy depends on context

# Check missing value patterns
print(df.isnull().sum())
print(df.isnull().sum() / len(df) * 100)  # Percentage

# Options:
# - Drop rows with critical missing values
df_clean = df.dropna(subset=['required_field'])

# - Fill with appropriate values
df['category'] = df['category'].fillna('Unknown')
df['amount'] = df['amount'].fillna(df['amount'].median())

# - Flag as missing (preserve for analysis)
df['amount_missing'] = df['amount'].isna()


# 4. DUPLICATES
# Find and handle duplicates

# Exact duplicates
print(f"Exact duplicates: {df.duplicated().sum()}")
df = df.drop_duplicates()

# Fuzzy duplicates (similar but not identical)
# Use record linkage or manual review
from fuzzywuzzy import fuzz

def find_similar_names(names, threshold=85):
    """Find potentially duplicate names."""
    duplicates = []
    for i, name1 in enumerate(names):
        for j, name2 in enumerate(names[i+1:], i+1):
            score = fuzz.ratio(str(name1).lower(), str(name2).lower())
            if score >= threshold:
                duplicates.append((name1, name2, score))
    return duplicates


# 5. OUTLIERS
# Identify potential data entry errors

def flag_outliers(series, method='iqr', threshold=1.5):
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

df['amount_outlier'] = flag_outliers(df['amount'])
print(f"Outliers found: {df['amount_outlier'].sum()}")


# 6. DATA TYPE CORRECTIONS
# Ensure proper types for analysis

# Convert to numeric (handling errors)
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

# Convert to categorical (saves memory, enables ordering)
df['status'] = pd.Categorical(df['status'],
                              categories=['Pending', 'Active', 'Closed'],
                              ordered=True)

# Convert to datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')
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

## Statistical analysis for journalism

### Basic statistics with context

```python
# Essential statistics for any dataset
def describe_for_journalism(df, column):
    """Generate journalist-friendly statistics."""
    stats = {
        'count': len(df[column].dropna()),
        'missing': df[column].isna().sum(),
        'min': df[column].min(),
        'max': df[column].max(),
        'mean': df[column].mean(),
        'median': df[column].median(),
        'std': df[column].std(),
    }

    # Percentiles for context
    stats['25th_percentile'] = df[column].quantile(0.25)
    stats['75th_percentile'] = df[column].quantile(0.75)
    stats['90th_percentile'] = df[column].quantile(0.90)
    stats['99th_percentile'] = df[column].quantile(0.99)

    # Distribution shape
    stats['skewness'] = df[column].skew()

    return stats

# Example interpretation
stats = describe_for_journalism(df, 'salary')
print(f"""
SALARY ANALYSIS
---------------
We analyzed {stats['count']:,} salary records.

The median salary is ${stats['median']:,.0f}, meaning half of workers
earn more and half earn less.

The average salary is ${stats['mean']:,.0f}, which is
{'higher' if stats['mean'] > stats['median'] else 'lower'} than the median,
indicating the distribution is {'right-skewed (pulled up by high earners)'
if stats['skewness'] > 0 else 'left-skewed'}.

The top 10% of earners make at least ${stats['90th_percentile']:,.0f}.
The top 1% make at least ${stats['99th_percentile']:,.0f}.
""")
```

### Comparisons and context

```python
# Year-over-year change
def calculate_change(current, previous):
    """Calculate change with multiple metrics."""
    absolute = current - previous
    if previous != 0:
        percent = (current - previous) / previous * 100
    else:
        percent = float('inf') if current > 0 else 0

    return {
        'current': current,
        'previous': previous,
        'absolute_change': absolute,
        'percent_change': percent,
        'direction': 'increased' if absolute > 0 else 'decreased' if absolute < 0 else 'unchanged'
    }

# Per capita calculations (essential for fair comparisons)
def per_capita(value, population):
    """Calculate per capita rate."""
    return (value / population) * 100000  # Per 100,000 is standard

# Example: Crime rates
city_a = {'crimes': 5000, 'population': 100000}
city_b = {'crimes': 8000, 'population': 500000}

rate_a = per_capita(city_a['crimes'], city_a['population'])
rate_b = per_capita(city_b['crimes'], city_b['population'])

print(f"City A: {rate_a:.1f} crimes per 100,000 residents")
print(f"City B: {rate_b:.1f} crimes per 100,000 residents")
# City A actually has higher crime rate despite fewer total crimes!


# Inflation adjustment
def adjust_for_inflation(amount, from_year, to_year, cpi_data):
    """Adjust dollar amounts for inflation."""
    from_cpi = cpi_data[from_year]
    to_cpi = cpi_data[to_year]
    return amount * (to_cpi / from_cpi)

# Always adjust when comparing dollars across years!
```

### Correlation vs causation

```markdown
## Reporting correlations responsibly

### What you CAN say
- "X and Y are correlated"
- "As X increases, Y tends to increase"
- "Areas with higher X also tend to have higher Y"
- "X is associated with Y"

### What you CANNOT say (without more evidence)
- "X causes Y"
- "X leads to Y"
- "Y happens because of X"

### Questions to ask before implying causation
1. Is there a plausible mechanism?
2. Does the timing make sense (cause before effect)?
3. Is there a dose-response relationship?
4. Has the finding been replicated?
5. Have confounding variables been controlled?
6. Are there alternative explanations?

### Red flags for spurious correlations
- Extremely high correlation (r > 0.95) with unrelated things
- No logical connection between variables
- Third variable could explain both
- Small sample size with high variance
```

## Data visualization

### Chart selection guide

```markdown
## Choosing the right chart

### Comparison
- **Bar chart**: Compare categories
- **Grouped bar**: Compare categories across groups
- **Bullet chart**: Actual vs target

### Change over time
- **Line chart**: Trends over time
- **Area chart**: Cumulative totals over time
- **Slope chart**: Change between two points

### Distribution
- **Histogram**: Distribution of one variable
- **Box plot**: Compare distributions across groups
- **Violin plot**: Detailed distribution shape

### Relationship
- **Scatter plot**: Relationship between two variables
- **Bubble chart**: Three variables (x, y, size)
- **Connected scatter**: Change in relationship over time

### Composition
- **Pie chart**: Parts of a whole (use sparingly, max 5 slices)
- **Stacked bar**: Parts of whole across categories
- **Treemap**: Hierarchical composition

### Geographic
- **Choropleth**: Values by region (use normalized data!)
- **Dot map**: Individual locations
- **Proportional symbol**: Magnitude at locations
```

### Visualization best practices

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Journalist-friendly chart defaults
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 12,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

def create_bar_chart(data, title, source, xlabel='', ylabel=''):
    """Create a publication-ready bar chart."""
    fig, ax = plt.subplots()

    # Create bars
    bars = ax.bar(data.keys(), data.values(), color='#2c7bb6')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    ha='center', va='bottom',
                    fontsize=10)

    # Labels and title
    ax.set_title(title, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Add source annotation
    fig.text(0.99, 0.01, f'Source: {source}',
             ha='right', va='bottom', fontsize=9, color='gray')

    plt.tight_layout()
    return fig

# Example
data = {'2020': 1200, '2021': 1450, '2022': 1380, '2023': 1620}
fig = create_bar_chart(data,
                       'Annual Widget Production',
                       'Department of Widgets, 2024',
                       ylabel='Units produced')
fig.savefig('chart.png', dpi=150, bbox_inches='tight')
```

### Avoiding misleading visualizations

```markdown
## Chart integrity checklist

### Axes
- [ ] Y-axis starts at zero (for bar charts)
- [ ] Axis labels are clear
- [ ] Scale is appropriate (not truncated to exaggerate)
- [ ] Both axes labeled with units

### Data representation
- [ ] All data points visible
- [ ] Colors are distinguishable (including colorblind)
- [ ] Proportions are accurate
- [ ] 3D effects not distorting perception

### Context
- [ ] Title describes what's shown, not conclusion
- [ ] Time period clearly stated
- [ ] Source cited
- [ ] Sample size/methodology noted if relevant
- [ ] Uncertainty shown where appropriate

### Honesty
- [ ] Cherry-picking dates avoided
- [ ] Outliers explained, not hidden
- [ ] Dual axes justified (usually avoid)
- [ ] Annotations don't mislead
```

## Story structure for data journalism

### Data story framework

```markdown
## The data story arc

### 1. The hook (nut graf)
- What's the key finding?
- Why should readers care?
- What's the human impact?

### 2. The evidence
- Show the data
- Explain the methodology
- Acknowledge limitations

### 3. The context
- How does this compare to past?
- How does this compare to elsewhere?
- What's the trend?

### 4. The human element
- Individual examples that illustrate the data
- Expert interpretation
- Affected voices

### 5. The implications
- What does this mean going forward?
- What questions remain?
- What actions could result?

### 6. The methodology box
- Where did data come from?
- How was it analyzed?
- What are the limitations?
- How can readers explore further?
```

### Methodology documentation template

```markdown
## How we did this analysis

### Data sources
[List all data sources with links and access dates]

### Time period
[Specify exactly what time period is covered]

### Definitions
[Define key terms and how you operationalized them]

### Analysis steps
1. [First step of analysis]
2. [Second step]
3. [Continue...]

### Limitations
- [Limitation 1]
- [Limitation 2]

### What we excluded and why
- [Excluded category]: [Reason]

### Verification
[How findings were verified/checked]

### Code and data availability
[Link to GitHub repo if sharing code/data]

### Contact
[How readers can reach you with questions]
```

## Tools and resources

### Essential tools

| Tool | Purpose | Cost |
|------|---------|------|
| Python + pandas | Data analysis | Free |
| R + tidyverse | Statistical analysis | Free |
| Excel/Sheets | Quick analysis | Free/Low |
| Datawrapper | Charts for web | Free tier |
| Flourish | Interactive viz | Free tier |
| QGIS | Mapping | Free |
| Tabula | PDF table extraction | Free |
| OpenRefine | Data cleaning | Free |

### Learning resources

- NICAR (Investigative Reporters & Editors)
- Knight Center for Journalism in the Americas
- Data Journalism Handbook (datajournalism.com)
- Flowing Data (flowingdata.com)
- The Pudding (pudding.cool) - examples
