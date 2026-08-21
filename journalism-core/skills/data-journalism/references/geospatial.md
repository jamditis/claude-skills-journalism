## Working with geospatial data

### Geocoding data

#### U.S. Census Geocoder

**Best for:** U.S. addresses only. Returns Census geography (tract, block, FIPS codes) along with coordinates, essential for joining with Census demographic data.

**Pros:** Completely free with no API key required. Returns Census geographies (state/county FIPS, tract, block) that let you join with ACS/decennial Census data. Good match rates for standard U.S. addresses.

**Cons:** Limited to 10,000 addresses per batch. U.S. addresses only. Slower than commercial alternatives. Lower match rates for non-standard addresses (PO boxes, rural routes, new construction).

**Use when:** You need to geocode nicely formatted U.S. addresses or you don't have budget for a paid service.

```python
# pip install censusgeocode
# (the older `censusbatchgeocoder` package on PyPI hasn't been updated since 2017
# and is unmaintained, use `censusgeocode` instead, which wraps the same Census
# batch endpoint and is actively maintained.)

import censusgeocode as cg
import pandas as pd

# DataFrame must have columns matching the *_col parameters below
# (defaults: id, address, city, state, zipcode). If your CSV uses
# different names like 'street' or 'zip', pass them via address_col=,
# zipcode_col=, etc. internally these are renamed to the keys the
# Census API expects ('address', 'zip', etc.) before the request.
# (state and zipcode are optional but improve match rates)

def census_geocode(
    df: pd.DataFrame,
    id_col: str = 'id',
    address_col: str = 'address',
    city_col: str = 'city',
    state_col: str = 'state',
    zipcode_col: str = 'zipcode',
    chunk_size: int = 9999,
) -> pd.DataFrame:
    """
    Geocode a DataFrame using the U.S. Census batch geocoder.
    Automatically handles datasets larger than 10,000 rows by chunking.

    Returns DataFrame with the documented batch-endpoint fields:
        id, address, match, matchtype, parsed, tigerlineid, side, lat, lon

    The batch endpoint does not return state/county/tract FIPS codes.
    For census-geography output, use the per-address helper below
    (`cg.onelineaddress(addr, returntype='geographies')`) on the matched
    rows, or call `cg.address(...)` per row.
    """
    col_map = {id_col: 'id', address_col: 'address', city_col: 'city'}
    if state_col and state_col in df.columns:
        col_map[state_col] = 'state'
    if zipcode_col and zipcode_col in df.columns:
        col_map[zipcode_col] = 'zip'

    renamed_df = df.rename(columns=col_map)
    records = renamed_df.to_dict('records')

    if len(records) <= chunk_size:
        return pd.DataFrame(cg.addressbatch(records))

    all_results = []
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        print(f"Geocoding rows {i:,} to {i + len(chunk):,} of {len(records):,}...")
        try:
            all_results.extend(cg.addressbatch(chunk))
        except Exception as e:
            print(f"Error on chunk starting at {i}: {e}")
            for record in chunk:
                all_results.append({**record, 'match': False, 'lat': None, 'lon': None})

    return pd.DataFrame(all_results)

# Usage:
geocoded = (pd
              .read_csv('../data/raw/addresses.csv')
              .assign(id=lambda x: x.index)
              .pipe(census_geocode,
                    id_col='id',
                    address_col='street',
                    city_col='city',
                    state_col='state',
                    zipcode_col='zip'))

# Follow-up per-address lookup for census geographies (state/county/tract FIPS).
# The batch endpoint above does not return these, only lat/lon and match status.
def add_geographies(geocoded: pd.DataFrame) -> pd.DataFrame:
    """For each matched row, fetch census-geography FIPS via per-address API."""
    fips_rows = []
    for row in geocoded[geocoded['match']].itertuples():
        try:
            geo = cg.onelineaddress(row.address, returntype='geographies')
            block = geo[0]['geographies']['Census Blocks'][0]
            fips_rows.append({
                'id': row.id,
                'state_fips': block['STATE'],
                'county_fips': block['COUNTY'],
                'tract': block['TRACT'],
                'block': block['BLOCK'],
            })
        except (IndexError, KeyError):
            continue
    return geocoded.merge(pd.DataFrame(fips_rows), on='id', how='left')
```

#### Google Maps Geocoder

**Best for:** International addresses, high match rates, and messy/non-standard address formats.

**Pros:** Excellent match rates even for poorly formatted addresses. Works worldwide. Fast and reliable. Returns rich metadata (place types, address components, place IDs).

**Cons:** Costs money ($5 per 1,000 requests after free tier). Requires API key and billing account. Does not return Census geography, you'd need to do a separate spatial join.

**Use when:** You need to geocode international addresses, have messy address data that the Census geocoder can't match, or need the highest possible match rate and have budget for it.

```python
import googlemaps
from typing import Optional

def geocode_address_google(address: str, api_key: str) -> Optional[dict]:
    """
    Geocode address using Google Maps API.
    Requires API key with Geocoding API enabled.
    """
    gmaps = googlemaps.Client(key=api_key)
    result = gmaps.geocode(address)

    if result:
        location = result[0]['geometry']['location']
        return {
            'formatted_address': result[0]['formatted_address'],
            'lat': location['lat'],
            'lon': location['lng'],
            'place_id': result[0]['place_id']
        }
    return None

# Batch geocode a DataFrame
def batch_geocode(df: pd.DataFrame, address_col: str, api_key: str) -> pd.DataFrame:
    gmaps = googlemaps.Client(key=api_key)

    results = []
    for address in df[address_col]:
        try:
            result = gmaps.geocode(address)
            if result:
                loc = result[0]['geometry']['location']
                results.append({'lat': loc['lat'], 'lon': loc['lng']})
            else:
                results.append({'lat': None, 'lon': None})
        except Exception:
            results.append({'lat': None, 'lon': None})

    return pd.concat([df, pd.DataFrame(results)], axis=1)
```

### Geopandas
```python
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Read data from various formats
gdf = gpd.read_file('data.geojson')                    # GeoJSON
gdf = gpd.read_file('data.shp')                         # Shapefile
gdf = gpd.read_file('https://example.com/data.geojson') # From URL
gdf = gpd.read_parquet('data.parquet')                  # GeoParquet (fast!)

# Transform DataFrame with lat/lon to GeoDataFrame
df = pd.read_csv('locations.csv')
geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry)

# Set CRS (Coordinate Reference System)
# EPSG:4326 = WGS84 (standard latitude, longitude)
gdf = gdf.set_crs('EPSG:4326')

# Transform to different CRS (for area/distance calculations, use projected CRS)
gdf_projected = gdf.to_crs('EPSG:3857')  # Web Mercator, for distance in meters

# Basic spatial operations

#Find the area of a shape
gdf['area'] = gdf_projected.geometry.area

#Find the center of a shape
gdf['centroid'] = gdf.geometry.centroid

#Draw a 1km boundary around a point
gdf['buffer_1km'] = gdf_projected.geometry.buffer(1000) #when set to CRS 3857

# Spatial join: find points within polygons
points = gpd.read_file('points.geojson')
polygons = gpd.read_file('boundaries.geojson')
joined = gpd.sjoin(points, polygons, predicate='within')

# Dissolve: merge geometries by attribute
dissolved = gdf.dissolve(by='state', aggfunc='sum')

# Export to various formats
gdf.to_parquet('output.parquet')          # GeoParquet (recommended)
gdf.to_file('output.geojson', driver='GeoJSON') #for tools that dont support GeoParquet
```

### Geo-Visualization with `.explore()`, `lonboard` and Datawrapper

#### `.explore()`

**Best for:** Quick exploration and prototyping during data analysis.

**Pros:** Built into GeoPandas, method is available on any GeoDataFrame. Great for exploratory data analysis, checking that your data looks right, exploring spatial patterns, and iterating quickly on map designs.

**Cons:** Becomes slow with large datasets (>100k features). Limited customization compared to dedicated mapping libraries. Requires extra dependencies to be installed.

**Use when:** You're in the middle of analysis and want to quickly visualize your GeoDataFrame without switching tools.

**Required dependencies:**
```bash
pip install folium mapclassify matplotlib
```
- `folium` - Required for `.explore()` to work at all (renders the interactive map)
- `mapclassify` - Required when using `scheme=` parameter for classification (e.g., 'naturalbreaks', 'quantiles', 'equalinterval')
- `matplotlib` - Required for colormap (`cmap=`) support

```python
import geopandas as gpd
# folium, mapclassify, and matplotlib must be installed but don't need to be imported
# geopandas imports them automatically when you call .explore()

# Basic interactive map (uses folium under the hood)
gdf.explore()

# Choropleth map with customization
# (requires mapclassify for scheme parameter)
gdf.explore(
    column='population',           # Column for color scale
    cmap='YlOrRd',                 # Matplotlib colormap
    scheme='naturalbreaks',        # Classification scheme (needs mapclassify)
    k=5,                           # Number of bins
    legend=True,
    tooltip=['name', 'population'],  # Columns to show on hover
    popup=True,                    # Show all columns on click
    tiles='CartoDB positron',      # Background tiles
    style_kwds={'color': 'black', 'weight': 0.5}  # Border style
)
```

#### `lonboard`

**Best for:** Large datasets and high-performance visualization in Jupyter notebooks.

**Pros:** GPU-accelerated rendering via deck.gl can handle millions of points smoothly. Excellent interactivity, pan, zoom, and hover work fluidly even with massive datasets. Native support for GeoArrow format for efficient data transfer.

**Cons:** Requires separate installation (`pip install lonboard`). Styling options are more technical (RGBA arrays, deck.gl conventions).

**Use when:** You have large point datasets (crime incidents, sensor readings, business locations) or need smooth interactivity with 100k+ features.

```python
import geopandas as gpd
from lonboard import viz, Map, ScatterplotLayer, PolygonLayer

# Quick visualization (auto-detects geometry type)
viz(gdf)

# Custom ScatterplotLayer for points
layer = ScatterplotLayer.from_geopandas(
    gdf,
    get_radius=100,
    get_fill_color=[255, 0, 0, 200],  # RGBA
    pickable=True
)
m = Map(layer)
m

# PolygonLayer with color based on column
from lonboard.colormap import apply_continuous_cmap
import matplotlib.pyplot as plt

colors = apply_continuous_cmap(gdf['value'], plt.cm.viridis)
layer = PolygonLayer.from_geopandas(
    gdf,
    get_fill_color=colors,
    get_line_color=[0, 0, 0, 100],
    pickable=True
)
Map(layer)
```

#### Datawrapper

**Best for:** Publication-ready choropleth and proportional symbol maps for articles and reports.

**Pros:** Beautiful, professional defaults out of the box. Generates embeddable, responsive iframes that work in any CMS. Readers can interact (hover, click) without running any code. Accessible and mobile-friendly. Easy to update data programmatically for updating data.

**Cons:** Requires a Datawrapper account (free tier available). Limited to Datawrapper's supported boundary files, you can't bring arbitrary geometries. Less flexibility for custom visualizations.

**Use when:** You need a polished map for publication. Ideal for choropleth maps showing statistics by region (unemployment by state, COVID cases by county, election results by district). Your audience will view the map in a browser, not a notebook.

Unlike `.explore()` or `lonboard`, you don't pass raw geometry, instead you match your data to Datawrapper's built-in boundary files using standard codes (FIPS, ISO, etc.).

```python
import datawrapper as dw
import pandas as pd

# Read API key
with open('datawrapper_api_key.txt', 'r') as f:
    api_key = f.read().strip()

# Prepare data with location codes that match Datawrapper's boundaries
# For US states: use 2-letter abbreviations or FIPS codes
# For countries: use ISO 3166-1 alpha-2 codes
df = pd.DataFrame({
    'state': ['AL', 'AK', 'AZ', 'AR', 'CA'],  # State abbreviations
    'unemployment_rate': [4.9, 3.2, 7.1, 4.2, 5.8]
})

# Create a choropleth map
chart = dw.ChoroplethMap(
    title='Unemployment Rate by State',
    intro='Percentage of labor force unemployed, 2024',
    data=df,

    # Map configuration
    basemap='us-states',           # Built-in US states boundaries
    basemap_key='state',           # Column in your data with location codes
    value_column='unemployment_rate',

    # Styling
    color_palette='YlOrRd',        # Color scheme
    legend_title='Unemployment %',

    # Attribution
    source_name='Bureau of Labor Statistics',
    source_url='https://www.bls.gov/',
    byline='Your Name'
)

# Create and publish
chart.create(access_token=api_key)
chart.publish()

# Get embed code for your article
iframe = chart.get_iframe_code(responsive=True)
print(f"Chart URL: https://datawrapper.dwcdn.net/{chart.chart_id}")

# Update with new data (for live-updating maps)
new_df = pd.DataFrame({...})  # Updated data
existing_chart = dw.get_chart('YOUR_CHART_ID')
existing_chart.data = new_df
existing_chart.update()
existing_chart.publish()
```

**Available Datawrapper basemaps include:**
- `us-states`, `us-counties`, `us-congressional-districts`
- `world`, `europe`, `africa`, `asia`
- Country-specific maps (e.g., `germany-states`, `uk-constituencies`)
