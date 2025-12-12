import ollama
import json
from core.config_manager import ConfigManager

class TheoryMiner:
    """
    Uses LLM to digest Ancient Texts (theory) and extract algorithmic rules.
    """
    def __init__(self, host=None):
        self.cm = ConfigManager()
        
        # 1. Load Host from Config
        config_host = self.cm.get('ollama_host', "http://localhost:11434")
        
        # 2. Argument Override Logic:
        # If no host passed, or host is default localhost, use Config.
        # This prevents legacy hardcoded "localhost" calls from ignoring the config.
        if not host or host == "http://localhost:11434":
            self.host = config_host
        else:
            self.host = host # Explicit override
             
        self.client = ollama.Client(host=self.host)
        from learning.db import LearningDB
        self.db = LearningDB()
        self.default_model = self.cm.get('selected_model_name', 'qwen2.5:3b')

    def extract_rules(self, text_snippet, model=None, mode="rule_extraction"):
        """
        Feeds text to LLM.
        mode="rule_extraction": Extract atomic rules (JSON)
        mode="summary": Summarize key concepts (JSON)
        """
        model = model or self.default_model
        if mode == "summary":
            prompt = f"""
            你是一个精通八字命理的高级研究员。
            请分析以下视频/书籍片段，重点在于去粗取精。
            
            【处理要求】:
            1. 忽略口语废话（如“点赞关注”、“大家好”）。
            2. 识别其中的【特定技法】或【断语逻辑】。
            3. 如果没有干货，直接返回空 JSON。

            【内容片段】:
            {text_snippet[:8000]} 

            【输出格式】:
            请返回一个 JSON 对象：
            {{
                "title": "内容主题",
                "quality_score": 0-100 (知识密度评分),
                "summary": "200字以内的核心逻辑总结，去除废话",
                "key_concepts": ["术语1", "术语2"]
            }}
            """
        else:
            prompt_path = "learning/prompts/etl_prompt.md"
            import os
            
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    # Injects the snippet into the loaded prompt (assuming the prompt expects it at the end or we append it)
                    # The prompt file we saved uses "我将提供一段..." as intro. We just append the snippet.
                    prompt = f.read() + f"\n\n## 待处理原始文本：\n{text_snippet}"
            else:
                prompt = f"""
                你是一个精通Python和八字（Bazi）算法的数据挖掘工程师。
                你的任务是从杂乱的字幕文本中，提取出【结构化的命理规则】。
                ... (Fallback Logic) ...
                【输入文本】:
                {text_snippet}
                """
        
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            content = response['message']['content']
            
            # Robust cleaning
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Use json.loads to validate, if fail return raw text but structured as error
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                return {"raw_text_fallback": content, "error": "JSON Parse Error", "original_fragment": text_snippet[:50]}
                
        except Exception as e:
            return {"error": f"LLM Connection Error: {e}"}




    def save_rule(self, rule_data):
        """
        Saves a valid rule to the SQLite BrainDB.
        """
        if not rule_data or "error" in rule_data:
            return False
            
        self.db.add_rule(rule_data)
        return True

    def get_read_history(self):
        return self.db.get_read_history()

    def is_book_read(self, filename):
        return self.db.is_book_read(filename)

    def mark_book_as_read(self, filename):
        self.db.mark_book_read(filename)

    def get_knowledge_base(self):
        return self.db.get_all_rules()

    def process_book(self, long_text, model=None, chunk_size=1000):
        """
        Generator that yields rules from a long text (book) chunk by chunk.
        """
        model = model or self.default_model
        # Split text into chunks
        chunks = [long_text[i:i+chunk_size] for i in range(0, len(long_text), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            result = self.extract_rules(chunk, model=model)
            
            rules_found = []
            if isinstance(result, list):
                rules_found = result
            elif isinstance(result, dict) and "rule_name" in result:
                rules_found = [result]
            
            # Auto-save disabled to allow caller (scheduler) to add metadata
            # for r in rules_found:
            #      self.save_rule(r)
                
            yield {
                "chunk_index": i+1,
                "total_chunks": len(chunks),
                "rules": rules_found # Changed from 'rule' to 'rules'
            }

    def mine_cases_from_text(self, text, model=None):
        """
        Analyzes text to extract Structured Bazi Cases (Charts).
        Returns a list of dicts.
        """
        model = model or self.default_model
        prompt = f"""
        Analyze the following text from a Bazi study material.
        Extract ANY Bazi Cases (Charts) mentioned.
        
        Text content:
        {text[:15000]} ... (truncated)
        
        REQUIREMENTS:
        1. Identify Year/Month/Day/Hour pillars (GanZhi).
        2. Identify the Name (if hidden, invent a name like 'Case_001').
        3. Identify Gender (default to 'Male' if unknown).
        4. Identify Outcome/Result (Vreal Score 0-100 for Wealth/Career).
        
        Return a JSON list:
        [
            {{
            "name": "Zhang San",
            "gender": "Male",
            "chart": {{
                "year": {{"stem": "甲", "branch": "子"}},
                "month": {{"stem": "...", "branch": "..."}},
                "day": {{...}},
                "hour": {{...}}
            }},
            "truth": {{ "wealth": 80, "career": 60 }}
            }}
        ]
        If data is partial (e.g. missing Hour), leave it empty or guess based on context if confident.
        If NO cases found, return [].
        Only output valid JSON.
        """
        
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            out = response['message']['content']
            
            # Extract JSON from markdown code blocks if present
            cleaned_out = out.replace("```json", "").replace("```", "").strip()
            
            # If still has text, regex find the list
            if "[" in cleaned_out and "]" in cleaned_out:
                start = cleaned_out.find("[")
                end = cleaned_out.rfind("]") + 1
                cleaned_out = cleaned_out[start:end]
            
            cases_found = json.loads(cleaned_out)
            
            # Basic Validation
            valid_cases = []
            if isinstance(cases_found, list):
                for c in cases_found:
                    if isinstance(c, dict) and 'chart' in c and isinstance(c['chart'], dict):
                        valid_cases.append(c)
            return valid_cases
            
        except Exception as e:
            # print(f"Mining Error: {e}")
            return []

# Example Usage for Testing
if __name__ == "__main__":
    # Simulate a snippet found from web search
    snippet = "三命通会云：巳酉丑合金局，为金之正库，见者主文章冠世，武职威权..."
    miner = TheoryMiner(host="http://115.93.10.51:11434") # Use the user's remote host
    print(miner.extract_rules(snippet, model="qwen2.5:latest")) # Assumption on model name
