# service/extractor.py
"""
Case Extraction Module
Project Crimson Vein - Information Extraction Layer

This module defines the LLM prompt and interface for extracting structured 
Bazi cases from raw unstructured text.
"""

import json
import re
import time
from typing import Dict, Optional, Any

# Optional Import for Ollama
try:
    import ollama
except ImportError:
    ollama = None

# The core system prompt defined by the user
SYSTEM_PROMPT_TEMPLATE = """
你是一个“八字案例信息抽取 agent”。
你的目标是：自动收集“真实八字案例”，用于学术研究中的算法验证。

约束条件：
- 不使用 ModelScope 或任何合成命理数据
- 不依赖用户注册或人工提交
- 不使用短视频平台作为主要数据源
- 数据必须来自公开网页
- 案例必须包含：出生信息 + 已发生的人生事件

任务：
- 从文本中抽取出生信息（年/月/日/时/出生地）
- 抽取所有已经发生的人生事件（年份/年龄/事件类型/描述）
- 评估案例质量（Quality Score）
- 判断是否可用于算法验证（必须有完整的生时和至少1个验证事件）

输出目标：严格按以下 JSON Schema 输出，不包含任何解释性文字。

```json
{
  "profile": {
    "name": "姓名或匿名",
    "gender": "M (男) 或 F (女)",
    "birth_year": 1990,
    "birth_month": 1,
    "birth_day": 1,
    "birth_hour": 12,  // 24小时制，必须尽量精确
    "birth_minute": 0, // 如果有
    "birth_city": "城市名"
  },
  "life_events": [
    {
      "year": 2015,
      "age": 25,
      "event_type": "Marriage", // 类别: Marriage, Career, Health, Wealth, Study, Crisis, Other
      "description": "事件描述",
      "verified": true
    }
  ],
  "tags": ["标签1", "标签2"],
  "quality_score": 85, // 0-100, 基于信息完整度和可信度
  "valid_for_validation": true // true if birth_hour is present AND events > 0
}
```
"""

def construct_prompt(raw_text: str) -> str:
    """
    Constructs the final prompt to be sent to the LLM.
    """
    return f"{SYSTEM_PROMPT_TEMPLATE}\n\n待处理文本：\n'''\n{raw_text}\n'''"

class CaseExtractor:
    def __init__(self, llm_client=None):
        """
        Initialize the Extractor.
        :param llm_client: Optional LLM client wrapper (if not using direct Ollama)
        """
        self.llm_client = llm_client
        
        # Load Config
        try:
            from core.config_manager import ConfigManager
            self.config = ConfigManager()
            # Default to qwen2.5 if not set, user can override to 'qwen2:7b' etc.
            # Align with UI key: 'selected_model_name'
            pass
        except ImportError:
            pass

    def _smart_compress(self, text: str) -> str:
        """
        Heuristic algorithm to keep only relevant lines for Bazi extraction.
        Reduces token usage and noise.
        """
        lines = text.splitlines()
        if len(lines) < 20: 
            return text # Too short, just keep it all
            
        kept_indices = set()
        
        # High-Value Keywords for Bazi
        keywords_high = ["生于", "出生", "乾造", "坤造", "男命", "女命", "八字", "年", "月", "日", "时", "大运", "流年", "岁运", "排盘"]
        stems_branches = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥"
        
        for i, line in enumerate(lines):
            score = 0
            line_str = line.strip()
            if not line_str: continue
            
            # Check Keywords
            for kw in keywords_high:
                if kw in line_str: score += 5
                
            # Check Stems/Branches
            count_sb = sum(1 for char in line_str if char in stems_branches)
            if count_sb > 0: score += (count_sb * 2)
            
            # Check Digits (Birth years, dates)
            count_digit = sum(1 for char in line_str if char.isdigit())
            if count_digit >= 4: score += 2
            
            # Keep line if relevant
            if score >= 5: # Threshold
                kept_indices.add(i)
                # Add context (previous and next line)
                if i > 0: kept_indices.add(i-1)
                if i < len(lines) - 1: kept_indices.add(i+1)
        
        # Always keep first 5 lines (often contain Title/Name)
        for i in range(min(5, len(lines))):
            kept_indices.add(i)
            
        # Reconstruct text
        sorted_indices = sorted(list(kept_indices))
        compressed_lines = [lines[i] for i in sorted_indices]
        
        result = "\n".join(compressed_lines)
        return result

    def extract(self, raw_text: str, model: Optional[str] = None) -> Optional[Dict]:
        """
        Main extraction method.
        Connects to Local LLM (Ollama) to perform structural extraction.
        """
        # 1. Runtime Config Loading (Hot-Swapping Support)
        current_host = self.config.get('ollama_host', 'http://localhost:11434')
        # Priority: Method Argument > Config > Default
        target_model = model or self.config.get('selected_model_name', 'qwen2.5')
        
        # Fast Path: Local Regex Mode
        if target_model == 'regex':
            print("   ⏩ [Extractor] Using Local Regex Mode (Configured)")
            return self._extract_with_regex(raw_text)
        
        # 1. Compress Text (Remove Noise)
        compressed_text = self._smart_compress(raw_text)
        print(f"   📉 [Extractor] Compressed {len(raw_text)} -> {len(compressed_text)} chars.")
        
        # 2. Final Truncation (Safety Net)
        final_text = compressed_text[:12000]
        if len(compressed_text) > 12000:
             print(f"   ✂️ [Extractor] Text truncated {len(compressed_text)} -> 12000 chars.")

        prompt = construct_prompt(final_text)
        
        try:
            if not ollama:
                raise ImportError("Ollama library not loaded")
            
            # Use custom host if configured
            client = ollama.Client(host=current_host, timeout=300)
            
            print(f"   ⏳ [Extractor] Sending {len(final_text)} chars to {target_model}... (Host: {current_host})")
            import time
            start_t = time.time()
            
            # Call Ollama
            # We use generation instead of chat for stricter control, or chat with system prompt
            response = client.chat(model=target_model, messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT_TEMPLATE},
                {'role': 'user', 'content': f"待处理文本：\n'''\n{final_text}\n'''"}
            ])
            
            duration = time.time() - start_t
            print(f"   ⏱️ [Extractor] LLM responded in {duration:.1f}s.")
            
            content = response['message']['content']
            
            # Clean Markdown Code Blocks  (```json ... ```)
            if "```" in content:
                import re
                # Extract content between first ```json and ``` or just ``` and ```
                match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
                if match:
                    content = match.group(1)
            
            # Parse JSON
            data = json.loads(content.strip())
            return data
            
        except ImportError:
            print("❌ [Extractor] 'ollama' library not installed. Please pip install ollama.")
            return self._extract_with_regex(raw_text)
        except json.JSONDecodeError as e:
            content_preview = content[:50] if 'content' in locals() else "Unknown"
            print(f"❌ [Extractor] LLM Output not valid JSON: {content_preview}...")
            return self._extract_with_regex(raw_text)
        except Exception as e:
            print(f"❌ [Extractor] LLM Inference Failed: {e}")
            return self._extract_with_regex(raw_text)

    def _extract_with_regex(self, text: str) -> Optional[Dict]:
        """
        Emergency Fallback: Rules-based extraction for common formats.
        """
        print("   ⚠️ Engaging Regex Fallback extraction...")
        
        # 0. Initialize Defaults
        profile = {
            "name": "Unknown_Regex",
            "gender": "Unknown",
            "birth_year": 1990,
            "birth_month": 1,
            "birth_day": 1,
            "birth_hour": 12,
            "birth_minute": 0,
            "birth_city": "Unknown"
        }
        
        # 1. Gender Detection
        if re.search(r'(乾造|男命|乾)', text):
            profile['gender'] = 'M'
        elif re.search(r'(坤造|女命|坤)', text):
            profile['gender'] = 'F'
            
        # 2. Date Extraction
        # Priority A: "1988年8月8日"
        date_cn = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if date_cn:
            profile['birth_year'] = int(date_cn.group(1))
            profile['birth_month'] = int(date_cn.group(2))
            profile['birth_day'] = int(date_cn.group(3))
        else:
            # Priority B: ADB style "24 February 1955" or simple year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
            if not year_match:
                return None # No date, no case.
            profile['birth_year'] = int(year_match.group(1))

        # 3. Hour Extraction (Simple)
        hour_match = re.search(r'(\d{1,2})点|(\d{1,2}):\d{2}', text)
        if hour_match:
            h = hour_match.group(1) or hour_match.group(2)
            profile['birth_hour'] = int(h)

        # 4. Name Heuristic
        # Look for "【姓名】XXX" or first line
        lines = text.splitlines()
        clean_lines = [l.strip() for l in lines if l.strip()]
        if clean_lines:
            potential_name = clean_lines[0]
            if len(potential_name) < 20: 
                profile['name'] = potential_name
        
        # Construct Result
        import hashlib
        id_str = f"{profile['name']}_{profile['birth_year']}_{profile['gender']}"
        case_id = hashlib.md5(id_str.encode()).hexdigest()
        
        return {
            "id": case_id,
            "profile": profile,
            "life_events": [], # Regex usually can't reliably extract events
            "quality_score": 60,
            "valid_for_validation": False,
            "source": "regex_fallback"
        }

    def mock_extract(self, raw_text: str) -> Dict:
        """
        Simulate extraction for testing logic flow without API cost.
        """
        # Minimal parser for specific mock patterns (just for demo)
        # in reality, this is where the LLM magic happens.
        return {
            "profile": {
                "name": "Mock User",
                "gender": "M",
                "birth_year": 1988,
                "birth_month": 8,
                "birth_day": 8,
                "birth_hour": 8,
                "birth_city": "Beijing"
            },
            "life_events": [
                {"year": 2018, "age": 30, "event_type": "Career", "description": "Founded verification engine", "verified": True}
            ],
            "tags": ["Mock", "Test"]
        }

if __name__ == "__main__":
    # Test the prompt construction
    sample_text = """
    【反馈】男命，1985年10月5日早上6点生于上海。
    大家都说我婚姻不顺，确实如此。2012年结婚，2015年因为性格不合离婚了。
    不过财运还行，2018年自己出来单干，赚了第一桶金。
    """
    
    extractor = CaseExtractor()
    print("Testing Smart Extraction...")
    extractor.extract(sample_text)
