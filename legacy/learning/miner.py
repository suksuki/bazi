import json

class DataMiner:
    """
    Simulates the pipeline: Web -> Text -> LLM -> JSON.
    In production, this would use BeautifulSoup + Ollama.
    """
    
    # Mock Database of "Ground Truth"
    MOCK_CASES = [
        {
            "id": "case_001_billionaire",
            "chart": { # Simulating 1977-05-08 Metal Bureau
                 "year": "丁巳", "month": "乙巳", "day": "癸丑", "hour": "辛酉"
            },
            "ground_truth": {
                "wealth_level": 95,  # Very Rich
                "dominant_element": "Jin", # Metal Bureau -> Should be Metal
                "desc": "Famous industrialist, made fortune in steel (Metal)."
            }
        },
        {
            "id": "case_002_scholar",
            "chart": { 
                 "year": "甲子", "month": "丙寅", "day": "乙卯", "hour": "壬午"
            },
            "ground_truth": {
                "wealth_level": 40, 
                "academic_level": 90, # High Academic
                "dominant_element": "Mu", # Wood
                "desc": "Renowned professor."
            }
        }
    ]

    def fetch_case(self, case_id=None):
        """
        Returns a case with 'Ground Truth' labels.
        """
        # In real world, logic to search web and parse
        return self.MOCK_CASES[0] if not case_id else next(c for c in self.MOCK_CASES if c['id'] == case_id)

    def verify_prediction(self, predicted_scores, ground_truth):
        """
        Compare Engine Output vs Truth.
        Simple logic: If Truth says 'Metal Dominant', is Metal score the highest?
        """
        target_elem = ground_truth['dominant_element']
        
        # Get element with max score from engine
        predicted_max = max(predicted_scores, key=predicted_scores.get)
        
        match = (predicted_max == target_elem)
        return {
            "match": match,
            "target": target_elem,
            "predicted": predicted_max,
            "scores": predicted_scores
        }
