import argparse
import json
import os
import sys
import numpy as np
from typing import Dict, Any, List

# 强制依赖
try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ Critical: json-logic-quibble missing.")
    sys.exit(1)

REGISTRY_DIR = "./registry/holographic_pattern"
DEFAULT_DATA = "./data/holographic_universe_518k.jsonl"

def ensure_dirs():
    if not os.path.exists(REGISTRY_DIR): os.makedirs(REGISTRY_DIR)

def load_manifest(path):
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def get_weights_matrix(m):
    # 构建 10x5 权重矩阵
    tmm = m['tensor_mapping_matrix']
    gods = tmm['ten_gods']
    matrix = []
    for god in gods:
        matrix.append(tmm['weights'][god])
    return np.array(matrix), gods # (10, 5)

def calculate_5d_tensor(case_ten_gods, weights_matrix, god_index_map):
    # [物理引擎核心]
    # Input: TenGod Vector (10,)
    # Matrix: Weights (10, 5)
    # Output: Tensor (5,) = Weights.T dot Vector
    
    vec = np.zeros(10)
    for god, val in case_ten_gods.items():
        if god in god_index_map:
            vec[god_index_map[god]] = float(val)
    
    # 矩阵运算: (5, 10) x (10, 1) = (5, 1)
    tensor = np.dot(weights_matrix.T, vec)
    return list(tensor) 

def run_sop(target, manifest_path, data_path):
    print(f"🚀 SOP V3.4 Deductive Running for {target}...")
    
    m = load_manifest(manifest_path)
    weights, gods_list = get_weights_matrix(m)
    god_map = {g: i for i, g in enumerate(gods_list)}
    
    total, hits = 0, 0
    benchmarks = []
    sub_pattern_defs = m.get('sub_pattern_definitions', {})
    sub_stats = {k: 0 for k in sub_pattern_defs.keys()}
    
    # 1. 全量海选 (Census) + 子格局分类
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                case = json.loads(line)
                total += 1
                
                # 逻辑过滤 (Logic Filter)
                if jsonLogic(m['classical_logic_rules']['expression'], case):
                    hits += 1
                    
                    # 2. 子格局分类 (Sub-pattern Classification)
                    for sub_id, sub_def in sub_pattern_defs.items():
                        if jsonLogic(sub_def['logic'], case):
                            sub_stats[sub_id] += 1
                    
                    # 3. 物理投影 (Physics Projection)
                    tensor = calculate_5d_tensor(case['ten_gods'], weights, god_map)
                    
                    # 4. 原石采集 (Mining)
                    if len(benchmarks) < 50:
                        benchmarks.append({
                            "t": [round(x, 4) for x in tensor],
                            "ref": case.get('case_id', f'CASE-{total}'),
                            "note": "Deductive Raw Data"
                        })
            except Exception: continue
            if total % 50000 == 0: print(f"   Scanning {total}...", end='\r')

    abundance = (hits / total * 100) if total > 0 else 0
    
    # 4. 全息封卷 (Registry)
    ensure_dirs()
    registry = {
        "topic": "holographic_pattern", # QGA 协议
        "schema_version": "3.0",
        "data": {
            "pattern_id": target,
            "meta_info": m['meta_info'],
            "population_stats": {
                "base_abundance": round(abundance, 4),
                "sample_size": total,
                "sub_patterns": sub_stats
            },
            "benchmarks": benchmarks
        }
    }
    
    out_path = os.path.join(REGISTRY_DIR, f"{target}.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Registry saved to: {out_path}")
    print(f"   Abundance: {hits}/{total} ({abundance:.2f}%)")
    
    # 子格局统计报告
    if sub_pattern_defs:
        print(f"\n🧩 Sub-pattern Classification Report:")
        for sub_id, count in sub_stats.items():
            sub_abd = (count / hits * 100) if hits > 0 else 0
            name = sub_pattern_defs[sub_id]['name']
            print(f"   • {name} ({sub_id}): {count} samples ({sub_abd:.1f}% of A01 hits)")

    print(f"\n📡 [PUB_EVENT] topic='holographic_pattern' id='{target}'")
    
    # [第017号工程指令] 自动化流水线：Step 6.2后自动触发知识生成
    print(f"\n🧠 [AUTO-PIPELINE] 触发HKB知识生成...")
    try:
        import subprocess
        import sys
        kb_generator_path = os.path.join(os.path.dirname(__file__), "fds_kb_generator.py")
        result = subprocess.run(
            [sys.executable, kb_generator_path, "--target", target],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        if result.returncode == 0:
            print(f"✅ HKB知识生成完成")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"⚠️ HKB知识生成失败（非阻塞）: {result.stderr}")
    except Exception as e:
        print(f"⚠️ HKB知识生成异常（非阻塞）: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--data", default=DEFAULT_DATA)
    args = parser.parse_args()
    run_sop(args.target, args.manifest, args.data)
