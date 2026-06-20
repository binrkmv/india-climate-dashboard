import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Set page configuration to wide layout
st.set_page_config(page_title="India Climate Dashboard", layout="wide")

# 1. PATH CONFIGURATION
DATA_DIR = r"F:\OneDrive - Shiv Nadar Institution of Eminence\Heat and Firms\dashboard"
CSV_PATH = os.path.join(DATA_DIR, "climate_data_india_FINAL.csv")
GEOJSON_PATH = os.path.join(DATA_DIR, "india_2001_districts.geojson")

# 2. CACHE DATA LOADING
@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

@st.cache_data
def load_geojson():
    with open(GEOJSON_PATH, 'r') as f:
        return json.load(f)

df = load_data()
geojson_data = load_geojson()

# 3. DASHBOARD HEADER
st.title("☀️ India Historical Climate & Weather Dashboard")
st.write("---")

# 4. LEFT SIDEBAR FILTERS
st.sidebar.header("🗺️ Filter Options")
available_years = sorted(df['year'].unique())
selected_year = st.sidebar.selectbox("Select Year", available_years, index=len(available_years)-1)

available_months = sorted(df['month'].unique())
selected_month = st.sidebar.selectbox("Select Month", available_months)

available_days = sorted(df['day'].unique())
selected_day = st.sidebar.selectbox("Select Day", available_days)

available_states = sorted(df['ST_NAME'].unique())
selected_state = st.sidebar.selectbox("Select State", available_states)

state_filtered_df = df[df['ST_NAME'] == selected_state]
available_districts = sorted(state_filtered_df['DISTRICT'].unique())
selected_district = st.sidebar.selectbox("Select District Focus", ["All Districts"] + list(available_districts))

# 5. DATA QUERY EXECUTION
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
# 6. TWO-COLUMN MAIN LAYOUT: MAP ON LEFT, CONTROLS & NOTES ON RIGHT
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
    
    # 📝 USER SPECIFIED METADATA & CITATIONS NOTE
    st.markdown("### ℹ️ Dashboard Info")
    st.markdown(
        """
        **Created by:** Binay Shankar  
        
        **Data Sources:** * **Shapefile (Census 2001):** [Census of India / Survey of India](https://onlinemaps.surveyofindia.gov.in/)  
        * **Climate Dynamics:** [Copernicus Data Space Ecosystem (CDSE)](https://dataspace.copernicus.eu/) - ERA5 Reanalysis Dataset  
        """
    )

# --- LEFT PANEL: The Widescreen Interactive Map ---
with map_column:
    st.subheader(f"🗺️ Geographic Heatmap: {selected_metric_label} ({selected_day}/{selected_month}/{selected_year})")
    
    if not query_df.empty:
        # Fixed wetbulb color scale map to use valid sequential 'RdYlBu_r' 
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
        st.error("Cannot render map. Data empty for selected parameters.")