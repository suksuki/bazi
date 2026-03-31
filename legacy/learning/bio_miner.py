
import json
import re
from datetime import datetime
from core.config_manager import ConfigManager

class BioMiner:
    """
    BioMiner: The "Biographer" Agent.
    Reads textual biographies and extracts structured "Ground Truth" data points 
    for Bazi validation.
    """
    
    def __init__(self, ollama_host=None):
        self.cm = ConfigManager()
        if not ollama_host or "115" in ollama_host:
             ollama_host = self.cm.get('ollama_host', "http://localhost:11434")
        self.host = ollama_host
        self.model = self.cm.get('selected_model_name', 'qwen2.5:3b')
        
    def set_config(self, host, model):
        self.host = host
        self.model = model

    def analyze_biography(self, bio_text, birth_year):
        """
        Uses LLM to extract year-by-year ratings from biography.
        Returns: List of dicts [{year, aspect, score, note}]
        """
        import ollama
        
        # Dynamic Config (Hot-Swap)
        current_host = self.cm.get('ollama_host', "http://localhost:11434")
        current_model = self.cm.get('selected_model_name', 'qwen2.5:3b')

        prompt = f"""
        You are a Biographer and Data Analyst.
        Read the following biography text. The subject was born in {birth_year}.
        
        Task: Identify key life events and rate their success in Bazi Aspects (0-100).
        Aspects: "Career", "Wealth", "Marriage" (Logic for Friendship/Love).
        
        Output Format: JSON Array ONLY. 
        Example: [{{ "year": 1990, "aspect": "Career", "score": 90, "note": "Founded Company" }}]
        
        Rules:
        1. Only include SIGNIFICANT events.
        2. Score key: 80+ (Great Success), 50 (Neutral), <40 (Failure/Trouble).
        3. Convert relative dates ("at age 20") to Years ({birth_year} + 20).
        
        Biography:
        {bio_text[:3000]} 
        """
        
        try:
            client = ollama.Client(host=current_host)
            response = client.generate(model=current_model, prompt=prompt, format='json', stream=False)
            content = response['response']
            
            # Parse JSON
            data = json.loads(content)
            
            # Validate output structure
            if isinstance(data, dict) and 'events' in data: data = data['events']
            if not isinstance(data, list): data = []
            
            return data
            
        except Exception as e:
            print(f"BioMiner Error: {e}")
            return []
