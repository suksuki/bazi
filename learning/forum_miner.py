
import os
import re
import json
import logging
from learning.theory_miner import TheoryMiner
from learning.db import LearningDB

class ForumMiner:
    """
    Pipeline A: The Forum Miner (Data Pipeline V6.0).
    Extracts structured Bazi cases and verified feedback from raw forum threads.
    Implements:
    1. Source Lock (High Signal only)
    2. Feedback Anchor (OP Replies only)
    3. PII Privacy Cleaning
    """
    
    def __init__(self):
        self.miner = TheoryMiner() # Re-use the LLM interface
        self.db = LearningDB()
        self.logger = logging.getLogger("ForumMiner")
        
        # PII Patterns
        self.pii_patterns = [
            (r"1[3-9]\d{9}", "[PHONE_REMOVED]"),
            (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL_REMOVED]"),
            (r"(QQ|qq|微信|vx|VX)\s*[:：]?\s*[0-9a-zA-Z]+", "[CONTACT_REMOVED]")
        ]

    def clean_pii(self, text):
        """
        Physical deletion of ID/Phone information.
        """
        cleaned = text
        for pattern, replacement in self.pii_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned

    def process_thread(self, thread_data, source_id="unknown"):
        """
        Main entry point for processing a forum thread structure.
        thread_data: {
            "title": str,
            "posts": [
                {"author_id": "LZ", "content": "...", "post_id": 1},
                {"author_id": "UserA", "content": "...", "post_id": 2},
                ...
            ]
        }
        """
        # 1. Identify OP (Lou Zhu)
        if not thread_data.get('posts'):
            return None
        
        op_post = thread_data['posts'][0]
        op_id = op_post['author_id']
        op_content = self.clean_pii(op_post['content'])
        
        # 2. Extract Feedback Anchor (The OP's replies)
        # We only care about OP's future posts that contain validation keywords
        feedback_candidates = []
        keywords = ["反馈", "准", "确实", "应期", "正如", "也没", "不对"]
        
        for post in thread_data['posts'][1:]:
            if post['author_id'] == op_id:
                # This is OP Speaking
                cleaned_content = self.clean_pii(post['content'])
                if any(k in cleaned_content for k in keywords):
                    feedback_candidates.append(cleaned_content)
        
        # If no feedback found, check if OP updated the main post or provided feedback inside
        if not feedback_candidates:
             # Heuristic: Check if OP content itself has "Feedback" section
             if "反馈" in op_content:
                 feedback_candidates.append(op_content)
        
        if not feedback_candidates:
            self.logger.info(f"Skipping {source_id}: No OP Feedback locked.")
            return None
            
        full_context = f"【Main Case】\n{op_content}\n\n【OP Feedback / Anchors】\n"
        for idx, fb in enumerate(feedback_candidates):
            full_context += f"--- Feedback {idx+1} ---\n{fb}\n"
            
        # 3. LLM Structured Extraction
        extracted_data = self._llm_extract_structure(full_context)
        
        # 4. Save
        if extracted_data:
             self._save_to_db(extracted_data, source_id, full_context)
             return extracted_data
        
        return None

    def _llm_extract_structure(self, text):
        """
        Uses LLM to parse Bazi and Feedback Events.
        """
        system_prompt = """
        You are a Physics Data Engineer for Bazi.
        Input: A Bazi case description and subsequent User Feedback.
        
        Task:
        1. Extract the Bazi Chart (Solar text or Pillars).
        2. Extract Verified Events (Ground Truth).
        
        Format (JSON Only):
        {
          "bazi_structure": {
             "year": {"stem": "X", "branch": "Y"},
             "month": {"stem": "X", "branch": "Y"},
             "day": {"stem": "X", "branch": "Y"},
             "hour": {"stem": "X", "branch": "Y"}
          },
          "ground_truth": [
             {
               "event_year": "e.g. 2022 / Ren Yin", 
               "type": "Wealth / Career / Marriage / Health",
               "description": "User feedback summary",
               "verification": "True/False/Mixed"
             }
          ]
        }
        
        If structure invalid or missing, return null.
        """
        
        import ollama
        try:
            # Using prompt piggyback or direct call
            # We truncate text to 2000 chars to be safe
            safe_text = text[:3000]
            
            response = ollama.chat(model='qwen2.5:3b', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': safe_text},
            ])
            content = response['message']['content']
            
            # Extract JSON
            match = re.search(r"```json(.*?)```", content, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = content
                
            return json.loads(json_str)
            
        except Exception as e:
            self.logger.error(f"Extraction Error: {e}")
            return None

    def _save_to_db(self, data, source_id, raw_text):
        chart = data.get('bazi_structure')
        truth = data.get('ground_truth', [])
        
        if not chart: return False
        
        # Determine "Truth Score" for DB compatibility
        # We calculate a simple "Wealth" / "Career" score based on event types?
        # Actually, LearningDB is simple. We allow 'truth' to be the full JSON list for now
        # But DB expects a dict of {category: score}
        
        # Heuristic Mapping
        mapped_truth = {}
        for ev in truth:
            etype = ev.get('type', 'General').lower()
            verify = ev.get('verification', 'True')
            
            val = 80 # Default 'Good'
            if "bad" in ev.get('description', '').lower() or "fail" in ev.get('description', '').lower():
                val = 20
            elif "lost" in ev.get('description', '').lower():
                val = 10
            elif "promotion" in ev.get('description', '').lower() or "win" in ev.get('description', '').lower():
                val = 90
            
            mapped_truth[etype] = val
            
        # Name: Anonymous_SourceID
        safe_name = f"Case_{source_id.replace(' ','_')}"
        
        self.db.add_case(safe_name, chart, mapped_truth, source=raw_text)
        return True
