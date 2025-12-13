import streamlit as st
from utils.data_loader import load_model
from views import dashboard, live_monitor, history

# --- CONFIG ---
st.set_page_config(
    page_title="Pakistan Heat Risk Command Center",
    page_icon="🔥", # Favicon can stay, it's tiny
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("app/style.css")

# --- SIDEBAR NAVIGATION (TERMINAL STYLE) ---
st.sidebar.markdown("### SELECT_MODULE")
st.sidebar.markdown("---")

# CLI Style Navigation
# No Emojis. Just Brackets and Slashes.
page = st.sidebar.radio(
    "SELECT_MODULE", 
    ["SIMULATION_ZONE", "LIVE_UPLINK", "HISTORICAL_PRESENTATION"],
)

st.sidebar.markdown("---")
st.sidebar.code("v2.1.0 | STABLE_BUILD")

# --- ROUTING ---
if page == "SIMULATION_ZONE":
    dashboard.show()
elif page == "LIVE_UPLINK":
    live_monitor.show()
elif page == "HISTORICAL_PRESENTATION":
    history.show()