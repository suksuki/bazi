import sys
import os
import ollama
import json
from core.config_manager import ConfigManager

def run_logic_benchmark():
    print("🚀 Bazi Logic Benchmark: Starting...")
    
    # 1. Load Config
    cm = ConfigManager()
    host = cm.get('ollama_host', 'http://localhost:11434')
    model = cm.get('selected_model_name', 'qwen2.5')
    
    print(f"📡 Target: {model} @ {host}")
    
    # 2. Define Benchmark Case (Standard Weak Day Master)
    # Case: Weak Wood (Jia) born in Autumn (You Metal month).
    # Needs Water/Wood support.
    
    benchmark_case_text = """
    【Standard Benchmark Case】
    Year: 1990 (Geng Wu) 庚午
    Month: Oct (Yi You) 乙酉
    Day: 5th (Jia Zi) 甲子
    Hour: 12:00 (Geng Wu) 庚午
    
    Analysis Task:
    1. Identify Day Master (日主).
    2. Determine Strength (旺衰) - Is it Weak or Strong?
    3. Identify Favorable Elements (喜用神).
    """
    
    prompt = f"""
    You are a Bazi Logic Evaluation Engine.
    Analyze this chart rigorously.
    
    {benchmark_case_text}
    
    Return JSON only:
    {{
        "day_master": "Stem",
        "strength_verdict": "Weak/Strong/Follow",
        "reasoning": "Short explanation",
        "favorable_elements": ["Element1", "Element2"]
    }}
    """
    
    try:
        # Create Client
        client = ollama.Client(host=host)
        
        # Run Inference
        print("⏳ Reasoning in progress...")
        response = client.chat(model=model, messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        content = response['message']['content']
        print("\n🔎 --- Model Output ---")
        print(content)
        print("-----------------------\n")
        
        # Check correctness (Heuristic)
        is_jia = "Jia" in content or "甲" in content
        is_weak = "Weak" in content or "Weak" in content or "身弱" in content
        has_water = "Water" in content or "水" in content
        
        score = 0
        if is_jia: score += 1
        if is_weak: score += 1
        if has_water: score += 1
        
        print(f"✅ Logic Score: {score}/3")
        if score == 3:
            print("🌟 PASSED: Model understands basic Bazi logic.")
        else:
            print("⚠️ WARNING: Model logic might be flawed for Bazi.")
            
    except Exception as e:
        print(f"❌ Error during benchmark: {e}")

if __name__ == "__main__":
    run_logic_benchmark()
