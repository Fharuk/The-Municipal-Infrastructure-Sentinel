# The-Municipal-Infrastructure-Sentinel

Municipal Infrastructure Sentinel (Capstone Project)

Project Summary

The Municipal Infrastructure Sentinel is a multi-agent AI system designed to modernize civic infrastructure management. Unlike traditional reporting apps that simply collect data, this system acts as an intelligent triage layer. It uses Multimodal AI (Computer Vision) to verify reports and Strategic Planning AI to prioritize them based on severity and context.

This project demonstrates expertise in:

Multimodal AI Integration: Using Gemini 2.5 Flash for image analysis and reasoning.

Geospatial Visualization: Integrating OpenStreetMap (via Folium) for operational heatmaps.

Dual-User UX: Designing distinct workflows for Citizens (Reporting/Gamification) and Government (Command/Dispatch).

Secure Architecture: Implementing robust secret management to protect API keys in public demos.

Core Architectural Features

1. The "Vision Agent" (The Eye)

Function: Analyzes user-uploaded images to detect infrastructure defects (potholes, flooding, trash).

Intelligence: Includes a Relevance Filter. If a user uploads a non-infrastructure image (e.g., a selfie), the agent rejects it before processing, saving compute costs and maintaining database integrity.

Output: Extracts structured JSON data including defect_type, severity_score (1-10), and estimated_material_needed.

2. The "Strategist Agent" (The Brain)

Function: Contextualizes the defect based on location.

Logic: A severity 8 pothole on a highway (high speed, high risk) is prioritized differently than a severity 8 pothole on a quiet cul-de-sac. The agent outputs a priority_index (0-100).

3. Gamification & Operations (The Experience)

Citizen Path (Path A): Users receive immediate feedback on their report's impact. The system tracks "Top Reporters" to encourage civic engagement.

Government Path (Path B): A command dashboard allows officials to filter reports by status/type and "Dispatch" teams, changing the state of a report from "New" to "In Progress."

Technical Stack

Frontend: Streamlit (Python)

AI Core: Google Gemini 2.5 Flash (via google-generativeai SDK)

Mapping: Folium (OpenStreetMap provider)

State Management: In-Memory Session State (optimized for secure, stateless demos)

Setup and Installation

Prerequisites

Python 3.10+

A Google Gemini API Key

Step 1: Clone and Install

git clone [https://github.com/Fharuk/The-Municipal-Infrastructure-Sentinel.git](https://github.com/Fharuk/The-Municipal-Infrastructure-Sentinel.git)
cd The-Municipal-Infrastructure-Sentinel

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (Linux/Codespaces only)
sudo apt-get update && sudo apt-get install -y graphviz


Step 2: Configure Secrets (Crucial)

This project uses secure secret management to prevent API key leakage. You cannot run it by simply pasting your key into the code.

For Local/Codespaces:
Export your key as an environment variable:

export GEMINI_API_KEY="your_actual_api_key_here"


For Streamlit Cloud:
Add your key to the App Secrets in the dashboard:

GEMINI_API_KEY = "your_actual_api_key_here"


Step 3: Run the Application

streamlit run app.py


Usage Guide

Citizen Reporter Tab:

Enter your name (optional, for the leaderboard).

Upload a photo of infrastructure (e.g., a pothole).

Provide a location name and brief description.

Click "Analyze & Submit."

Note: The AI will reject images that do not contain valid infrastructure defects.

Government Dashboard Tab:

View the Operational Heatmap to see clusters of high-priority issues (Red markers).

Use the sidebar filters to drill down by defect type (e.g., "Show only Flooding").

Use the Dispatch Command Center table to select a report and update its status to "In Progress" or "Resolved."

Strategic Decisions & Trade-offs

Persistence: The current version uses In-Memory Persistence (st.session_state). This was chosen to allow for a friction-free, no-login public demo. Data resets when the app creates a new session.

Map Provider: OpenStreetMap was selected over Google Maps to ensure the project remains 100% open-source and free to deploy without billing constraints.

Security: The application removes all manual API key input fields from the UI, relying entirely on server-side secrets to prevent user error or credential theft during public demonstrations.