import pandas as pd
import logging
import streamlit as st
from google.cloud import firestore

logger = logging.getLogger(__name__)

class CityManager:
    """
    Manages the state of infrastructure reports using Firebase Firestore.
    """
    def __init__(self, db_client):
        self.db = db_client
        self.collection_name = 'municipal_reports'

    def add_report(self, lat: float, lon: float, vision_data: dict, priority_data: dict, user_id: str):
        """Adds a new report to Firestore."""
        if not self.db:
            logger.error("Database client not initialized.")
            return None

        # Firestore Path: /artifacts/{appId}/public/data/municipal_reports (Public Shared Data)
        # Using public path so all users (Government & Citizens) see the same heatmap.
        app_id = st.session_state.get('app_id', 'default-app-id')
        collection_path = f"artifacts/{app_id}/public/data/{self.collection_name}"
        
        new_report = {
            "lat": lat,
            "lon": lon,
            "type": vision_data.get('defect_type', 'Unknown'),
            "severity": vision_data.get('severity_score', 0),
            "priority": priority_data.get('priority_index', 0.0),
            "dept": priority_data.get('assigned_department', 'General'),
            "desc": vision_data.get('description'),
            "material": vision_data.get('estimated_material_needed'),
            "status": "New",
            "justification": priority_data.get('justification'),
            "timestamp": firestore.SERVER_TIMESTAMP,
            "reporter_id": user_id
        }
        
        try:
            doc_ref = self.db.collection(collection_path).add(new_report)
            return new_report
        except Exception as e:
            logger.error(f"Failed to add report: {e}")
            return None

    def get_dataframe(self):
        """Fetches all reports from Firestore and returns a DataFrame."""
        if not self.db:
            return pd.DataFrame() # Return empty if no DB

        app_id = st.session_state.get('app_id', 'default-app-id')
        collection_path = f"artifacts/{app_id}/public/data/{self.collection_name}"
        
        try:
            docs = self.db.collection(collection_path).stream()
            data = []
            for doc in docs:
                report = doc.to_dict()
                report['id'] = doc.id
                data.append(report)
            
            if not data:
                return pd.DataFrame()
                
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch reports: {e}")
            return pd.DataFrame()

    def get_stats(self):
        """Calculates live stats from the DataFrame."""
        df = self.get_dataframe()
        if df.empty:
            return {"total": 0, "critical": 0, "avg_severity": 0}
            
        return {
            "total": len(df),
            "critical": len(df[df['priority'] > 80]),
            "avg_severity": df['severity'].mean()
        }