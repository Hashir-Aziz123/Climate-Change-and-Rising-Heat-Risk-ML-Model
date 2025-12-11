import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_history, load_map_geojson, load_model
from utils.model_engine import run_prediction, calculate_heat_index

def show():
    st.markdown("## 🎬 History Lab: 2015 Heatwave Replay")
    
    # 1. Load Data
    with st.spinner("Loading Forensic Archive..."):
        hist_df = load_history()
        geojson = load_map_geojson()
        model = load_model()

    # 2. Data Polish (Fixing the "Gray Map" issue)
    # Ensure district names match the Map (Title Case)
    hist_df['district_name'] = hist_df['district_name'].str.strip().str.title()
    
    # 3. Run AI Prediction
    # We calculate risk for the raw data first
    preds, _ = run_prediction(model, hist_df)
    hist_df['pred_risk'] = preds
    
    # Calculate Heat Index for the tooltip (Visualization only)
    hist_df['heat_index_c'] = calculate_heat_index(hist_df['temp_c'], hist_df['humidity_relative'])

    # 4. OPTIMIZATION: Resample to 4-Hour Intervals
    # Problem: Hourly animation (360 frames) is too slow to load.
    # Solution: Group by 4 hours. We take the MAX risk in that window (Safety first).
    
    # Create 4H grouping key
    hist_df['time_group'] = hist_df['time'].dt.floor('4h')
    
    # Aggregate
    anim_df = hist_df.groupby(['district_name', 'time_group']).agg({
        'pred_risk': 'max',          # Show worst risk in the 4h block
        'heat_index_c': 'max',       # Show peak heat
        'temp_c': 'max',
        'population_2020': 'first'   # Static data
    }).reset_index()
    
    # Create readable Timeline String (e.g., "Jun 18, 16:00")
    anim_df['time_str'] = anim_df['time_group'].dt.strftime('%b %d, %H:00')
    anim_df = anim_df.sort_values('time_group')

    # 5. Render Native Plotly Animation
    # Since data is now 4x smaller, this will load fast and play smoothly
    fig = px.choropleth(
        anim_df,
        geojson=geojson,
        locations='district_name',
        featureidkey="properties.district_name",
        color='pred_risk',
        animation_frame='time_str', # The Built-in Player
        color_continuous_scale=[
            (0.00, "#00cc96"), # Safe
            (0.33, "#ffc107"), # Caution
            (0.66, "#ff5722"), # Danger
            (1.00, "#b71c1c")  # Extreme
        ],
        range_color=(0, 3),
        title="Forensic Reconstruction: June 15-30, 2015 (4-Hour Intervals)",
        projection="mercator",
        hover_data={
            'pred_risk': False,
            'heat_index_c': ':.1f',
            'temp_c': ':.1f',
            'population_2020': ':,'
        },
        labels={'heat_index_c': 'Heat Index', 'time_str': 'Time'}
    )
    
    # Map Styling
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="#0E1117",
        geo_bgcolor="#0E1117",
        height=650,
        coloraxis_colorbar=dict(
            title="Risk Level",
            tickvals=[0, 1, 2, 3],
            ticktext=["Safe", "Caution", "Danger", "Extreme"]
        ),
        # Player Styling
        updatemenus=[{
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True}],
                    "label": "▶ Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                    "label": "⏸ Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("ℹ️ Animation resampled to 4-hour intervals for optimal performance.")