import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from utils.data_loader import load_baseline_data, load_map_geojson, load_model
from utils.model_engine import calculate_heat_index, run_prediction

def show():
    # --- 1. LOAD ASSETS ---
    model = load_model()
    geojson = load_map_geojson() 
    baseline = load_baseline_data()
    
    st.markdown("## 🕹️ Simulation Lab (God Mode)")
    
    col_controls, col_map = st.columns([1, 3])
    
    # --- 2. CONTROLS ---
    with col_controls:
        with st.form("sim_form"):
            st.subheader("⚙️ Scenario Parameters")
            
            # Month Selector (Restricted to Heat Season)
            month_map = {4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep"}
            sel_month = st.select_slider(
                "Baseline Season", 
                options=[4, 5, 6, 7, 8, 9], 
                value=6, 
                format_func=lambda x: month_map[x]
            )
            
            # BASELINE CONTEXT (The Reference Point)
            base_stats = baseline[baseline['month'] == sel_month]
            avg_t = base_stats['temp_c'].mean()
            avg_rh = base_stats['humidity_relative'].mean()
            
            st.info(f"📊 **{month_map[sel_month]} Baseline:**\n\n"
                    f"🌡️ Avg Temp: **{avg_t:.1f}°C**\n\n"
                    f"💧 Avg Humidity: **{avg_rh:.0f}%**")

            st.markdown("**Stressors**")
            d_temp = st.slider("Global Warming (°C)", 0.0, 5.0, 0.0)
            d_rh = st.slider("Humidity Shift (%)", -20, 20, 0)
            d_pop = st.slider("Population Boom (%)", 0, 50, 0)
            
            submitted = st.form_submit_button("🚀 Run Simulation", type="primary")
            
    # --- 3. SIMULATION LOGIC ---
    if submitted or 'sim_data' not in st.session_state:
        sim_df = baseline[baseline['month'] == sel_month].copy()
        
        # Apply Modifiers
        sim_df['temp_c'] += d_temp
        sim_df['humidity_relative'] = (sim_df['humidity_relative'] + d_rh).clip(0, 100)
        sim_df['population_2020'] = sim_df['population_2020'] * (1 + d_pop/100)
        sim_df['pop_log'] = np.log10(sim_df['population_2020'] + 1)
        
        # Re-calc Physics
        sim_df['heat_index_c'] = calculate_heat_index(sim_df['temp_c'], sim_df['humidity_relative'])
        sim_df['temp_roll_24h'] += d_temp
        sim_df['hi_max_72h'] = np.maximum(sim_df['hi_max_72h'], sim_df['heat_index_c'])
        
        # Lag Heuristic
        conditions = [
            (sim_df['heat_index_c'] < 27),
            (sim_df['heat_index_c'] >= 27) & (sim_df['heat_index_c'] < 32),
            (sim_df['heat_index_c'] >= 32) & (sim_df['heat_index_c'] < 41),
            (sim_df['heat_index_c'] >= 41)
        ]
        sim_df['risk_lag_1h'] = np.select(conditions, [0, 1, 2, 3], default=0)
        
        # Predict
        preds, _ = run_prediction(model, sim_df)
        sim_df['pred_risk'] = preds
        
        st.session_state['sim_data'] = sim_df

    # --- 4. MAP RENDERING ---
    df = st.session_state['sim_data']
    
    with col_map:
        # --- [RESTORED] AI CRISIS ADVISORY ---
        risk_districts = len(df[df['pred_risk'] == 3])
        
        if risk_districts > 5:
            st.error(f"🚨 **CRITICAL ALERT:** {risk_districts} districts detected at EXTREME RISK. Infrastructure failure imminent. Activate Level 3 protocols.")
        elif risk_districts > 0:
            st.warning(f"⚠️ **ADVISORY:** {risk_districts} districts requiring immediate cooling intervention. Mobilize hydration units.")
        else:
            st.success("✅ **STATUS NORMAL:** No extreme risk districts detected under current parameters.")
        # -------------------------------------

        # KPI Row
        k1, k2, k3 = st.columns(3)
        risk_pop = df[df['pred_risk'] >= 2]['population_2020'].sum()
        k1.metric("People at High Risk", f"{risk_pop/1_000_000:.1f} M")
        k2.metric("Extreme Districts", f"{risk_districts}")
        k3.metric("Avg Heat Index", f"{df['heat_index_c'].mean():.1f}°C")
        
        # PyDeck Map
        color_lookup = {
            0: [0, 204, 150, 255],    # Green
            1: [255, 193, 7, 255],    # Yellow
            2: [255, 87, 34, 255],    # Orange
            3: [183, 28, 28, 255]     # Red
        }
        
        df['fill_color'] = df['pred_risk'].map(color_lookup)
        color_dict = dict(zip(df['district_name'], df['fill_color']))
        
        for feature in geojson['features']:
            dist_name = feature['properties']['district_name']
            feature['properties']['fill_color'] = color_dict.get(dist_name, [50, 50, 50, 255])
            
            if dist_name in df['district_name'].values:
                row = df[df['district_name'] == dist_name].iloc[0]
                feature['properties']['hi'] = round(row['heat_index_c'], 1)
                feature['properties']['temp'] = round(row['temp_c'], 1)
                feature['properties']['risk_label'] = ["Safe", "Caution", "Danger", "Extreme"][int(row['pred_risk'])]
            else:
                feature['properties']['hi'] = "N/A"

        layer = pdk.Layer(
            "GeoJsonLayer",
            geojson,
            opacity=1.0,
            stroked=True,
            filled=True,
            get_fill_color="properties.fill_color",
            get_line_color=[0, 0, 0],
            get_line_width=1000,
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(latitude=30.3753, longitude=69.3451, zoom=4.5)
        
        tooltip = {
            "html": "<b>{district_name}</b><br/>Risk: {risk_label}<br/>Heat Index: {hi}°C<br/>Temp: {temp}°C",
            "style": {"backgroundColor": "#1E1E1E", "color": "white"}
        }

        st.pydeck_chart(pdk.Deck(
            layers=[layer], 
            initial_view_state=view_state, 
            tooltip=tooltip, 
            map_style="mapbox://styles/mapbox/dark-v10"
        ))