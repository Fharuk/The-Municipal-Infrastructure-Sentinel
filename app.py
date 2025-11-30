import streamlit as st
from PIL import Image
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import logging

# Internal Modules
from civic_agent_core import CivicAgentCore
from city_manager import CityManager

# Page Config
st.set_page_config(layout="wide", page_title="Municipal Sentinel")
logger = logging.getLogger(__name__)

# --- SECURE INIT ---
def get_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
    return None

api_key = get_api_key()

if 'city' not in st.session_state:
    st.session_state.city = CityManager()

if 'agent' not in st.session_state:
    if api_key:
        st.session_state.agent = CivicAgentCore(api_key)
    else:
        st.session_state.agent = None

# --- SIDEBAR (Gamified) ---
with st.sidebar:
    st.title("🛡️ Sentinel Control")
    
    if st.session_state.agent:
        st.success("System Online (Secure Key)")
    else:
        st.error("System Offline")

    st.markdown("---")
    st.subheader("📊 Live Impact")
    stats = st.session_state.city.get_stats()
    c1, c2 = st.columns(2)
    c1.metric("Reports", stats['total'])
    c2.metric("Critical", stats['critical'])
    
    st.markdown("---")
    st.subheader("🏆 Top Reporters")
    leaderboard = st.session_state.city.get_leaderboard()
    if not leaderboard.empty:
        st.dataframe(leaderboard, hide_index=True, use_container_width=True)

# --- MAIN UI ---
st.title("🏙️ Municipal Infrastructure Sentinel")
st.markdown("AI-Powered Infrastructure Triage System. **Map Provider: OpenStreetMap**")

tab_citizen, tab_gov = st.tabs(["📢 Citizen Reporter", "🗺️ Government Command"])

# --- TAB 1: CITIZEN REPORTING (Path A) ---
with tab_citizen:
    col_input, col_analysis = st.columns([1, 1])
    
    with col_input:
        st.subheader("New Incident Report")
        
        # Gamification: Identity
        reporter_name = st.text_input("Your Name (For Leaderboard)", value="Anonymous")
        
        img_file = st.file_uploader("Upload Scene Photo", type=['jpg', 'png', 'jpeg'])
        
        st.caption("Location Metadata (Simulated GPS)")
        lat = st.number_input("Latitude", value=6.5244, format="%.4f")
        lon = st.number_input("Longitude", value=3.3792, format="%.4f")
        location_type = st.selectbox("Context", ["Highway", "Residential", "Market", "School Zone"])
        
        submit_btn = st.button("Analyze & Submit")

    with col_analysis:
        if submit_btn and img_file:
            if not st.session_state.agent:
                st.error("AI Agent not initialized.")
            else:
                image = Image.open(img_file)
                st.image(image, caption="Evidence", width=300)
                
                with st.spinner("AI Vision analyzing defect..."):
                    vision_result = st.session_state.agent.vision_agent(image)
                    
                    # 1. Relevance Check
                    if not vision_result.get('is_relevant', True):
                        st.error("❌ Image Rejected: Not identified as municipal infrastructure.")
                        st.stop()

                    defect = vision_result.get('defect_type', 'Unknown')
                    severity = vision_result.get('severity_score', 0)
                    st.info(f"Detected: **{defect}** | Severity: **{severity}/10**")
                    
                with st.spinner("AI Planner calculating priority..."):
                    priority_result = st.session_state.agent.prioritization_agent(vision_result, location_type)
                    
                    # Save to Memory
                    report = st.session_state.city.add_report(lat, lon, vision_result, priority_result, reporter_name)
                    
                    if report:
                        # Gamification: Celebration
                        if report['priority'] > 80:
                            st.balloons()
                            st.error(f"🚨 Priority: {report['priority']} (Immediate)")
                        else:
                            st.success(f"✅ Priority: {report['priority']} (Logged)")
                        
                        st.write(f"**Justification:** {priority_result.get('justification')}")
                        st.info(f"Thank you, {reporter_name}! You earned +10 Impact Points.")

# --- TAB 2: GOVERNMENT DASHBOARD (Path B) ---
with tab_gov:
    st.subheader("Operational Heatmap")
    
    # 1. Filters (Operational Pivot)
    df = st.session_state.city.get_dataframe()
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        type_filter = st.multiselect("Filter by Defect Type", options=df['type'].unique() if not df.empty else [])
    with col_filter2:
        status_filter = st.multiselect("Filter by Status", options=["New", "Pending", "In Progress", "Resolved"])

    # Apply Filters
    if not df.empty:
        if type_filter:
            df = df[df['type'].isin(type_filter)]
        if status_filter:
            df = df[df['status'].isin(status_filter)]

    # 2. Map
    if not df.empty:
        center_lat = df['lat'].mean()
        center_lon = df['lon'].mean()
    else:
        center_lat, center_lon = 6.5244, 3.3792

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    if not df.empty:
        for _, row in df.iterrows():
            color = "red" if row['priority'] > 80 else "orange" if row['priority'] > 50 else "green"
            # Add Status to popup
            popup_html = f"<b>{row['type']}</b><br>Priority: {row['priority']}<br>Status: {row['status']}<br>ID: {row['id']}"
            folium.Marker(
                [row['lat'], row['lon']],
                popup=popup_html,
                tooltip=f"{row['type']} ({row['severity']}/10)",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)

    st_folium(m, width=1000, height=500)
    
    # 3. Dispatch Command Center (Operational Pivot)
    st.subheader("Dispatch Command Center")
    if not df.empty:
        col_list, col_action = st.columns([2, 1])
        
        with col_list:
            st.dataframe(
                df[['id', 'type', 'priority', 'dept', 'status', 'lat', 'lon']].sort_values(by="priority", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        
        with col_action:
            st.markdown("#### Action Panel")
            # Select Report
            report_ids = df[df['status'] != 'Resolved']['id'].tolist()
            if report_ids:
                selected_id = st.selectbox("Select Report ID", report_ids)
                new_status = st.selectbox("Update Status", ["In Progress", "Resolved", "False Alarm"])
                
                if st.button("Update & Dispatch"):
                    if st.session_state.city.update_status(selected_id, new_status):
                        st.success(f"Report {selected_id} updated to '{new_status}'")
                        st.rerun()
            else:
                st.info("No pending reports available for dispatch.")