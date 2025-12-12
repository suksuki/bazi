
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from learning.forum_miner import ForumMiner

def test_pipeline_v6():
    print("Testing Data Pipeline V6.0...")
    miner = ForumMiner()
    
    # 1. Mock Thread Data (With PII and Feedback)
    mock_thread = {
        "title": "Please help check career",
        "posts": [
            {
                "author_id": "LZ_001",
                "content": "My Bazi: Jia Zi, Bing Yin, Wu Wu, Geng Shen. Contact me at 13800138000. test@example.com",
                "post_id": 1
            },
            {
                "author_id": "Master_A",
                "content": "You will be rich in 2022.",
                "post_id": 2
            },
            {
                "author_id": "LZ_001", 
                "content": "Feedback: Indeed (确实), in 2022 I got a promotion!",
                "post_id": 3
            }
        ]
    }
    
    # Check PII Cleaning
    op_content = mock_thread['posts'][0]['content']
    cleaned = miner.clean_pii(op_content)
    print(f"Original: {op_content}")
    print(f"Cleaned:  {cleaned}")
    
    if "138" in cleaned or "@" in cleaned:
        print("❌ PII Leak Detected")
    else:
        print("✅ PII Cleaned")
        
    # Check Anchor Logic (Manual check of process logic)
    # We can't easily mock the LLM part without mocking 'ollama' module.
    # But we can check if it parses the thread structure correctly.
    
    # Let's mock _llm_extract_structure to avoid actual API call failure
    miner._llm_extract_structure = lambda text: {
        "bazi_structure": {"year": {"stem": "Jia", "branch": "Zi"}},
        "ground_truth": [{"event_year": "2022", "type": "Career", "description": "Promotion", "verification": "True"}]
    }
    
    result = miner.process_thread(mock_thread, source_id="Test_Thread_1")
    
    if result:
        print("✅ Pipeline Processed Thread Successfully")
        print(f"Result: {result}")
    else:
        print("❌ Pipeline Failed")

if __name__ == "__main__":
    test_pipeline_v6()
