
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json
import re
from core.config_manager import ConfigManager

class WebHunter:
    """
    The Autonomous Data Hunter.
    Searches the open web for Bazi case studies and extracts chart data + life events.
    """
    
    def __init__(self, ollama_host=None):
        self.cm = ConfigManager()
        if not ollama_host or "115" in ollama_host:
             ollama_host = self.cm.get('ollama_host', "http://localhost:11434")
        self.host = ollama_host
        self.model = self.cm.get('selected_model_name', 'qwen2.5:3b')
        
    def hunt(self, target_name):
        """
        1. Search
        2. Scrape
        3. Extract
        Returns: { 'chart': {...}, 'events': [...] }
        """
        results = self._search(target_name)
        if not results: return None
        
        # Analyze top 2 results to find data
        for r in results[:2]:
            url = r.get('href')
            print(f"Hunting in: {url}")
            content = self._scrape(url)
            
            if len(content) < 200: continue
            
            data = self._ai_extract(content)
            if data and (data.get('birth_year') or data.get('events')):
                data['source_url'] = url
                return data
                
        return None

    def _search(self, name):
        try:
            with DDGS() as ddgs:
                # Query: Name + Bazi Analysis
                query = f"{name} 八字命理分析 案例"
                results = list(ddgs.text(query, max_results=3))
                return results
        except Exception as e:
            print(f"Search Error: {e}")
            return []

    def _scrape(self, url):
        try:
            # Simple User-Agent to avoid immediate block
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                # Extract text
                soup = BeautifulSoup(resp.content, 'html.parser')
                # Remove scripts and styles
                for s in soup(["script", "style"]): s.extract()
                return soup.get_text()[:6000] # Limit size for LLM
        except Exception as e:
            print(f"Scrape Error: {e}")
            return ""
        return ""

    def _ai_extract(self, text):
        import ollama
        prompt = """
        You are a Bazi Data Extraction Agent.
        Analyze the text provided. It is a Bazi analysis article.
        
        Task: Extract the Birth Info and Life Events.
        
        Output JSON Schema:
        {
            "name": "Subject Name",
            "birth_year": 1980,
            "birth_month": 5,
            "birth_day": 20,
            "birth_hour": 14 (0-23, or null if unknown),
            "gender": "男" or "女",
            "events": [
                { "year": 1998, "aspect": "Career/Wealth/Marriage/Total", "score": 80, "note": "Accepted to uni" }
            ]
        }
        
        If data is missing, use null.
        
        Text:
        """ + text
        
        try:
            client = ollama.Client(host=self.host)
            response = client.generate(model=self.model, prompt=prompt, format='json', stream=False)
            data = json.loads(response['response'])
            return data
        except Exception as e:
            print(f"AI Extract Error: {e}")
            return None
