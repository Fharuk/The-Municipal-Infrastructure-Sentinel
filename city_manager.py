import pandas as pd
import logging
import streamlit as st
import datetime

logger = logging.getLogger(__name__)

class CityManager:
    """
    Manages the state of infrastructure reports in memory (Session State).
    """
    def __init__(self):
        # Initialize session state storage if it doesn't exist
        if 'reports_db' not in st.session_state:
            st.session_state.reports_db = []
            self.seed_mock_data()

    def seed_mock_data(self):
        """Populates the database with realistic mock data."""
        mock_data = [
            {
                "lat": 6.5244, "lon": 3.3792, "type": "Pothole", "severity": 8, "priority": 85.0, 
                "dept": "Works", "status": "Pending", "reporter": "Ahmed",
                "loc_name": "Third Mainland Bridge Ramp", "notes": "Causing severe traffic backlog."
            },
            {
                "lat": 6.4281, "lon": 3.4219, "type": "Flooding", "severity": 6, "priority": 60.0, 
                "dept": "Sanitation", "status": "In Progress", "reporter": "Chidinma",
                "loc_name": "Adetokunbo Ademola St", "notes": "Drainage blocked by waste."
            },
        ]
        
        for data in mock_data:
            self.add_report(
                data['lat'], data['lon'],
                {"defect_type": data['type'], "severity_score": data['severity'], "description": "AI Analysis", "estimated_material_needed": "Standard"},
                {"priority_index": data['priority'], "assigned_department": data['dept'], "justification": "Mock Data"},
                data['reporter'],
                location_name=data['loc_name'],
                user_notes=data['notes']
            )

    # UPDATED SIGNATURE: Added location_name and user_notes with defaults
    def add_report(self, lat: float, lon: float, vision_data: dict, priority_data: dict, user_id: str, location_name: str = "Unknown", user_notes: str = ""):
        """Adds a new report with user-provided context."""
        new_report = {
            "id": f"R{len(st.session_state.reports_db) + 1:03d}",
            "lat": lat,
            "lon": lon,
            "location_name": location_name, 
            "user_notes": user_notes,       
            "type": vision_data.get('defect_type', 'Unknown'),
            "severity": vision_data.get('severity_score', 0),
            "priority": priority_data.get('priority_index', 0.0),
            "dept": priority_data.get('assigned_department', 'General'),
            "ai_desc": vision_data.get('description'),
            "material": vision_data.get('estimated_material_needed'),
            "status": "New",
            "justification": priority_data.get('justification'),
            "timestamp": datetime.datetime.now().isoformat(),
            "reporter_id": user_id
        }
        st.session_state.reports_db.append(new_report)
        return new_report

    def update_status(self, report_id: str, new_status: str):
        for report in st.session_state.reports_db:
            if report['id'] == report_id:
                report['status'] = new_status
                return True
        return False

    def get_dataframe(self):
        if not st.session_state.reports_db:
            return pd.DataFrame()
        return pd.DataFrame(st.session_state.reports_db)

    def get_stats(self):
        df = self.get_dataframe()
        if df.empty:
            return {"total": 0, "critical": 0, "avg_severity": 0}
        return {
            "total": len(df),
            "critical": len(df[df['priority'] > 80]),
            "avg_severity": df['severity'].mean()
        }

    def get_leaderboard(self):
        df = self.get_dataframe()
        if df.empty:
            return pd.DataFrame()
        return df['reporter_id'].value_counts().reset_index(name='count').rename(columns={'index': 'Reporter', 'reporter_id': 'Reporter'})