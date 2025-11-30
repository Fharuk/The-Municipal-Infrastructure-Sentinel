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

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Sentinel Control")
    
    if st.session_state.agent:
        st.success("System Online (Secure Key)")
    else:
        st.error("System Offline: Missing Key")

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

# --- TAB 1: CITIZEN REPORTING ---
with tab_citizen:
    col_input, col_analysis = st.columns([1, 1])
    
    with col_input:
        st.subheader("New Incident Report")
        
        reporter_name = st.text_input("Your Name (For Leaderboard)", value="Anonymous")
        
        # Enhanced Input Section
        st.markdown("---")
        st.caption("Incident Details")
        location_name = st.text_input("Location Name", placeholder="e.g., Junction of Broad St & Marina")
        user_notes = st.text_area("Description", placeholder="Describe the issue (e.g., Deep hole causing traffic, drainage blocked by trash)")
        
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
                    
                    if not vision_result.get('is_relevant', True):
                        st.error("❌ Image Rejected: Not identified as municipal infrastructure.")
                    else:
                        defect = vision_result.get('defect_type', 'Unknown')
                        severity = vision_result.get('severity_score', 0)
                        st.info(f"Detected: **{defect}** | Severity: **{severity}/10**")
                        
                        with st.spinner("AI Planner calculating priority..."):
                            priority_result = st.session_state.agent.prioritization_agent(vision_result, location_type)
                            
                            # Pass new fields to CityManager
                            report = st.session_state.city.add_report(
                                lat, lon, vision_result, priority_result, reporter_name,
                                location_name=location_name, user_notes=user_notes
                            )
                            
                            if report:
                                if report['priority'] > 80:
                                    st.balloons()
                                    st.error(f"🚨 Priority: {report['priority']} (Immediate)")
                                else:
                                    st.success(f"✅ Priority: {report['priority']} (Logged)")
                                
                                st.write(f"**Justification:** {priority_result.get('justification')}")
                                st.success("Report logged. Thank you for your contribution!")

# --- TAB 2: GOVERNMENT DASHBOARD ---
with tab_gov:
    st.subheader("Operational Heatmap")
    
    df = st.session_state.city.get_dataframe()
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        # Check if 'type' column exists before filtering
        if 'type' in df.columns:
            type_filter = st.multiselect("Filter by Type", options=df['type'].unique() if not df.empty else [])
    with col_filter2:
        # Check if 'status' column exists before filtering
        if 'status' in df.columns:
            status_filter = st.multiselect("Filter by Status", options=["New", "Pending", "In Progress", "Resolved"])

    if not df.empty:
        if 'type' in df.columns and type_filter:
            df = df[df['type'].isin(type_filter)]
        if 'status' in df.columns and status_filter:
            df = df[df['status'].isin(status_filter)]

    # Map
    if not df.empty:
        center_lat = df['lat'].mean()
        center_lon = df['lon'].mean()
    else:
        center_lat, center_lon = 6.5244, 3.3792

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    if not df.empty:
        for _, row in df.iterrows():
            color = "red" if row['priority'] > 80 else "orange" if row['priority'] > 50 else "green"
            
            # --- BUG FIX START ---
            # Use .get() to safely access keys that might be missing in old records
            loc_name = row.get('location_name', 'Unknown Location')
            notes = row.get('user_notes', 'No description provided.')
            # --- BUG FIX END ---

            # Enhanced Popup with User Details
            popup_html = f"""
            <b>{row['type']}</b><br>
            Loc: {loc_name}<br>
            Note: {notes}<br>
            Priority: {row['priority']}<br>
            Status: {row['status']}
            """
            folium.Marker(
                [row['lat'], row['lon']],
                popup=popup_html,
                tooltip=f"{row['type']} ({row['severity']}/10)",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)

    st_folium(m, width=1000, height=500)
    
    # Dispatch Panel
    st.subheader("Dispatch Command Center")
    if not df.empty:
        col_list, col_action = st.columns([2, 1])
        with col_list:
            # Filter columns to only show existing ones to prevent KeyError
            cols_to_show = ['id', 'type', 'priority', 'location_name', 'user_notes', 'status']
            available_cols = [c for c in cols_to_show if c in df.columns]
            
            st.dataframe(
                df[available_cols], 
                hide_index=True, use_container_width=True
            )
        
        with col_action:
            st.markdown("#### Action Panel")
            if 'status' in df.columns and 'id' in df.columns:
                report_ids = df[df['status'] != 'Resolved']['id'].tolist()
                if report_ids:
                    selected_id = st.selectbox("Select Report ID", report_ids)
                    new_status = st.selectbox("Update Status", ["In Progress", "Resolved", "False Alarm"])
                    if st.button("Update & Dispatch"):
                        st.session_state.city.update_status(selected_id, new_status)
                        st.success(f"Updated {selected_id}")
                        st.rerun()