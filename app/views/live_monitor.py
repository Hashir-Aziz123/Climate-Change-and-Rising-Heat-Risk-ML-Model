import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from utils.data_loader import load_coords, load_model, load_baseline_data
from utils.model_engine import calculate_heat_index, run_prediction

def show():
    st.markdown("## 📡 Real-Time Live Monitor")
    
    coords = load_coords()
    model = load_model()
    baseline = load_baseline_data()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        target = st.selectbox("Select Target District", sorted(coords.index))
        
        if st.button("🔴 CONNECT SATELLITE", type="primary"):
            with st.spinner("Establishing Uplink..."):
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
                    st.error(f"Connection Failed: {e}")

    # Display Results
    if 'live_result' in st.session_state:
        res = st.session_state['live_result']
        
        risk_labels = {0: "Safe", 1: "Caution", 2: "Danger", 3: "Extreme"}
        risk_colors = {0: "#00cc96", 1: "#ffc107", 2: "#ff5722", 3: "#b71c1c"}
        
        with col2:
            st.markdown(f"### Status: <span style='color:{risk_colors[res['risk']]}'>{risk_labels[res['risk']]}</span>", unsafe_allow_html=True)
            
            # Added Solar Metric Here
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Temp", f"{res['temp']}°C")
            m2.metric("Humidity", f"{res['rh']}%")
            m3.metric("Solar Rad", f"{res['solar']} W/m²")
            m4.metric("Heat Index", f"{res['hi']:.1f}°C")
            
            # Gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = res['hi'],
                title = {'text': "Heat Stress Index"},
                gauge = {'axis': {'range': [0, 60]}, 'bar': {'color': risk_colors[res['risk']]}}
            ))
            fig.update_layout(height=300, margin={"t":0,"b":0}, paper_bgcolor="#0E1117")
            st.plotly_chart(fig, use_container_width=True)