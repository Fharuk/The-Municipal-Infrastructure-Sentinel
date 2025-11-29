import json
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

logger = logging.getLogger(__name__)

class CivicAgentCore:
    """
    Orchestrates Multimodal Agents for Infrastructure Analysis.
    """
    def __init__(self, api_key: str, model_name: str = 'gemini-2.5-flash-preview-09-2025'):
        if not api_key:
            raise ValueError("API Key is required.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def _generate_json(self, prompt: str, image: Image = None) -> dict:
        """Helper to handle text-only or multimodal (image+text) requests."""
        config = genai.GenerationConfig(response_mime_type="application/json")
        try:
            inputs = [prompt, image] if image else [prompt]
            response = self.model.generate_content(
                inputs,
                generation_config=config,
                safety_settings=self.safety
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Agent Generation Failed: {e}")
            return {"error": str(e)}

    # --- AGENT 1: THE INSPECTOR (Computer Vision) ---
    def vision_agent(self, image: Image) -> dict:
        """
        Analyzes an image to detect infrastructure failures.
        """
        prompt = """
        You are a Civil Engineer Inspector. Analyze this image for municipal infrastructure issues.
        
        Tasks:
        1. Identify the primary defect (Pothole, Blocked Drainage, Heap of Trash, Fallen Pole, or 'None').
        2. Estimate Severity (1-10) based on size and obstruction.
        3. Estimate Repair Complexity (Low, Medium, High).
        
        Output JSON:
        {
            "defect_type": "string",
            "severity_score": int,
            "description": "short technical description",
            "estimated_material_needed": "string (e.g., 'Asphalt', 'Excavator')"
        }
        """
        return self._generate_json(prompt, image)

    # --- AGENT 2: THE STRATEGIST (Prioritization) ---
    def prioritization_agent(self, defect_data: dict, location_context: str) -> dict:
        """
        Calculates a priority score based on defect severity and location context.
        """
        prompt = f"""
        You are a City Planner. Prioritize this repair request.
        
        Defect: {defect_data.get('defect_type')} (Severity: {defect_data.get('severity_score')})
        Location Context: {location_context} (e.g., 'Main Highway', 'School Zone', 'Back Alley')
        
        Rules:
        - High traffic areas (Highways) multiply urgency.
        - Safety risks (School zones) multiply urgency.
        
        Output JSON:
        {{
            "priority_index": float (0.0 to 100.0),
            "justification": "Why this priority level?",
            "assigned_department": "Works / Sanitation / Power"
        }}
        """
        return self._generate_json(prompt)