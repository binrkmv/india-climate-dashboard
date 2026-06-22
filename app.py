import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

# Set page configuration to wide layout
st.set_page_config(page_title="India Climate Dashboard", layout="wide")
# ==============================================================================
# 1. CLOUD URL CONFIGURATION (Updated for Raw Monthly CSV)
# ==============================================================================
# Changed extension from .zip to .csv
CSV_URL = "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/climate_data_india_MONTHLY.csv"
GEOJSON_URL = "https://github.com/binrkmv/india-climate-dashboard/releases/download/v1.0.0/india_2001_districtsbig.geojson"

# ==============================================================================
# 2. DATA LOADING ENGINE (Fast & Memory Safe for Raw CSV)
# ==============================================================================
@st.cache_data(show_spinner="Loading monthly climate dataset... Please wait.")
def load_data():
    # Removed the compression='zip' parameter since it's a straight CSV now
    df = pd.read_csv(CSV_URL)
    
    # Cast timeframe elements into integers
    df['year'] = df['year'].astype(int)
    df['month'] = df['month'].astype(int)
    return df

@st.cache_data
def load_geojson():
    response = requests.get(GEOJSON_URL)
    return response.json()

# Execute asset downloads safely
try:
    df = load_data()
    geojson_data = load_geojson()
except Exception as e:
    st.error(f"Error loading remote cloud assets: {e}")
    st.info("Please verify that climate_data_india_MONTHLY.zip is fully uploaded to your GitHub Release assets.")
    st.stop()

# ==============================================================================
# 3. DASHBOARD HEADER
# ==============================================================================
st.title("☀️ India Historical Climate & Weather Dashboard (Monthly Metrics)")
st.write("---")

# ==============================================================================
# 4. LEFT SIDEBAR FILTERS (With Month Name Labels)
# ==============================================================================
st.sidebar.header("🗺️ Filter Options")

# Year Filter
available_years = sorted(df['year'].unique())
selected_year = st.sidebar.selectbox("Select Year", available_years, index=len(available_years)-1)

# Month Name Dictionary Mapping
month_mapping = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}
available_months = sorted(df['month'].unique())

# Displays human-readable month names while passing the correct integer backend value
selected_month_num = st.sidebar.selectbox(
    "Select Month", 
    available_months, 
    format_func=lambda x: month_mapping.get(x)
)

# State Filter
available_states = sorted(df['ST_NAME'].unique())
selected_state = st.sidebar.selectbox("Select State", available_states)

# Dynamic District Filter
state_filtered_df = df[df['ST_NAME'] == selected_state]
available_districts = sorted(state_filtered_df['DISTRICT'].unique())
selected_district = st.sidebar.selectbox("Select District Focus", ["All Districts"] + list(available_districts))

# ==============================================================================
# 5. DATA QUERY EXECUTION
# ==============================================================================
query_df = df[
    (df['year'] == selected_year) & 
    (df['month'] == selected_month_num)
]

if selected_district != "All Districts":
    display_df = query_df[query_df['DISTRICT'] == selected_district]
else:
    display_df = query_df

# ==============================================================================
# 6. WIDESCREEN MAIN LAYOUT
# ==============================================================================
map_column, right_panel_column = st.columns([4.2, 1])

# --- RIGHT SIDE PANEL: Settings & Stats Summary ---
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
        # Dynamic label adjustment depending on chosen math context
        if chosen_column == 'temp_max':
            stat_label = "Highest Temp in Month"
            stat_val = display_df[chosen_column].max()
        elif chosen_column == 'temp_min':
            stat_label = "Lowest Temp in Era"
            stat_val = display_df[chosen_column].min()
        elif chosen_column == 'precip_total':
            stat_label = "Total Monthly Volume"
            stat_val = display_df[chosen_column].sum()
        else:
            stat_label = "Average Value"
            stat_val = display_df[chosen_column].mean()

        st.metric(label=stat_label, value=f"{stat_val:.2f}")
        st.metric(label="Data Points Included", value=f"{len(display_df)} Districts")
    else:
        st.warning("No data found.")
        
    st.write("---")
    st.markdown("### ℹ️ Dashboard Info")
    st.markdown(
        """
        **Created by:** [Binay Shankar](https://binayshankar.weebly.com)
        
        **Data Sources:**
        * **Shapefile (Census 2001):** [Census of India](https://onlinemaps.surveyofindia.gov.in/)  
        * **Climate Dynamics:** [CDSE Portal](https://dataspace.copernicus.eu/) - ERA5 Dataset  
        """
    )

# --- LEFT PANEL: The Widescreen Interactive Map ---
with map_column:
    st.subheader(f"🗺️ Geographic Heatmap: {selected_metric_label} ({month_mapping[selected_month_num]} {selected_year})")
    
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
        
        # Snap map onto Indian geographic coordinates
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
        st.error("Cannot render map for selected parameters.")
