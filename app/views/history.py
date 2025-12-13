import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_history, load_map_geojson, load_model
from utils.model_engine import run_prediction, calculate_heat_index

def show():
    # TERMINAL HEADER
    st.markdown("""
    <div style='border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;'>
        <h2 style='margin:0; color: white; font-family: Roboto Mono;'>// FORENSIC_LOGS <span style='font-size: 14px; color: #FF00FF;'>[ARCHIVE_MOUNTED]</span></h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Load Data
    with st.spinner("DECRYPTING_ARCHIVE..."):
        hist_df = load_history()
        geojson = load_map_geojson()
        model = load_model()

    # 2. Data Polish
    hist_df['district_name'] = hist_df['district_name'].str.strip().str.title()
    
    # 3. Run AI Prediction
    preds, _ = run_prediction(model, hist_df)
    hist_df['pred_risk'] = preds
    hist_df['heat_index_c'] = calculate_heat_index(hist_df['temp_c'], hist_df['humidity_relative'])

    # 4. OPTIMIZATION: Resample to 4-Hour Intervals
    hist_df['time_group'] = hist_df['time'].dt.floor('4h')
    
    anim_df = hist_df.groupby(['district_name', 'time_group']).agg({
        'pred_risk': 'max',      
        'heat_index_c': 'max',   
        'temp_c': 'max',
        'population_2020': 'first'
    }).reset_index()
    
    anim_df['time_str'] = anim_df['time_group'].dt.strftime('%Y-%m-%d %H:00')
    anim_df = anim_df.sort_values('time_group')

    # 5. Render Native Plotly Animation (Terminal Style)
    fig = px.choropleth(
        anim_df,
        geojson=geojson,
        locations='district_name',
        featureidkey="properties.district_name",
        color='pred_risk',
        animation_frame='time_str',
        # NEON PALETTE
        color_continuous_scale=[
            (0.00, "#00CC96"), # Neon Teal
            (0.33, "#FFC107"), # Neon Gold
            (0.66, "#FF5722"), # Neon Orange
            (1.00, "#D50000")  # Neon Red
        ],
        range_color=(0, 3),
        title="[PLAYBACK] EVENT_ID: KARACHI_2015",
        projection="mercator",
        hover_data={
            'pred_risk': False,
            'heat_index_c': ':.1f',
            'temp_c': ':.1f',
            'population_2020': ':,'
        },
        labels={'heat_index_c': 'HEAT_IDX', 'time_str': 'TIMESTAMP'}
    )
    
    # ... [Keep everything above the fig = px.choropleth(...) part] ...

    # TERMINAL MAP STYLING (Fixed Layout)
    fig.update_geos(
        fitbounds="locations", 
        visible=False, 
        bgcolor="#000000"
    )
    
    fig.update_layout(
        template="plotly_dark",

        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        geo_bgcolor="#000000",
        height=650,
        font={'family': "Roboto Mono", 'color': "white"},
        
        # 1. Legend Styling
        coloraxis_colorbar=dict(
            title=dict(text="RISK_LEVEL", font=dict(family="Roboto Mono")),
            tickvals=[0, 1, 2, 3],
            ticktext=["SAFE", "CAUTION", "DANGER", "EXTREME"],
            tickfont=dict(family="Roboto Mono"),
            # Position the legend to the right
            x=1.0, 
            y=0.5
        ),
        
        # 2. Player Styling (Buttons) - FIXED POSITION & COLOR

        # 2. Player Styling (Buttons)
        updatemenus=[{
            "type": "buttons",
            "direction": "left",
            "showactive": False,  # <--- THIS IS THE MAGIC FIX. KILLS THE WHITE HIGHLIGHT.
            "x": 0.1,
            "y": 0,
            "xanchor": "right",
            "yanchor": "top",
            "pad": {"t": 0, "r": 10},
            
            # Styling the Buttons themselves
            "bgcolor": "#000000",      # Keep inactive buttons Pitch Black
            "bordercolor": "#333333",  # Subtle Grey Border
            "borderwidth": 1,
            "font": {"color": "#00FF41", "family": "Roboto Mono"}, # Green Text
            
            "buttons": [
                {
                    "label": "▶ EXEC",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 150, "redraw": True}, "fromcurrent": True}]
                },
                {
                    "label": "II HALT",
                    "method": "animate",
                    "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}]
                }
            ]
        }],
        
        # 3. Slider Styling (Timeline)
        sliders=[{
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {
                "font": {"size": 14, "color": "#00FF41", "family": "Roboto Mono"},
                "prefix": ">> SYSTEM_TIME: ",
                "visible": True,
                "xanchor": "right"
            },
            "transition": {"duration": 150, "easing": "cubic-in-out"},
            "pad": {"b": 10, "t": 0}, # Tighter padding
            "len": 0.9,
            "x": 0.1, # Starts right after the buttons
            "y": 0,
            "steps": [
                {
                    "args": [
                        [t],
                        {"frame": {"duration": 150, "redraw": True}, "mode": "immediate", "transition": {"duration": 150}}
                    ],
                    "label": t,
                    "method": "animate"
                }
                for t in anim_df['time_str'].unique()
            ],
            "bgcolor": "#222",         # Dark slider track
            "activebgcolor": "#00FF41", # Green active track
            "bordercolor": "#333",
            "font": {"color": "white", "family": "Roboto Mono"}
        }]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Footer Note
    st.markdown("""
    <div style="font-family: Roboto Mono; font-size: 12px; color: #666; margin-top: -10px; border-top: 1px solid #333; padding-top: 10px;">
        ℹ [SYSTEM_NOTE] TIMELINE RESAMPLED (4H INTERVALS) FOR RENDERING PERFORMANCE.
    </div>
    """, unsafe_allow_html=True)