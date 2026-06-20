import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

# Set page configuration to wide layout
st.set_page_config(page_title="India Climate Dashboard", layout="wide")

# ==============================================================================
# 1. CLOUD URL CONFIGURATION (Dynamic Router Mapping)
# ==============================================================================
GEOJSON_URL = "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/india_2001_districtsbig.geojson"

# Dictionary mapping specific eras to their direct download links on your release page
ERA_DATA_URLS = {
    "1952 - 1975": "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/climate_1952_1975.csv",
    "1976 - 1995": "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/climate_1976_1995.csv",
    "1996 - 2010": "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/climate_1996_2010.csv",
    "2011 - 2023": "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/climate_2011_2023.csv"
}

# ==============================================================================
# 2. DYNAMIC SIDEBAR CONFIGURATION (Part 1 - Era Assignment)
# ==============================================================================
st.sidebar.header("🗺️ Filter Options")

# User selects the historical context block first
selected_era = st.sidebar.selectbox("1. Select Climate Era", list(ERA_DATA_URLS.keys()), index=len(ERA_DATA_URLS)-1)
chosen_csv_url = ERA_DATA_URLS[selected_era]

# ==============================================================================
# 3. MEMORY-SAFE DYNAMIC ASSET CACHING ENGINE
# ==============================================================================
@st.cache_data(show_spinner="Fetching localized climate era matrix... Please wait.")
def load_era_data(url):
    # Only pull columns required for map rendering to minimize memory allocation
    keep_cols = ['year', 'month', 'day', 'ST_NAME', 'DISTRICT', 
                 'temp_max', 'temp_min', 'temp_mean', 'rh_mean', 'wetbulb_mean', 'precip_total']
    
    # Check if reading raw csv or zipped archive dynamically
    if url.endswith('.zip'):
        df = pd.read_csv(url, compression='zip', usecols=keep_cols)
    else:
        df = pd.read_csv(url, usecols=keep_cols)
        
    df.dropna(subset=['DISTRICT'], inplace=True)
    df['year'] = df['year'].astype(int)
    df['month'] = df['month'].astype(int)
    df['day'] = df['day'].astype(int)
    return df

@st.cache_data
def load_geojson():
    response = requests.get(GEOJSON_URL)
    return response.json()

# Execute dynamic streaming data pull
try:
    df = load_era_data(chosen_csv_url)
    geojson_data = load_geojson()
except Exception as e:
    st.error(f"Error loading remote cloud assets: {e}")
    st.stop()

# ==============================================================================
# 4. SIDEBAR CONFIGURATION (Part 2 - Context Cascades)
# ==============================================================================
# Filter date pickers are constrained specifically by the loaded dataset
available_years = sorted(df['year'].unique())
selected_year = st.sidebar.selectbox("2. Select Year", available_years, index=len(available_years)-1)

available_months = sorted(df['month'].unique())
selected_month = st.sidebar.selectbox("3. Select Month", available_months)

available_days = sorted(df['day'].unique())
selected_day = st.sidebar.selectbox("4. Select Day", available_days)

available_states = sorted(df['ST_NAME'].unique())
selected_state = st.sidebar.selectbox("5. Select State", available_states)

state_filtered_df = df[df['ST_NAME'] == selected_state]
available_districts = sorted(state_filtered_df['DISTRICT'].unique())
selected_district = st.sidebar.selectbox("6. Select District Focus", ["All Districts"] + list(available_districts))

# ==============================================================================
# 5. DATA QUERY EXECUTION
# ==============================================================================
query_df = df[
    (df['year'] == selected_year) & 
    (df['month'] == selected_month) & 
    (df['day'] == selected_day)
]

if selected_district != "All Districts":
    display_df = query_df[query_df['DISTRICT'] == selected_district]
else:
    display_df = query_df

# ==============================================================================
# 6. WIDESCREEN MAIN LAYOUT
# ==============================================================================
map_column, right_panel_column = st.columns([4.2, 1])

# --- RIGHT SIDE PANEL: Settings & Citations ---
with right_panel_column:
    st.subheader("⚙️ Map Settings")
    metric_options = {
        "Maximum Temperature (°C)": "temp_max",
        "Minimum Temperature (°C)": "temp_min",
        "Mean Temperature (°C)": "temp_mean",
        "Relative Humidity (%)": "rh_mean",
        "Wetbulb Temperature (°C)": "wetbulb_mean",
        "Total Precipitation (mm)": "precip_total"
    }
    selected_metric_label = st.selectbox("Choose Variable", list(metric_options.keys()))
    chosen_column = metric_options[selected_metric_label]
    
    st.write("---")
    st.subheader("📈 Summary Stats")
    
    if not display_df.empty:
        st.metric(label="Average Value", value=f"{display_df[chosen_column].mean():.2f}")
        st.metric(label="Max Recorded", value=f"{display_df[chosen_column].max():.2f}")
        st.metric(label="Data Points", value=f"{len(display_df)} Districts")
    else:
        st.warning("No data found.")
        
    st.write("---")
    
    st.markdown("### ℹ️ Dashboard Info")
    st.markdown(
        """
        * **Created by:** [Binay Shankar](binayshankar.weebly.com)
        
        **Data Sources:**
        * **Shapefile (Census 2001):** [Census of India](https://onlinemaps.surveyofindia.gov.in/)  
        * **Climate Dynamics:** [CDSE Portal](https://dataspace.copernicus.eu/) - ERA5 Dataset  
        """
    )

# --- LEFT PANEL: Widescreen Map Visualization ---
with map_column:
    st.subheader(f"🗺️ Geographic Heatmap: {selected_metric_label} ({selected_day}/{selected_month}/{selected_year})")
    
    if not query_df.empty:
        color_scales = {
            "temp_max": "Reds", 
            "temp_min": "Blues", 
            "temp_mean": "Thermal",
            "rh_mean": "YlGnBu", 
            "wetbulb_mean": "RdYlBu_r", 
            "precip_total": "Blues"
        }
        
        fig = px.choropleth(
            query_df,
            geojson=geojson_data,
            locations="DISTRICT",
            featureidkey="properties.DISTRICT",
            color=chosen_column,
            color_continuous_scale=color_scales.get(chosen_column, "Viridis"),
            scope="asia",
            hover_data=["ST_NAME", "DISTRICT", chosen_column]
        )
        
        fig.update_geos(
            center=dict(lon=78.9629, lat=22.5937),
            projection_scale=6.5,
            visible=False
        )
        
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, 
            height=750,
            coloraxis_colorbar=dict(title=dict(text="Scale", side="top"), thickness=15, len=0.6)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No map profile matching current selectors found.")
