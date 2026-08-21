## Statistical analysis for journalism

### Basic statistics with context

```python
import cpi
import numpy as np
import pandas as pd
import wbdata

# Essential statistics for any dataset
def describe_for_journalism(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Generate journalist-friendly statistics."""
    stats = df[col].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99])

    # Add skewness to the describe() output
    stats['skewness'] = df[col].skew()

    return stats.to_frame(name=col)

# Example interpretation
stats = describe_for_journalism(salaries, 'salary')

print(f"""
ANALYSIS
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
# Calculate change metrics for a column
def calculate_change(df: pd.DataFrame, col: str, periods: int = 1) -> pd.DataFrame:
    """Add change metrics to a DataFrame using built-in pandas methods.

    Args:
        df: Input DataFrame
        col: Column to calculate changes for
        periods: Number of rows to look back (1=previous row, 12=year-over-year for monthly)
    """
    return df.assign(
        absolute_change=df[col].diff(periods),
        percent_change=df[col].pct_change(periods) * 100,
        direction=np.sign(df[col].diff(periods)).map({1: 'increased', -1: 'decreased', 0: 'unchanged'})
    )

# Usage:
# changes = data_clean.pipe(calculate_change, 'revenue', periods=12) # Year-over-year for monthly data

# Per capita calculations (essential for fair comparisons)
def per_capita(value: float, population: float, multiplier: int = 100000) -> float:
    """Calculate per capita rate."""
    return (value / population) * multiplier  # Per 100,000 is standard

# Example: Crime rates
city_a = {'crimes': 5000, 'population': 100000}
city_b = {'crimes': 8000, 'population': 500000}

rate_a = per_capita(city_a['crimes'], city_a['population'])
rate_b = per_capita(city_b['crimes'], city_b['population'])

print(f"City A: {rate_a:.1f} crimes per 100,000 residents")
print(f"City B: {rate_b:.1f} crimes per 100,000 residents")
# City A actually has higher crime rate despite fewer total crimes!


def adjust_for_inflation(
    amount: float | pd.Series,
    from_year: int | pd.Series,
    to_year: int,
    country: str = 'US'
) -> float | pd.Series:
    """Adjust dollar amounts for inflation. Works with scalars or Series for .assign().

    Args:
        amount: Value(s) to adjust
        from_year: Original year(s) of the amount
        to_year: Target year to adjust to
        country: ISO 2-letter country code (default 'US'). US uses BLS data via cpi package,
                 others use World Bank CPI data (FP.CPI.TOTL indicator)
    """
    if country == 'US':
        # Use cpi package for US (more accurate, from BLS)
        if isinstance(from_year, pd.Series):
            return pd.Series([cpi.inflate(amt, yr, to=to_year)
                            for amt, yr in zip(amount, from_year)], index=amount.index)
        return cpi.inflate(amount, from_year, to=to_year)
    else:
        # Use World Bank data for other countries
        cpi_data = wbdata.get_dataframe(
            {'FP.CPI.TOTL': 'cpi'},
            country=country
        )['cpi'].to_dict()

        from_cpi = pd.Series(from_year).map(cpi_data) if isinstance(from_year, pd.Series) else cpi_data[from_year]
        to_cpi = cpi_data[to_year]
        return amount * (to_cpi / from_cpi)

# Usage:
# adjust_for_inflation(100, 2020, 2024)  # US by default
# adjust_for_inflation(100, 2020, 2024, country='GB')  # UK
# df.assign(inf_adjust24=lambda x: adjust_for_inflation(x['amount'], x['year'], 2024, country='DE'))

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
