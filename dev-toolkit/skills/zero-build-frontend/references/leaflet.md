## Leaflet.js maps

### Basic map setup

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="/vendor/leaflet-1.9.4.css" />
  <link rel="stylesheet" href="/vendor/MarkerCluster-1.5.3.css" />
  <link rel="stylesheet" href="/vendor/MarkerCluster.Default-1.5.3.css" />
  <style>
    #map { height: 85vh; width: 100%; }
  </style>
</head>
<body>
  <div id="map"></div>

  <script src="/vendor/leaflet-1.9.4.js"></script>
  <script src="/vendor/leaflet.markercluster-1.5.3.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

### Map application with clustering

```javascript
// js/app.js

class MapApp {
  constructor() {
    this.map = null;
    this.markers = null;
    this.data = [];
    this.filters = {
      year: null,
      county: null,
      status: null
    };
  }

  async init() {
    this.setupMap();
    await this.loadData();
    this.renderMarkers();
    this.setupFilters();
  }

  setupMap() {
    // Initialize map centered on NJ
    this.map = L.map('map', {
      center: [40.0583, -74.4057],
      zoom: 8,
      scrollWheelZoom: false,  // Disable mouse wheel zoom
      zoomControl: false       // We'll add custom controls
    });

    // Add tile layer (CARTO Voyager)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap, &copy; CARTO',
      maxZoom: 19
    }).addTo(this.map);

    // Add custom zoom control (top-right)
    L.control.zoom({ position: 'topright' }).addTo(this.map);

    // Initialize marker cluster group
    this.markers = L.markerClusterGroup({
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      maxClusterRadius: 50,
      spiderLegPolylineOptions: { weight: 1.5, color: '#2dc8d2' }
    });

    this.map.addLayer(this.markers);
  }

  async loadData() {
    const response = await fetch('data/grantees.json');
    this.data = await response.json();
  }

  renderMarkers() {
    this.markers.clearLayers();

    const filtered = this.data.filter(item => {
      if (this.filters.year && item.year !== this.filters.year) return false;
      if (this.filters.county && item.county !== this.filters.county) return false;
      if (this.filters.status && item.status !== this.filters.status) return false;
      return true;
    });

    filtered.forEach(item => {
      if (!item.lat || !item.lng) return;

      const marker = L.marker([item.lat, item.lng], {
        icon: this.createIcon(item.status)
      });

      marker.bindPopup(this.createPopup(item));
      this.markers.addLayer(marker);
    });

    // Update count display
    document.getElementById('count').textContent = filtered.length;
  }

  createIcon(status) {
    const colors = {
      'Active': '#2dc8d2',
      'Completed': '#666666',
      'Pending': '#f34213'
    };

    return L.divIcon({
      html: `<div style="background: ${colors[status] || '#2dc8d2'}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
      className: 'custom-marker',
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });
  }

  createPopup(item) {
    return `
      <div class="popup-content">
        <h3 class="font-bold text-lg">${item.name}</h3>
        <p class="text-sm text-gray-600">${item.county} County</p>
        <p class="text-sm mt-2">${item.description || ''}</p>
        <div class="mt-2">
          <span class="px-2 py-1 text-xs rounded bg-gray-200">${item.status}</span>
          <span class="px-2 py-1 text-xs rounded bg-gray-200">${item.year}</span>
        </div>
        ${item.website ? `<a href="${item.website}" target="_blank" class="block mt-2 text-brand-primary">Visit Website →</a>` : ''}
      </div>
    `;
  }

  setupFilters() {
    // Year filter
    const years = [...new Set(this.data.map(d => d.year))].sort();
    const yearSelect = document.getElementById('year-filter');
    years.forEach(year => {
      const option = document.createElement('option');
      option.value = year;
      option.textContent = year;
      yearSelect.appendChild(option);
    });

    yearSelect.addEventListener('change', (e) => {
      this.filters.year = e.target.value || null;
      this.renderMarkers();
    });

    // Similar for county, status filters...
  }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  const app = new MapApp();
  app.init();
});
```
