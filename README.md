# india-climate-dashboard

# ☀️ India Historical Climate & Weather Dashboard (1952 - 2023)

An interactive, widescreen geographic dashboard built using Streamlit and Plotly to visualize district-level historical climate variations across India. The application processes and analyzes monthly historical weather metrics.

👉 **[[india-climate-dashboard](https://india-climate-dashboard.streamlit.app/)]**

---

## 🚀 Features
* **Granular Filters:** Cascading sidebar options to filter by specific Year, Month, and State.
* **Widescreen Map Visualization:** Immersive India choropleth map highlighting spatial distribution at the district level.
* **Key Weather Metrics:** Interactive mapping for Maximum, Minimum, and Mean Temperature, Relative Humidity, Wetbulb Temperature, and Total Precipitation.
* **Instant Statistical Summaries:** High-level metric tracking showing average and peak values for the selected filters.

---

## 📊 Data & Architecture Setup
Because of the massive scale of the daily climate records, the core dataset exceeds traditional version-control limits. The backend architecture maps remote cloud assets asynchronously:

1. **Spatial Boundary Shapefile (Census 2001 GeoJSON):** Hosted via the repository's stable release assets (`india_2001_districtsbig.geojson`). Source: Census of India / Survey of India.
2. **Climate Matrices (ERA5 Reanalysis):** Compressed into an in-memory stream .csv (`climate_data_india_MONTHLY.csv`) and served via GitHub Releases. Source: Copernicus Data Space Ecosystem (CDSE).

---

## 🛠️ Local Installation & Testing

If you want to run this project on your local machine:

1. Clone or download this repository.
2. Ensure you have Python installed, then install the required dependencies using terminal:
   ```bash
   pip install -r requirements.txt
