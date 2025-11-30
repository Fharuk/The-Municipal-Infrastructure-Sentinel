import json
import logging
import os
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
        """Helper to handle text-only or multimodal requests."""
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

    def vision_agent(self, image: Image) -> dict:
        """
        Analyzes an image to detect infrastructure failures.
        """
        prompt = """
        You are a Civil Engineer Inspector. Analyze this image for municipal infrastructure issues.
        
        First, determine RELEVANCE. Is this image related to roads, drainage, waste, utilities, or public infrastructure?
        If NO (e.g., a selfie, a cat, food, indoor furniture), set "is_relevant": false.
        
        If YES:
        1. Identify the primary defect.
        2. Estimate Severity (1-10).
        3. Describe technical details.
        
        Output JSON:
        {
            "is_relevant": boolean,
            "defect_type": "string",
            "severity_score": int,
            "description": "string",
            "estimated_material_needed": "string"
        }
        """
        return self._generate_json(prompt, image)

    def prioritization_agent(self, defect_data: dict, location_context: str) -> dict:
        """
        Calculates a priority score based on defect severity and location context.
        """
        prompt = f"""
        You are a City Planner. Prioritize this repair request.
        
        Defect: {defect_data.get('defect_type')} (Severity: {defect_data.get('severity_score')})
        Location Context: {location_context}
        
        Task: Calculate 'priority_index' (0-100).
        - Severity * Context Multiplier = Priority.
        - Highway/School Zone = High Multiplier.
        
        Output JSON:
        {{
            "priority_index": float,
            "justification": "Short reason for priority level.",
            "assigned_department": "Works / Sanitation / Power"
        }}
        """
        return self._generate_json(prompt)