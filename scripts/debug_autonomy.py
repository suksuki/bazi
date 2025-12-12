import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from service.web_hunter import WebHunter
from service.processor import ContentProcessor
from service.extractor import CaseExtractor
from service.auto_miner import AutoMiner

def diagnose():
    print("🕵️ Starting System Diagnostic...")
    
    # 1. Test Search Reachability
    print("\n[1] Testing Search Engine (DuckDuckGo)...")
    miner = AutoMiner()
    try:
        urls = miner._search_duckduckgo("Steve Jobs Astro Databank", limit=3)
        print(f"   -> Found {len(urls)} URLs.")
        if not urls:
            print("   ❌ Search failed. Check internet connection or DDG blocking.")
            return
        target_url = urls[0]
        print(f"   -> Target URL: {target_url}")
    except Exception as e:
        print(f"   ❌ Search crashed: {e}")
        return

    # 2. Test Fetching (WebHunter)
    print(f"\n[2] Testing WebHunter on {target_url}...")
    hunter = WebHunter()
    try:
        # Use generic hunt logic manually to inspect text
        import requests
        resp = requests.get(target_url, headers=hunter.headers, timeout=10)
        text = hunter._extract_visible_text(resp.text)
        print(f"   -> Fetched {len(text)} chars.")
        print(f"   -> Preview: {text[:100]}...")
    except Exception as e:
        print(f"   ❌ Fetch crashed: {e}")
        return

    # 3. Test Classification (Processor)
    print("\n[3] Testing Processor Classification...")
    processor = ContentProcessor()
    category = processor.classify_content(text)
    print(f"   -> Classified as: [{category}]")
    
    if category != "CASE":
        print("   ⚠️ WARNING: Content was NOT classified as a CASE.")
        print("   -> Reason: Missing keywords? (Need 'born', 'sheng', 'male/female' etc.)")
        
        # Test stricter logic explanation
        text_lower = text.lower()
        has_birth = any(k in text_lower for k in ["born", "birth", "出生", "生于"])
        has_subject = any(k in text_lower for k in ["male", "female", "man", "woman", "男命", "日主"])
        print(f"   -> Debug: has_birth={has_birth}, has_subject={has_subject}")
    
    # 4. Test Extraction (LLM)
    print("\n[4] Testing Extractor (LLM Connect)...")
    extractor = CaseExtractor()
    try:
        # We try a small chunk to save time
        # Do not pass model arg, let it load from ConfigManager
        result = extractor.extract(text[:2000])
        if result:
            print("   ✅ Extraction Successful!")
            print(f"   -> Result: {result}")
        else:
            print("   ❌ Extraction returned None (LLM failure or empty response).")
            # check ollama
            try:
                import ollama
                print("   -> Ollama library detected.")
            except:
                print("   -> Ollama library NOT installed.")
    except Exception as e:
        print(f"   ❌ Extraction crashed: {e}")

if __name__ == "__main__":
    diagnose()
