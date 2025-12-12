import json
import ollama
from learning.db import LearningDB
from learning.theory_miner import TheoryMiner
from core.config_manager import ConfigManager

class KnowledgeProcessor:
    """
    The 'Prefrontal Cortex' of the system.
    Responsible for:
    1. Classifying raw text input (Is it a Case? A Rule? Noise?)
    2. Routing to the appropriate extractor.
    3. Structuralizing the data into the Database.
    """
    def __init__(self, ollama_host=None):
        self.cm = ConfigManager()
        # Use config host if not provided
        config_host = self.cm.get('ollama_host', "http://localhost:11434")
        final_host = ollama_host if ollama_host else config_host
        
        self.client = ollama.Client(host=final_host)
        self.db = LearningDB()
        self.rule_miner = TheoryMiner(host=final_host)
        self.model = self.cm.get('selected_model_name', 'qwen2.5:3b')
        
    def process_content_chunk(self, text_chunk, source_meta=""):
        """
        Main entry point. Intelligent triage of text.
        """
        # 1. Classification
        ctype = self._classify_text(text_chunk)
        print(f"  [KnowledgeRouter] Identified Content Type: {ctype}")
        
        results = {"type": ctype, "extracted": []}

        # 2. Routing
        extracted_summary = []
        
        # Strategy: If Case or Mixed -> Try extract case
        if ctype in ["PROBABLY_CASE", "MIXED"]:
             print("  -> Attempting Case Extraction...")
             case_data = self._extract_case_data(text_chunk)
             if case_data:
                self.db.add_case(case_data, source=source_meta)
                extracted_summary.append(f"Case: {case_data.get('name', 'Unknown')}")
        
        # Strategy: If Theory or Mixed -> Try extract rules
        if ctype in ["PROBABLY_THEORY", "MIXED"]:
            print("  -> Attempting Rule Extraction...")
            # Delegate to existing Rule Miner
            rules = self.rule_miner.extract_rules(text_chunk)
            extracted_rules = []
            
            # Handle list/dict return types
            if isinstance(rules, list): extracted_rules = rules
            elif isinstance(rules, dict) and "rule_name" in rules: extracted_rules = [rules]
                
            for r in extracted_rules:
                # Save rule to DB directly
                self.db.add_rule(r, source_book=source_meta)
            
            if extracted_rules:
                extracted_summary.append(f"Rules: {len(extracted_rules)}")
                
        results["extracted"] = extracted_summary
        return results

    def _classify_text(self, text):
        """
        Ask LLM to classify the text segment.
        """
        prompt = f"""
        你是一个八字命理数据分拣员。请分析以下文本片段，判断其主要内容属于哪一类。
        
        【文本片段】:
        {text[:1000]}... (截取)

        【分类标准】:
        1. [THEORY]: 主要讲解理论、技法、口诀（如“甲木参天，脱胎要火”）。
        2. [CASE]: 主要讲述某个具体人的命运、八字排盘分析（如“某男，生于1990年...”）。
        3. [NOISE]: 广告、闲聊、无意义废话。
        4. [MIXED]: 既有案例又有理论，难以分割。

        请只返回分类代码（THEORY / CASE / NOISE / MIXED），不要其他废话。
        """
        try:
            print(f"  [Debug] Classifying text chunk ({len(text)} chars) with {self.model}...")
            res = self.client.generate(model=self.model, prompt=prompt, stream=False)
            tag = res['response'].strip().upper()
            if "THEORY" in tag: return "PROBABLY_THEORY"
            if "CASE" in tag: return "PROBABLY_CASE"
            if "MIXED" in tag: return "MIXED"
            return "NOISE"
        except:
            return "NOISE"

    def _extract_case_data(self, text):
        """
        Extract structured Bazi Case from text.
        Delegates to the unified CaseExtractor in service layer.
        """
        from service.extractor import CaseExtractor
        # Initialize extractor (will auto-load config)
        extractor = CaseExtractor(llm_client=self.client) # Pass client to reuse connection if possible
        # Actually CaseExtractor builds its own client from config usually, but we can trust it.
        # Or better yet, just instantiate it default.
        extractor = CaseExtractor() 
        
        return extractor.extract(text)
