# app/main.py
import streamlit as st
from utils.data_loader import load_model
# Import views (We will write these next)
from views import dashboard, live_monitor, history

# --- CONFIG ---
st.set_page_config(
    page_title="Pakistan Heat Risk Command Center",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("app/style.css")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🔥 Command Center")
st.sidebar.markdown("Theme 2: Climate Resilience")

# Navigation Menu
page = st.sidebar.radio(
    "Mission Control", 
    ["🕹️ Simulation Lab", "📡 Live Monitor", "🎬 History Lab"]
)

st.sidebar.markdown("---")
st.sidebar.info("v2.0 | Powered by Random Forest / XGBoost")

# --- ROUTING ---
if page == "🕹️ Simulation Lab":
    dashboard.show()
elif page == "📡 Live Monitor":
    live_monitor.show()
elif page == "🎬 History Lab":
    history.show()