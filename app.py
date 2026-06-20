import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

# Set page configuration to wide layout
st.set_page_config(page_title="India Climate Dashboard", layout="wide")

# ==============================================================================
# 1. CLOUD URL CONFIGURATION 
# ==============================================================================

# Direct download link to your compressed data ZIP file in GitHub Releases
CSV_URL = "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/climate_data_india_FINAL.zip"

# Direct download link to your map file in GitHub Releases
GEOJSON_URL = "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/india_2001_districtsbig.geojson"

# ==============================================================================
# 2. CACHE DATA LOADING (Optimized for Streamlit Cloud performance)
# ==============================================================================
@st.cache_data(show_spinner="Downloading climate matrix (15M+ rows)... Please wait.")
def load_data():
    # Pandas natively detects the '.zip' extension, decompresses it in memory, and parses the CSV
    df = pd.read_csv(CSV_URL, compression='zip')
    
    # Ensure date component types are correct integers
    df['year'] = df['year'].astype(int)
    df['month'] = df['month'].astype(int)
    df['day'] = df['day'].astype(int)
    return df

@st.cache_data
def load_geojson():
    response = requests.get(GEOJSON_URL)
    return response.json()

# Execute asset downloads
try:
    df = load_data()
    geojson_data = load_geojson()
except Exception as e:
    st.error(f"Error loading remote cloud assets: {e}")
    st.info("Please verify your GitHub URLs are public and spelled correctly.")
    st.stop()

# ==============================================================================
# 3. DASHBOARD HEADER
# ==============================================================================
st.title("☀️ India Historical Climate & Weather Dashboard")
st.write("---")

# ==============================================================================
# 4. LEFT SIDEBAR FILTERS (Cascading Selection Engine)
# ==============================================================================
st.sidebar.header("🗺️ Filter Options")

# Year Filter
available_years = sorted(df['year'].unique())
selected_year = st.sidebar.selectbox("Select Year", available_years, index=len(available_years)-1)

# Month Filter
available_months = sorted(df['month'].unique())
selected_month = st.sidebar.selectbox("Select Month", available_months)

# Day Filter
available_days = sorted(df['day'].unique())
selected_day = st.sidebar.selectbox("Select Day", available_days)

# State Filter
available_states = sorted(df['ST_NAME'].unique())
selected_state = st.sidebar.selectbox("Select State", available_states)

# Dynamic District Filter (Only shows districts belonging to selected state)
state_filtered_df = df[df['ST_NAME'] == selected_state]
available_districts = sorted(state_filtered_df['DISTRICT'].unique())
selected_district = st.sidebar.selectbox("Select District Focus", ["All Districts"] + list(available_districts))

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
# 6. WIDESCREEN MAIN LAYOUT: MAP ON LEFT (4.2), CONTROLS & NOTES ON RIGHT (1)
# ==============================================================================
map_column, right_panel_column = st.columns([4.2, 1])

# --- RIGHT SIDE PANEL: Settings, Stats, and Metadata Notes ---
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
    
    # 📝 Footnotes & Data Citations
    st.markdown("### ℹ️ Dashboard Info")
    st.markdown(
        """
        **Created by:** Binay Shankar (https://binayshankar.weebly.com/)  
        
        **Data Sources:**
        * **Shapefile (Census 2001):** [Census of India / Survey of India](https://onlinemaps.surveyofindia.gov.in/)  
        * **Climate Dynamics:** [Copernicus Data Space Ecosystem (CDSE)](https://dataspace.copernicus.eu/) - ERA5 Reanalysis Dataset  
        """
    )

# --- LEFT PANEL: The Widescreen Interactive Map ---
with map_column:
    st.subheader(f"🗺️ Geographic Heatmap: {selected_metric_label} ({selected_day}/{selected_month}/{selected_year})")
    
    if not query_df.empty:
        # Valid sequential and diverging Plotly color palettes
        color_scales = {
            "temp_max": "Reds", 
            "temp_min": "Blues", 
            "temp_mean": "Thermal",
            "rh_mean": "YlGnBu", 
            "wetbulb_mean": "RdYlBu_r", # Fixed from 'Blry' to valid diverging palette
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
        
        # Center view and snap onto Indian geographic coordinates
        fig.update_geos(
            center=dict(lon=78.9629, lat=22.5937),
            projection_scale=6.5,
            visible=False
        )
        
        # Maximize map canvas container size
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, 
            height=750,
            coloraxis_colorbar=dict(title=dict(text="Scale", side="top"), thickness=15, len=0.6)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Cannot render map. Data empty for selected parameters.")
