import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import json
import os


st.set_page_config(
    page_title="Pakistan Heat Risk Command Center",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    /* Map Container borders */
    .plotly-graph-div {
        border-radius: 10px;
        overflow: hidden;
    }
    /* Sidebar Headers */
    .css-10trblm {
        color: #FF4B4B;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_assets():
    """Loads the ML Model and GeoJSON Map once."""
    # Paths
    MODEL_PATH = "models/heat_risk_model.pkl"
    GEOJSON_PATH = "app/data/pakistan_districts.geojson"
    
    # Load Model
    if not os.path.exists(MODEL_PATH):
        st.error(f"❌ Critical Error: Model not found at {MODEL_PATH}")
        st.stop()
    model = joblib.load(MODEL_PATH)
    
    # Load Map
    if not os.path.exists(GEOJSON_PATH):
        st.error(f"❌ Critical Error: Map not found at {GEOJSON_PATH}")
        st.stop()
    with open(GEOJSON_PATH, 'r') as f:
        geojson = json.load(f)
        
    return model, geojson

@st.cache_data
def load_baseline_data():
    """Loads the seasonal weather baseline."""
    CSV_PATH = "app/data/app_baseline.csv"
    if not os.path.exists(CSV_PATH):
        st.error(f"❌ Critical Error: Data not found at {CSV_PATH}")
        st.stop()
    return pd.read_csv(CSV_PATH)

model, geojson_map = load_assets()
baseline_df = load_baseline_data()

# ==========================================
# 3. HELPER FUNCTIONS (PHYSICS ENGINE)
# ==========================================
def calculate_heat_index_vectorized(temp_c, rh):
    """Calculates Heat Index for the entire array of districts at once."""
    T_F = (temp_c * 9/5) + 32
    
    # Simple formula
    hi_simple = 0.5 * (T_F + 61.0 + ((T_F-68.0)*1.2) + (rh*0.094))
    
    # Regression formula constants
    c1, c2, c3, c4 = -42.379, 2.04901523, 10.14333127, -0.22475541
    c5, c6, c7, c8, c9 = -6.83783e-3, -5.481717e-2, 1.22874e-3, 8.5282e-4, -1.99e-6
    
    hi_full = (c1 + c2*T_F + c3*rh + c4*T_F*rh + c5*T_F**2 + 
               c6*rh**2 + c7*T_F**2*rh + c8*T_F*rh**2 + c9*T_F**2*rh**2)
    
    # Apply threshold logic (HI > 80F uses full formula)
    hi_final_f = np.where(hi_simple > 80, hi_full, hi_simple)
    
    return (hi_final_f - 32) * 5/9

# ==========================================
# 4. SIDEBAR CONTROLS (SCENARIO BUILDER)
# ==========================================
st.sidebar.title("🎛️ Command Center")

# A. Season Selector
st.sidebar.subheader("1. Select Baseline Season")
month_map = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 
             7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
selected_month = st.sidebar.select_slider(
    "Month", options=range(1, 13), value=6, format_func=lambda x: month_map[x]
)

# B. Climate Modifiers
st.sidebar.subheader("2. Apply Stressors (What-If)")
delta_temp = st.sidebar.slider("🌍 Global Warming (°C)", 0.0, 5.0, 0.0, 0.1, help="Add to baseline temp")
delta_rh = st.sidebar.slider("💧 Humidity Shift (%)", -20, 20, 0, 5, help="Add to baseline humidity")
delta_pop = st.sidebar.slider("👥 Population Growth (%)", 0, 50, 0, 5, help="Simulate urbanization")

# ==========================================
# 5. SIMULATION ENGINE
# ==========================================
# Filter data for the selected month
sim_df = baseline_df[baseline_df['month'] == selected_month].copy()

# Apply Scenarios
sim_df['temp_c'] += delta_temp
sim_df['humidity_relative'] = (sim_df['humidity_relative'] + delta_rh).clip(0, 100)
sim_df['population_2020'] = sim_df['population_2020'] * (1 + delta_pop/100)
sim_df['pop_log'] = np.log10(sim_df['population_2020'] + 1)

# Re-Calculate Heat Index based on new conditions
sim_df['heat_index_c'] = calculate_heat_index_vectorized(sim_df['temp_c'], sim_df['humidity_relative'])

# Update Lag Features (Assumption: Persistent Heatwave)
# If we raise temp by 2C, we assume the 'rolling avg' also rose by 2C
sim_df['temp_roll_24h'] += delta_temp
sim_df['hi_max_72h'] = sim_df[['hi_max_72h', 'heat_index_c']].max(axis=1) # Updates max if new HI is higher

# Estimate Risk Lag (Heuristic)
# We assume the lag risk is roughly similar to the current risk for a steady-state simulation
# To do this rigorously, we'd need a 2-step prediction, but for PoC, we use a proxy
conditions = [
    (sim_df['heat_index_c'] < 27),
    (sim_df['heat_index_c'] >= 27) & (sim_df['heat_index_c'] < 32),
    (sim_df['heat_index_c'] >= 32) & (sim_df['heat_index_c'] < 41),
    (sim_df['heat_index_c'] >= 41)
]
choices = [0, 1, 2, 3]
sim_df['risk_lag_1h'] = np.select(conditions, choices, default=0) # Assume steady state

# Prepare Features for Model
features = ['population_2020', 'pop_log', 'temp_c', 'humidity_relative', 
            'wind_speed_m_s', 'solar_w_m2', 'temp_roll_24h', 'hi_max_72h', 'risk_lag_1h']

# --- RUN PREDICTION ---
sim_df['predicted_risk'] = model.predict(sim_df[features])
sim_df['risk_label'] = sim_df['predicted_risk'].map({0:"Safe", 1:"Caution", 2:"Danger", 3:"Extreme"})

# ==========================================
# 6. DASHBOARD LAYOUT
# ==========================================

# --- ROW 1: KPI COUNTERS ---
st.markdown(f"### 📊 National Impact Report ({month_map[selected_month]} + {delta_temp}°C)")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# KPI 1: Population at High Risk (Classes 2 & 3)
high_risk_pop = sim_df[sim_df['predicted_risk'] >= 2]['population_2020'].sum()
kpi1.metric("Pop. at Risk (High/Extreme)", f"{high_risk_pop/1_000_000:.1f} M", delta_color="inverse")

# KPI 2: Districts in Extreme Danger
extreme_count = len(sim_df[sim_df['predicted_risk'] == 3])
kpi2.metric("Districts in Extreme Danger", f"{extreme_count}", delta_color="inverse")

# KPI 3: Hottest District
hottest_district = sim_df.loc[sim_df['heat_index_c'].idxmax()]
kpi3.metric("Hottest District", hottest_district['district_name'], f"{hottest_district['heat_index_c']:.1f}°C HI")

# KPI 4: Average Heat Index
avg_hi = sim_df['heat_index_c'].mean()
kpi4.metric("National Avg Heat Index", f"{avg_hi:.1f}°C", delta=f"{delta_temp}°C vs Baseline")

# --- ROW 2: THE MAP ---
col_map, col_details = st.columns([3, 1])

with col_map:
    st.markdown("#### 🗺️ Spatial Risk Assessment")
    
    # Plotly Choropleth
    fig = px.choropleth(
        sim_df,
        geojson=geojson_map,
        locations='district_name',
        featureidkey="properties.district_name",
        color='predicted_risk',
        color_continuous_scale=[
            (0.00, "green"),   # Safe
            (0.33, "yellow"),  # Caution
            (0.66, "orange"),  # Danger
            (1.00, "red")      # Extreme
        ],
        range_color=(0, 3),
        hover_name='district_name',
        hover_data={
            'predicted_risk': False,
            'risk_label': True,
            'temp_c': ':.1f',
            'heat_index_c': ':.1f',
            'population_2020': True
        },
        projection="mercator"
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="#0E1117", # Matches Streamlit Dark Mode
        geo_bgcolor="#0E1117",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

# --- ROW 3: DISTRICT DEEP DIVE ---
with col_details:
    st.markdown("#### 🔍 District Detail")
    
    # Sort districts by Risk (descending) so dangerous ones appear first
    sorted_districts = sim_df.sort_values(['predicted_risk', 'heat_index_c'], ascending=False)['district_name'].tolist()
    target_district = st.selectbox("Inspect District:", sorted_districts)
    
    # Get stats
    d_stats = sim_df[sim_df['district_name'] == target_district].iloc[0]
    
    # Custom Risk Badge
    risk_colors = {0: "green", 1: "#FFC300", 2: "#FF5733", 3: "#C70039"}
    st.markdown(f"""
        <div style="background-color: {risk_colors[d_stats['predicted_risk']]}; padding: 10px; border-radius: 5px; text-align: center;">
            <h2 style="color: white; margin:0;">{d_stats['risk_label']}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    st.write(f"**Temperature:** {d_stats['temp_c']:.1f}°C")
    st.write(f"**Heat Index:** {d_stats['heat_index_c']:.1f}°C")
    st.write(f"**Humidity:** {d_stats['humidity_relative']:.0f}%")
    st.write(f"**Wind:** {d_stats['wind_speed_m_s']:.1f} m/s")
    
    # Population Bar
    st.progress(min(d_stats['population_2020'] / 5_000_000, 1.0))
    st.caption(f"Pop: {d_stats['population_2020']:,}")

# --- ROW 4: DATA TABLE ---
with st.expander("📋 View Full Simulation Data"):
    st.dataframe(
        sim_df[['district_name', 'risk_label', 'heat_index_c', 'temp_c', 'humidity_relative', 'population_2020']]
        .sort_values('heat_index_c', ascending=False)
        .style.background_gradient(subset=['heat_index_c'], cmap='Reds')
    )