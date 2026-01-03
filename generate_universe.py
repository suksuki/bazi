#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成全息宇宙样本数据库 (Holographic Universe Generator)
—— 支持 SOP Step 2 逻辑普查的数据生成工具 ——

根据 FDS_ARCHITECTURE_v3.0 规范，生成 518,400 个基础样本数据。

**版本**: V1.0
**状态**: Data Generation Tool
"""

import json
import os
import random
from tqdm import tqdm

# 配置
OUTPUT_DIR = "./data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "holographic_universe_518k.jsonl")

# 天干地支
GAN = list("甲乙丙丁戊己庚辛壬癸")
ZHI = list("子丑寅卯辰巳午未申酉戌亥")

def generate_ganzhi():
    """生成60甲子列表"""
    return [g + z for g in GAN for z in ZHI]

def main():
    """主函数：生成全息宇宙样本数据库"""
    
    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created directory: {OUTPUT_DIR}")
    
    print("=" * 70)
    print("🚀 Generating Holographic Universe (518,400 samples)")
    print("=" * 70)
    print(f"   Output: {OUTPUT_FILE}")
    print(f"   Format: JSONL (one JSON object per line)")
    print("=" * 70)
    
    # 计算总样本数：60年 × 12月 × 60日 × 12时 = 518,400
    total_samples = 518400
    
    # 生成60甲子列表（用于随机选择）
    ganzhi_list = generate_ganzhi()
    
    # 设置随机种子（可选，用于可重现性）
    random.seed(42)
    
    # 打开文件并写入数据
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i in tqdm(range(total_samples), desc="Generating", unit="samples"):
            # 1. 模拟八字（随机生成，用于测试）
            case = {
                "case_id": f"CASE-{i+1:06d}",
                "bazi": {
                    "year": random.choice(ganzhi_list),
                    "month": random.choice(ganzhi_list),
                    "day": random.choice(ganzhi_list),
                    "hour": random.choice(ganzhi_list)
                },
                # 2. 模拟十神统计 (Mock for SOP Step 2 testing)
                # 关键：确保这里有 manifest 需要的 Key (ZG, PS, ZC 等)
                "ten_gods": {
                    "ZG": random.randint(0, 3),
                    "PG": random.randint(0, 3),
                    "ZC": random.randint(0, 3),
                    "PC": random.randint(0, 3),
                    "ZS": random.randint(0, 3),
                    "PS": random.randint(0, 3),
                    "ZR": random.randint(0, 3),
                    "PR": random.randint(0, 3),
                    "ZB": random.randint(0, 3),
                    "PB": random.randint(0, 3)
                },
                # 3. 模拟日主能量 (Mock for SOP testing)
                # 关键：self_energy.E 用于物理公理检查
                "self_energy": {
                    "E": round(random.random(), 3)  # 0.0 ~ 1.0，保留3位小数
                }
            }
            
            # 写入JSONL格式（每行一个JSON对象）
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    
    # 验证文件生成
    file_size = os.path.getsize(OUTPUT_FILE)
    file_size_mb = file_size / (1024 * 1024)
    
    print("\n" + "=" * 70)
    print(f"✅ Generation Complete!")
    print("=" * 70)
    print(f"   File: {OUTPUT_FILE}")
    print(f"   Size: {file_size_mb:.2f} MB")
    print(f"   Samples: {total_samples:,}")
    print(f"   Format: JSONL (one JSON object per line)")
    print("=" * 70)
    print("\n🎯 Ready for SOP Step 2 Real Data Validation.")
    print(f"   Run: python fds_sop_runner.py --target A-01 --manifest config/patterns/manifest_A01.json")

if __name__ == "__main__":
    main()

