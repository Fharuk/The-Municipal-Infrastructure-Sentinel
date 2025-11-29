import streamlit as st
from PIL import Image
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
import logging

# Firebase Imports
from firebase_admin import credentials, initialize_app, firestore
from firebase_admin import auth as firebase_auth

# Internal Modules
from civic_agent_core import CivicAgentCore
from city_manager import CityManager

# Page Config
st.set_page_config(layout="wide", page_title="Municipal Sentinel")
logger = logging.getLogger(__name__)

# --- FIREBASE INIT ---
def init_firebase():
    """Initializes Firebase."""
    if 'firebase_initialized' in st.session_state:
        return firestore.client(), st.session_state.user_id

    try:
        app_id = os.environ.get('__app_id', 'default-app-id')
        firebase_config_str = os.environ.get('__firebase_config')
        auth_token = os.environ.get('__initial_auth_token')
        
        if not firebase_config_str:
            return None, "anonymous"

        firebase_config = json.loads(firebase_config_str)
        if not firestore._apps:
            cred = credentials.Certificate(firebase_config)
            initialize_app(cred)

        db = firestore.client()
        
        # Auth (Simplified for demo)
        user_id = "anonymous"
        if auth_token:
            try:
                decoded = firebase_auth.verify_id_token(auth_token)
                user_id = decoded['uid']
            except: pass

        st.session_state.app_id = app_id
        st.session_state.user_id = user_id
        st.session_state.firebase_initialized = True
        return db, user_id
    except Exception as e:
        st.error(f"DB Error: {e}")
        return None, None

# Initialize
db, user_id = init_firebase()
if 'city' not in st.session_state:
    st.session_state.city = CityManager(db)
if 'agent' not in st.session_state:
    st.session_state.agent = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Sentinel Control")
    st.markdown("Enter Gemini API Key to enable AI analysis.")
    api_key = st.text_input("API Key", type="password")
    
    if st.button("Initialize System"):
        if api_key:
            st.session_state.agent = CivicAgentCore(api_key)
            st.success(" AI Agents Online")
        else:
            st.warning("Key required.")

    st.markdown("---")
    if db:
        stats = st.session_state.city.get_stats()
        st.metric("Active Reports", stats['total'])
        st.metric("Critical Issues", stats['critical'])
    else:
        st.error("Database Offline")

# --- MAIN UI ---
st.title("🏙️ Municipal Infrastructure Sentinel")
st.markdown("AI-Powered Infrastructure Triage System. **Map Provider: OpenStreetMap**")

tab_citizen, tab_gov = st.tabs(["📢 Citizen Reporter", "🗺️ Government Dashboard"])

# --- TAB 1: REPORTING ---
with tab_citizen:
    col_input, col_analysis = st.columns([1, 1])
    
    with col_input:
        st.subheader("New Incident Report")
        img_file = st.file_uploader("Upload Scene Photo", type=['jpg', 'png', 'jpeg'])
        
        st.caption("Location Metadata (Simulated GPS)")
        # Default to a generic coordinate (e.g., Lagos)
        lat = st.number_input("Latitude", value=6.5244, format="%.4f")
        lon = st.number_input("Longitude", value=3.3792, format="%.4f")
        location_type = st.selectbox("Context", ["Highway", "Residential", "Market", "School Zone"])
        
        submit_btn = st.button("Analyze & Submit")

    with col_analysis:
        if submit_btn and img_file and st.session_state.agent:
            image = Image.open(img_file)
            st.image(image, caption="Evidence", width=300)
            
            with st.spinner("AI Vision analyzing defect..."):
                vision_result = st.session_state.agent.vision_agent(image)
                st.info(f"Detected: **{vision_result.get('defect_type')}**")
                
            with st.spinner("AI Planner calculating priority..."):
                priority_result = st.session_state.agent.prioritization_agent(vision_result, location_type)
                
                # Save to Firestore
                report = st.session_state.city.add_report(lat, lon, vision_result, priority_result, user_id)
                
                if report:
                    if report['priority'] > 80:
                        st.error(f"🚨 Priority: {report['priority']} (Immediate)")
                    else:
                        st.success(f"✅ Priority: {report['priority']} (Logged)")
                    st.write(f"**Justification:** {priority_result.get('justification')}")

# --- TAB 2: MAP DASHBOARD ---
with tab_gov:
    st.subheader("Operational Heatmap (OSM)")
    
    # 1. Map Visualization
    df = st.session_state.city.get_dataframe()
    
    if not df.empty:
        center_lat = df['lat'].mean()
        center_lon = df['lon'].mean()
    else:
        center_lat, center_lon = 6.5244, 3.3792

    # Create Map (OpenStreetMap is default tile)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    if not df.empty:
        for _, row in df.iterrows():
            color = "red" if row['priority'] > 80 else "orange" if row['priority'] > 50 else "green"
            folium.Marker(
                [row['lat'], row['lon']],
                popup=f"<b>{row['type']}</b><br>Priority: {row['priority']}",
                tooltip=f"Severity: {row['severity']}",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)

    st_folium(m, width=1000, height=500)
    
    # 2. Data Table
    if not df.empty:
        st.dataframe(
            df[['type', 'priority', 'dept', 'status', 'lat', 'lon']].sort_values(by="priority", ascending=False),
            use_container_width=True,
            hide_index=True
        )