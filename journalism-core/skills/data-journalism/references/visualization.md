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
- **Pie chart**: Parts of a whole (almost never use, max 5 slices, prefer donut charts)
- **Donut chart**: Parts of a whole
- **Stacked bar**: Parts of whole across categories
- **Treemap**: Hierarchical composition

### Geographic
- **Choropleth**: Values by region (use normalized data!)
- **Dot map**: Individual locations
- **Proportional symbol**: Magnitude at locations
```

### Exploratory interactive visualizations with Plotly Express

```python
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set default template for all charts
px.defaults.template = 'simple_white'

def create_bar_chart(
    data: pd.DataFrame,
    title: str,
    source: str,
    x_val: str,
    y_val: str,
    x_lab: str | None = None,
    y_lab: str | None = None,
    text_col: str | None = None,
) -> go.Figure:
    """Create a bar chart with a source-credit footer."""
    fig = px.bar(
        data,
        x=x_val,
        y=y_val,
        text=text_col,
        title=title,
        labels={x_val: x_lab or x_val, y_val: y_lab or y_val},
    )
    fig.add_annotation(
        text=f"Source: {source}",
        showarrow=False,
        xref='paper', yref='paper',
        x=0, y=-0.15,
        xanchor='left', yanchor='top',
        font=dict(size=10, color='gray'),
    )
    return fig

# Example
fig = create_bar_chart(
    data,
    title='Annual widget production',
    source='Department of Widgets, 2024',
    x_val='year',
    y_val='widgets_prod',
    x_lab='Year',
    y_lab='Units produced',
)

fig.show()  # Interactive display
```

### Publication-ready automated data visualizations with Datawrapper
```python
import pandas as pd
import datawrapper as dw

# Authentication: Set DATAWRAPPER_ACCESS_TOKEN environment variable,
# or read from file and pass to create()
with open('datawrapper_api_key.txt', 'r') as f:
    api_key = f.read().strip()

# read in your data
data = pd.read_csv('../data/raw/data.csv')

# Create a bar chart using the new OOP API
chart = dw.BarChart(
    title='My Bar Chart Title',
    intro='Subtitle or description text',
    data=data,

    # Formatting options
    value_label_format=dw.NumberFormat.ONE_DECIMAL,
    show_value_labels=True,
    value_label_alignment='left',
    sort_bars=True,  # sort by value
    reverse_order=False,

    # Source attribution
    source_name='Your Data Source',
    source_url='https://example.com',
    byline='Your Name',

    # Optional: custom base color
    base_color='#1d81a2'
)

# Create and publish (uses DATAWRAPPER_ACCESS_TOKEN env var, or pass token)
chart.create(access_token=api_key)
chart.publish()

# Get chart URL and embed code
print(f"Chart ID: {chart.chart_id}")
print(f"Chart URL: https://datawrapper.dwcdn.net/{chart.chart_id}")
iframe_code = chart.get_iframe_code(responsive=True)

# Update existing chart with new data (for live-updating charts)
existing_chart = dw.get_chart('YOUR_CHART_ID')  # retrieve by ID
existing_chart.data = new_df  # assign new DataFrame
existing_chart.title = 'Updated Title'  # modify properties
existing_chart.update()  # push changes to Datawrapper
existing_chart.publish()  # republish to make live

# Optional, Export chart as image
chart.export(filepath='chart.png', width=800, height=600)

#view chart
chart
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
