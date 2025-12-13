import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from utils.data_loader import load_coords, load_model, load_baseline_data
from utils.model_engine import calculate_heat_index, run_prediction

def show():
    # TERMINAL HEADER
    st.markdown("""
    <div style='border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;'>
        <h2 style='margin:0; color: white; font-family: Roboto Mono;'>LIVE_UPLINK <span style='font-size: 14px; color: #00F0FF;'>[STANDBY]</span></h2>
    </div>
    """, unsafe_allow_html=True)
    
    coords = load_coords()
    model = load_model()
    baseline = load_baseline_data()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.markdown("**>> TARGET_SELECTION**")
            target = st.selectbox("SECTOR_COORDINATES", sorted(coords.index))
            
            st.write("")
            st.write("")
            if st.button(" INITIATE_CONNECTION", type="primary"):
                with st.spinner("ESTABLISHING HANDSHAKE..."):
                    lat = coords.loc[target]['lat']
                    lon = coords.loc[target]['lon']
                    
                    # API Call
                    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,direct_radiation"
                    
                    try:
                        r = requests.get(url, timeout=5)
                        data = r.json()['current']
                        
                        # Process
                        temp = data['temperature_2m']
                        rh = data['relative_humidity_2m']
                        wind = data['wind_speed_10m'] / 3.6
                        solar = data['direct_radiation']
                        
                        # Logic
                        hi = calculate_heat_index(temp, rh)
                        base_info = baseline[baseline['district_name'] == target].iloc[0]
                        pop = base_info['population_2020']
                        
                        # Build Input
                        input_row = pd.DataFrame([{
                            'population_2020': pop,
                            'pop_log': np.log10(pop + 1),
                            'temp_c': temp,
                            'humidity_relative': rh,
                            'wind_speed_m_s': wind,
                            'solar_w_m2': solar,
                            'temp_roll_24h': temp,
                            'hi_max_72h': hi,
                            'risk_lag_1h': 0
                        }])
                        
                        # Predict
                        pred, prob = run_prediction(model, input_row)
                        risk_class = pred[0]
                        
                        st.session_state['live_result'] = {
                            'temp': temp, 'rh': rh, 'hi': hi, 'solar': solar, 
                            'risk': risk_class, 'district': target
                        }
                        
                    except Exception as e:
                        st.error(f"[CONNECTION_FAILURE] {e}")

    # Display Results
    if 'live_result' in st.session_state:
        res = st.session_state['live_result']
        
        # --- NEON PALETTE ---
        risk_labels = {0: "SAFE", 1: "CAUTION", 2: "DANGER", 3: "EXTREME"}
        risk_colors = {
            0: "#00CC96", # Neon Teal
            1: "#FFC107", # Neon Amber
            2: "#FF5722", # Neon Orange
            3: "#D50000"  # Neon Red
        }
        
        color = risk_colors[res['risk']]
        label = risk_labels[res['risk']]
        
        with col2:
            # STATUS BOX
            st.markdown(f"""
            <div style="border: 1px solid {color}; color: {color}; padding: 15px; margin-bottom: 20px; font-family: Roboto Mono; background: #000;">
                <span style="font-weight:bold;">[SYSTEM_STATUS]</span> {label}. SECTOR {res['district'].upper()} MONITORING ACTIVE.
            </div>
            """, unsafe_allow_html=True)
            
            # METRICS ROW
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TEMP [C]", f"{res['temp']}")
            m2.metric("HUMIDITY [%]", f"{res['rh']}")
            m3.metric("SOLAR [W/m2]", f"{res['solar']}")
            m4.metric("HEAT_INDEX", f"{res['hi']:.1f}")
            
            # GAUGE CHART (FIXED CLIPPING)
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", 
                value = res['hi'],
                title = {'text': "THERMAL_STRESS_INDEX", 'font': {'color': '#888', 'size': 12}}, # Smaller Title
                gauge = {
                    'axis': {'range': [0, 60], 'tickcolor': '#333'},
                    'bar': {'color': color},
                    'bgcolor': "#000",
                    'borderwidth': 2,
                    'bordercolor': "#333",
                    'steps': [
                        {'range': [0, 27], 'color': '#00CC96'},
                        {'range': [27, 32], 'color': '#FFC107'},
                        {'range': [32, 41], 'color': '#FF5722'},
                        {'range': [41, 60], 'color': '#D50000'}
                    ],
                }
            ))
            
            fig.update_layout(
                height=220, # Slightly smaller height to fit container
                margin={"t": 30, "b": 10, "l": 30, "r": 30}, # Optimized Margins to prevent clipping
                paper_bgcolor="#000000",
                font={'family': "Roboto Mono", 'color': "white"}
            )
            st.plotly_chart(fig, use_container_width=True)