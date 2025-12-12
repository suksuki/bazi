# service/processor.py
"""
Content Processing Pipeline
Project Crimson Vein - Logic Layer

Routes raw text to appropriate extractors (Case vs Rule) based on semantic content.
"""

from typing import Dict, Literal
from service.extractor import CaseExtractor, construct_prompt as construct_case_prompt
from service.case_db import CaseDatabase

# Enum for content types
ContentCategory = Literal["CASE", "RULE", "MIXED", "NOISE"]

CLASSIFIER_PROMPT = """
你是一个“八字内容分类员”。
输入一段文本，请判断其主要内容属于以下哪一类：
1. CASE: 包含具体某人的八字排盘分析、生平事件反馈。
2. RULE: 讲解八字理论、口诀、断语（如“伤官见官，为祸百端”）。
3. MIXED: 既有理论又有案例。
4. NOISE: 广告、闲聊、无关内容。

只输出类别单词，不要其他内容。
"""

class ContentProcessor:
    def __init__(self, db_path="data/cases.db"):
        self.case_db = CaseDatabase(db_path)
        self.case_extractor = CaseExtractor()
        # self.rule_extractor = RuleExtractor() # Future work

    def classify_content(self, text: str) -> ContentCategory:
        """
        [MOCK] Uses heuristic rules to determine content type.
        Designed to strictly separate Logic (RULE) from Facts (CASE).
        """
        # TODO: Upgrade to LLM-based classification for higher accuracy
        
        text_lower = text.lower()
        
        # 1. Strong Case Indicators (Birth Info is mandatory)
        has_birth_info = any(k in text_lower for k in ["born", "birth", "出生", "生于", "乾造", "坤造", "年", "nativ"])
        has_subject = any(k in text_lower for k in ["male", "female", "man", "woman", "男命", "女命", "日主", "命主", "day master"])
        
        # 2. Strong Theory Indicators
        has_theory_keywords = any(k in text_lower for k in ["口诀", "断语", "凡是", "theory", "principle", "classic"])
        
        # 3. Decision Logic
        if has_birth_info and has_subject:
            # If it has birth data and a subject, it's likely a case, 
            # even if it mentions theory (Mixed). We prioritize extracting the Case.
            return "CASE"
            
        if has_theory_keywords:
            return "RULE"
        
        # Fallback
        if len(text) > 200:
            # Long text without clear indicators? maybe noise or subtle case
            return "NOISE"
            
        return "NOISE"

    def process_text(self, text: str, source_url: str = ""):
        """
        Main entry point for processing mined text.
        """
        category = self.classify_content(text)
        print(f"🔍 Content classified as: {category}")
        
        if category == "CASE" or category == "MIXED":
            self._handle_case(text, source_url)
        
        if category == "RULE" or category == "MIXED":
            self._handle_rule(text, source_url)

    def _handle_case(self, text: str, source_url: str):
        """Extract and save case data"""
        print("⚡ Extracting Case data...")
        
        # Check Configuration for extraction mode
        # Added per user request to toggle between LLM and Local Regex
        try:
            from core.config_manager import ConfigManager
            cm = ConfigManager()
            force_local = cm.get("auto_miner_force_local", False)
        except ImportError:
            force_local = True # Fallback if config fails
            
        extraction_model = "regex" if force_local else None
        if force_local:
             print("   ⏩ [Processor] Using Local Regex Mode (Configured)")

        # Step 1: Extraction
        case_data = self.case_extractor.extract(text, model=extraction_model)
        
        if not case_data:
            # For demo, use mock data if LLM is not connected
            # In production, this should log an error/warning
            print("⚠️ Extraction failed (No LLM). Skipping save.")
            return

        # Step 2: Enrich metadata
        case_data['source_url'] = source_url
        
        # Generate Deterministic ID (to avoid duplicates)
        # ID = MD5(Name + Gender + BirthYear + BirthMonth + BirthDay)
        import hashlib
        p = case_data.get('profile', {})
        raw_id_str = f"{p.get('name')}{p.get('gender')}{p.get('birth_year')}{p.get('birth_month')}{p.get('birth_day')}"
        case_id = hashlib.md5(raw_id_str.encode('utf-8')).hexdigest()
        case_data['id'] = case_id
        
        # Step 3: Persistence
        self.case_db.insert_case(case_data)

    def _handle_rule(self, text: str, source_url: str):
        """Extract and save rule data"""
        print("📚 Rule extraction not implemented yet.")
        # TODO: Implement RuleExtractor and RuleDB

if __name__ == "__main__":
    # Test Run
    processor = ContentProcessor()
    
    sample_text = """
    这是一个典型的伤官配印案例。男命，甲子年丙寅月丁卯日出生。
    2018年考上公务员，就是因为印星发力。
    """
    
    print(f"Processing text: {sample_text.strip()}")
    # output will be mocked since extract() returns None without LLM
    processor.process_text(sample_text, source_url="http://test.com")
