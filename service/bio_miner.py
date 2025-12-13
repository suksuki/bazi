import json
import re
import logging
import time
from typing import List, Dict, Optional

# Optional Import for Ollama
try:
    import ollama
except ImportError:
    ollama = None

BIO_MINER_SYSTEM_PROMPT = """
你是一个专业的人物传记分析师。你的任务是从文本中提取关键的人生大事，并判断其对命主是“吉”(positive) 还是“凶”(negative)。

### 输出格式要求 (Strict JSON)
必须直接输出合法的 JSON 列表，不要包含 Markdown 标记（如 ```json），不要包含任何解释性文字。
格式如下：
[
    {"year": 2014, "age": 50, "event": "阿里巴巴在纽交所上市", "type": "positive"},
    {"year": 2000, "age": 36, "event": "互联网泡沫破裂，公司差点倒闭", "type": "negative"}
]

### 极性判断标准
- positive: 升职、发财、上市、获奖、结婚、生子、掌权。
- negative: 破产、降职、入狱、离婚、生病、车祸、被裁员。

### 示例 (Few-Shot)
Input: "1999年，马云在杭州创办了阿里巴巴。但2001年遭遇了巨大的资金危机。"
Output:
[
    {"year": 1999, "event": "创办阿里巴巴", "type": "positive"},
    {"year": 2001, "event": "遭遇资金危机", "type": "negative"}
]
"""

class BioMiner:
    """
    BioMiner: Life Event Extraction Module (Powered by LLM).
    Focuses on mining structured life trajectory events (Year -> Event -> Polarity).
    """
    def __init__(self):
        self.logger = logging.getLogger("Antigravity.BioMiner")
        
        # Load Config
        try:
            from core.config_manager import ConfigManager
            self.config = ConfigManager()
        except ImportError:
            self.config = {} # Fallback if config manager missing

    def mine_events(self, text_input: str) -> List[Dict]:
        """
        Extract life events from text using LLM with specialized prompt.
        Returns list of dicts: {'year': int, 'type': 'positive'/'negative', 'description': '...'}
        """
        self.logger.info("BioMiner mining events with specialized prompt...")
        
        # 1. Config Loading
        current_host = self.config.get('ollama_host', 'http://localhost:11434') if hasattr(self.config, 'get') else 'http://localhost:11434'
        target_model = self.config.get('selected_model_name', 'qwen2.5:3b') if hasattr(self.config, 'get') else 'qwen2.5:3b'

        if not ollama:
            self.logger.error("Ollama library not installed.")
            return []

        try:
            client = ollama.Client(host=current_host, timeout=300)
            
            # 2. Call LLM
            self.logger.info(f"   ⏳ BioMiner: Sending text to {target_model}...")
            start_t = time.time()
            
            response = client.chat(model=target_model, messages=[
                {'role': 'system', 'content': BIO_MINER_SYSTEM_PROMPT},
                {'role': 'user', 'content': f"待处理文本：\n'''\n{text_input}\n'''"}
            ])
            
            duration = time.time() - start_t
            self.logger.info(f"   ⏱️ BioMiner: LLM responded in {duration:.1f}s.")
            
            content = response['message']['content']
            
            # 3. Sanitize and Parse
            raw_events = self._sanitize_and_parse_json(content)
            
            # 4. Standardize Output
            events_out = []
            for ev in raw_events:
                # Map prompt output keys to internal keys
                # Prompt: {"year": ..., "event": ..., "type": ...}
                # Internal: {'year': ..., 'description': ..., 'type': ...}
                
                year = ev.get('year')
                if not year: continue
                
                events_out.append({
                    'year': int(year),
                    'type': ev.get('type', 'neutral'),
                    'description': ev.get('event', '') # Prompt uses "event" key
                })
                
            return events_out
            
        except Exception as e:
            self.logger.error(f"BioMiner Inference Failed: {e}")
            return []

    def _sanitize_and_parse_json(self, llm_output: str) -> List[Dict]:
        """
        清洗 LLM 输出的脏数据，尝试提取有效 JSON
        """
        # 1. 尝试直接解析
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            pass

        # 候选字符串列表
        candidates = []
        
        # 2. 尝试提取完整闭合的 JSON 列表 [ ... ]
        match_closed = re.search(r'\[.*\]', llm_output, re.DOTALL)
        if match_closed:
            candidates.append(match_closed.group(0))
            
        # 3. 尝试提取从第一个 [ 开始到结尾的内容 (处理截断情况)
        match_open = re.search(r'\[.*', llm_output, re.DOTALL)
        if match_open:
             # 如果完全闭合的没找到，或者找到的这个比完全闭合的长(说明有额外内容?)，或者就是同一个
             # 简单起见，只要找到了就加进去，尝试修复
             candidates.append(match_open.group(0))

        # 4. 遍历候选并尝试修复
        for json_str in candidates:
            # 4a. 直接解析候选
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # 4b. 尝试修复（去除尾部逗号，补全 ]）
            try:
                s = json_str.strip()
                # 常见错误：结尾是 "}," 
                if s.endswith(','):
                    s = s[:-1]
                # 常见错误：结尾没有 "]"
                if not s.endswith(']'):
                    s += ']'
                return json.loads(s)
            except json.JSONDecodeError:
                pass
        
        self.logger.error(f"JSON 解析彻底失败. Raw output snippet: {llm_output[:100]}...")
        return []

if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.INFO)
    miner = BioMiner()
    test_text = "1999年，马云在杭州创办了阿里巴巴。但2001年遭遇了巨大的资金危机。"
    res = miner.mine_events(test_text)
    print("Test Result:", json.dumps(res, ensure_ascii=False, indent=2))
