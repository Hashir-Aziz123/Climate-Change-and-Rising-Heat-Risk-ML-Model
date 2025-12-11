# app/utils/data_loader.py
import streamlit as st
import pandas as pd
import joblib
import json
import os

@st.cache_resource
def load_model():
    """Loads the trained ML model."""
    path = "models/heat_risk_model.pkl"
    if not os.path.exists(path):
        st.error("🚨 Model not found! Please check 'models/' folder.")
        return None
    return joblib.load(path)

@st.cache_resource
def load_map_geojson():
    """Loads the optimized district map."""
    path = "app/data/pakistan_districts.geojson"
    if not os.path.exists(path):
        st.error("🚨 Map GeoJSON not found!")
        return None
    with open(path, 'r') as f:
        return json.load(f)

@st.cache_data
def load_baseline_data():
    """Loads the 2023 seasonal baseline."""
    return pd.read_csv("app/data/app_baseline.csv")

@st.cache_data
def load_coords():
    """Loads Lat/Lon for Live Monitor."""
    return pd.read_csv("app/data/district_coords.csv").set_index('district_name')

@st.cache_data
def load_history():
    """Loads 2015 heatwave slice."""
    df = pd.read_csv("app/data/app_history_2015.csv")
    df['time'] = pd.to_datetime(df['time'])
    return df.sort_values('time')