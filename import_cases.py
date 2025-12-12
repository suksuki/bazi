
import sys
import os
import json
import argparse
from learning.theory_miner import TheoryMiner
from learning.db import LearningDB

def import_text_cases(text_content, source_name="User Input", auto_train=False):
    """
    Imports raw text cases, processes them via LLM ETL, and saves to DB.
    """
    print(f"--- 🚀 Starting Batch Case Import ---")
    print(f"Source: {source_name}")
    print(f"Input Length: {len(text_content)} chars")

    # 1. Initialize Components
    miner = TheoryMiner() # Will pick up config host
    db = LearningDB()

    # 2. Run ETL Process (Text -> JSON)
    print("Step 1: Mining cases from text (LLM)...")
    cases_raw = miner.mine_cases_from_text(text_content)
    
    cases = []
    if isinstance(cases_raw, list):
        cases = cases_raw
    elif isinstance(cases_raw, dict):
        # Handle wrapped responses like {"cases": [...]}
        for k, v in cases_raw.items():
            if isinstance(v, list):
                cases.extend(v)
                
    if not cases:
        print(f"⚠️ No valid cases found. Raw output type: {type(cases_raw)}")
        return 0

    print(f"Step 2: Validation. Found {len(cases)} potential cases.")
    
    valid_count = 0
    for c in cases:
        # Validate Structure
        if 'chart' not in c or 'truth' not in c:
            print(f"  ❌ Skipping invalid case: {c.get('name', 'Unknown')}")
            continue
            
        chart = c['chart']
        truth = c['truth']
        name = c.get('name', 'Case')
        
        # Save to DB
        try:
            # Check dupes? DB handles it via ID? We rely on DB add_case.
            # Convert dicts to JSON strings as DB expects -> NO, DB expects Dict and dumps it.
            # chart_json = json.dumps(chart, ensure_ascii=False)
            # truth_json = json.dumps(truth, ensure_ascii=False)
            
            db.add_case(name, chart, truth, source=source_name)
            print(f"  ✅ Saved: {name} (Wealth: {truth.get('wealth', '?')})")
            valid_count += 1
        except Exception as e:
            print(f"  ❌ DB Error for {name}: {e}")

    print(f"--- Import Summary: {valid_count} / {len(cases)} succeeded ---")
    
    # 3. Trigger Training?
    if auto_train and valid_count > 0:
        print("Step 3: Triggering Auto-Calibration...")
        from core.trainer import ModelTrainer
        trainer = ModelTrainer()
        trainer.train(aspect='wealth', algorithm='svm')
        trainer.train(aspect='career', algorithm='svm')
        print("✅ Models Updated with new data.")

    return valid_count

if __name__ == "__main__":
    # CLI Usage
    parser = argparse.ArgumentParser(description="Import Bazi Cases from Text")
    parser.add_argument("--file", help="Path to text file containing cases")
    parser.add_argument("--text", help="Direct text string input")
    parser.add_argument("--train", action="store_true", help="Auto-train models after import")
    
    args = parser.parse_args()
    
    content = ""
    source = "CLI"
    
    if args.file:
        source = args.file
        if os.path.exists(args.file):
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
    elif args.text:
        content = args.text
        
    if content:
        import_text_cases(content, source_name=source, auto_train=args.train)
    else:
        # Demo Mode
        print("No input provided. Running Demo...")
        demo_text = """
        案例1：乾造，甲子年，丙寅月，戊午日，丁巳时。
        此人早年贫困，但中年行南方火运，开矿发家，资产过亿。
        财富评分：95。事业评分：90。
        
        案例2：坤造，乙丑年，己卯月，辛酉日，壬辰时。
        辛金生于卯月绝地，但坐下酉金强根，又见辰土生合。
        一生平稳公务员，副处级干部。
        财富：60（小资）。事业：75（掌权）。
        """
        import_text_cases(demo_text, source_name="Demo Text", auto_train=True)
