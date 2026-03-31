import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import ollama
from core.config_manager import ConfigManager

class AutoCrawler:
    def __init__(self, host="http://localhost:11434"):
        self.cm = ConfigManager()
        if host == "http://localhost:11434":
            host = self.cm.get('ollama_host', host)
        self.host = host
        self.client = ollama.Client(host=host)
        self.default_model = self.cm.get('selected_model_name', 'qwen2.5:3b')

    def search_articles(self, keyword, max_results=3):
        """
        Uses DuckDuckGo to find relevant articles.
        """
        results = []
        try:
            with DDGS() as ddgs:
                # DDGS returns a generator
                for r in ddgs.text(keyword, max_results=max_results):
                    results.append(r)
        except Exception as e:
            print(f"Search failed: {e}")
        return results

    def fetch_content(self, url):
        """
        Fetches and cleans text from a URL.
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator='\n')
                # Clean whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                return clean_text
            else:
                return None
        except Exception as e:
            return None

    def assess_quality(self, title, text, model=None):
        """
        Asks LLM to judge if the content is high-quality Bazi theory.
        Returns: {score: int, reason: str}
        """
        model = model or self.default_model
        # Truncate text for judgment to save context window
        snippet = text[:2000]
        
        prompt = f"""
        你不仅是八字专家，还是一位严格的学术编辑。
        请评估以下文章是否包含**有价值的、具体的八字命理规则或理论**。
        
        【标题】: {title}
        【片段】:
        {snippet}
        
        【评分标准】:
        - 0-40分: 广告、算命软件推广、只有结果没有逻辑、纯迷信、无关内容。
        - 41-70分: 泛泛而谈的基础知识，缺乏深度。
        - 71-100分: 包含具体的断语、口诀、详细的格局分析、古籍引用与注解。干货满满。
        
        请仅以 JSON 格式返回:
        {{
            "score": <0-100>,
            "reason": "简短评价理由"
        }}
        """
        
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            import json
            return json.loads(response['message']['content'])
        except Exception as e:
            return {"score": 0, "reason": f"AI Error: {e}"}

# Mock testing
if __name__ == "__main__":
    crawler = AutoCrawler()
    # Mocking usage
    # print(crawler.search_articles("八字 调候"))
