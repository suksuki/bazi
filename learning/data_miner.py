import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import ollama
import json
import os
import re

class RealDataMiner:
    """
    Miners real-world data (celebrity biographies) to create a 'Ground Truth' dataset
    for validating Bazi theories.
    """
    def __init__(self, host="http://localhost:11434"):
        self.client = ollama.Client(host=host)
        # Ensure data directory exists
        self.data_dir = os.path.join(os.path.dirname(__file__), "../data/cases")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def search_person(self, name):
        """
        Search for a person's biography on DuckDuckGo.
        Returns the most relevant URL (preferring Wikipedia or Baidu Baike).
        """
        try:
            results = DDGS().text(f"{name} 个人经历 生平 Wiki", max_results=5)
            if not results:
                return None, "未找到相关结果"
            
            # Simple heuristic: take the first one, or prefer baidu/wiki if possible
            # For now, just return the first result's URL and Title
            top_result = results[0]
            return top_result['href'], f"Found: {top_result['title']}"
        except Exception as e:
            return None, f"Search Error: {e}"

    def get_bio_text(self, url):
        """
        Fetch and parse the text content from the URL.
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = resp.apparent_encoding # Handle charset
            
            if resp.status_code != 200:
                return None, f"HTTP Error: {resp.status_code}"
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Basic cleanup: remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text()
            
            # Normalize whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return clean_text, "Success"
        except Exception as e:
            return None, f"Fetch Error: {e}"

    def extract_profile(self, name, text, model="qwen2.5"):
        """
        Uses LLM to extract Birth Data and Major Life Events from biography text.
        """
        # Note: double braces {{ and }} are needed to escape literal braces in f-string
        prompt = f"""
        你是一个专业的数据分析师。请阅读关于【{name}】的传记文本，提取关键信息。
        
        【文本内容】:
        {text[:4000]} ... (content truncated)
        
        【提取目标】:
        1. 出生日期 (年, 月, 日, 时-如果提到的话)
        2. 重大人生事件 (尤其是发财、破产、升职、灾难等年份)
        
        请返回严格的 JSON 格式，不要包含任何 markdown 标记或解释文字。格式示例如下：
        {{
            "name": "{name}",
            "birth_info": {{
                "year": 1964,
                "month": 10,
                "day": 15,
                "hour": null 
            }},
            "events": [
                {{ "year": 1999, "description": "Founded Alibaba", "type": "GOOD" }},
                {{ "year": 2005, "description": "Partnership with Yahoo", "type": "NEUTRAL" }}
            ]
        }}
        
        注意：
        - 如果找不到具体的日或时，请填 null 或 "Unknown"。
        - 只提取确定的事实。
        - 必须是合法的 JSON。
        """
        
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            content = response['message']['content']
            
            # Robust Cleanup
            # 1. Remove Markdown code blocks
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            
            # 2. Extract JSON part if mixed with text
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            content = content.strip()
            
            data = json.loads(content)
            return data, "Success"
        except json.JSONDecodeError as e:
            return None, f"JSON Parsing Error: {e}\nRaw Content: {content[:100]}..."
        except Exception as e:
            return None, f"LLM Extraction Error: {e}"

    def save_case(self, data):
        """
        Save the extracted case to the SQLite Database.
        """
        try:
            from learning.db import LearningDB
            db = LearningDB()
            
            # Convert simple "events" to "ground_truth" dummy for now
            # In real app, we need logic to convert "Found Alibaba 1999" -> "Wealth Score 90" (via LLM)
            # For prototype, we just save the raw events as truth
            
            name = data.get('name', 'Unknown')
            chart_info = data.get('birth_info', {})
            ground_truth = {"raw_events": data.get('events', [])}
            source = "RealDataMiner (Web)"
            
            success = db.add_case(name, chart_info, ground_truth, source)
            
            if success:
                return f"Saved to DB: {name}"
            else:
                return f"Duplicate or Error saving {name}"
                
        except Exception as e:
            return f"Save Error: {e}"

if __name__ == "__main__":
    # Test
    miner = RealDataMiner()
    url, msg = miner.search_person("马云")
    print(f"URL: {url}, Msg: {msg}")
    if url:
        text, msg = miner.get_bio_text(url)
        print(f"Text len: {len(text)}")
        data, msg = miner.extract_profile("马云", text)
        print(data)
