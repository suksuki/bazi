import sys
import os
import json
import numpy as np
import datetime
from typing import Dict, List, Any

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants, ArbitrationNexus
from core.profile_manager import ProfileManager
from core.calculator import BaziCalculator

def run_holographic_scan(profile_name: str):
    print(f"📡 [AUF_HOLOGRAPHIC_SCAN] Activating full-spectrum logic scanners for '{profile_name}'...")
    
    pm = ProfileManager()
    profiles = pm.get_all()
    prof = next((p for p in profiles if p['name'] == profile_name), None)
    
    if not prof:
        print(f"❌ Profile '{profile_name}' not found.")
        return

    # 1. Calc Bazi
    calc = BaziCalculator(prof['year'], prof['month'], prof['day'], prof['hour'], prof.get('minute', 0))
    chart = calc.get_chart()
    bazi = [
        f"{chart['year']['stem']}{chart['year']['branch']}",
        f"{chart['month']['stem']}{chart['month']['branch']}",
        f"{chart['day']['stem']}{chart['day']['branch']}",
        f"{chart['hour']['stem']}{chart['hour']['branch']}"
    ]
    dm = bazi[2][0]
    
    # 2. Oracle Analysis
    oracle = TrinityOracle()
    res = oracle.analyze(bazi, dm)
    interactions = res.get("interactions", [])
    resonance = res.get("resonance")
    verdict = res.get("verdict")
    
    # 3. Generate Holographic Report
    report = []
    report.append(f"# 🌌 AUF 全频谱逻辑扫描报告: {profile_name}")
    report.append(f"**核心特征**: {' '.join(bazi)} (日主: {dm})")
    report.append(f"**扫描时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n---")
    
    # Section 1: Destiny Audit
    report.append("## 1. 八字物理诊断报告 (The Destiny Audit)")
    
    m_icon = "☢️" if resonance.mode == "ANNIHILATION" else "💎" if resonance.mode == "COHERENT" else "🐌"
    report.append(f"### 1.1 相态判定 (Phase Result)")
    report.append(f"- **系统相态**: {m_icon} **`{resonance.mode}`** ({resonance.description})")
    report.append(f"- **相干度 η**: `{resonance.sync_state:.4f}`")
    
    report.append(f"\n### 1.2 核心病灶识别 (Bottleneck Identification)")
    if not interactions:
        report.append("- 系统状态: **[BASE_STATE]** 基态运行，未发现强力冲突节点。")
    else:
        sorted_inters = sorted(interactions, key=lambda x: x['priority'])
        primary = sorted_inters[0]
        prio = primary['priority']
        p_desc = "毁灭级" if prio == 0 else "结构级" if prio < 4 else "工程级"
        report.append(f"- **主导病灶**: `[{primary['type']}]` {primary['name']}")
        report.append(f"- **冲突能级**: `PRIO {prio}` ({p_desc})")
        report.append(f"- **物理自洽度**: 正在进行 {p_type if 'p_type' in locals() else '系统'} 级的频谱仲裁。")

    report.append(f"\n### 1.3 能量健康度指标 (Energy Metrics)")
    snr = resonance.sync_state * 1.2
    report.append("| 指标项 | 物理量 | 状态说明 |")
    report.append("| :--- | :--- | :--- |")
    report.append(f"| **SNR (信噪比)** | `{snr:.2f}` | {'理想 (Pure)' if snr > 0.8 else '中庸 (Noisy)' if snr > 0.4 else '混沌 (Chaos)'} |")
    report.append(f"| **Sync (同步率)** | `{resonance.sync_state:.4f}` | 日主与背景场的共振效率 |")
    report.append(f"| **Frag (碎片化)** | `{resonance.fragmentation_index:.2f}` | 结构稳定性指数 |")

    # Section 1.4: Integrated Dynamics
    unified = res.get("unified_metrics")
    if unified:
        report.append(f"\n### 1.4 集成动力学分析 (Integrated Dynamics)")
        UNI_MAP = {"capture": "食神捕获率 (Capture Eff)", "cutting": "枭神切断深度 (Cut Depth)", "contamination": "介质污染指数 (Pollution Index)"}
        for k, v in unified.items():
            label = UNI_MAP.get(k.lower(), k.capitalize())
            val = v.get('efficiency', v.get('depth', v.get('index', 0)))
            report.append(f"- **{label}**: `{val:.2%}` ({v['status']})")

    report.append("\n---")
    
    # Section 2: Quantum Remedy
    report.append("## 2. 八字优化建议与规划 (The Quantum Remedy)")
    
    remedy = res.get('remedy')
    
    # 2.1 Spatial
    report.append("### 2.1 空间能级修复 (Geospatial Fix)")
    DIR_MAP = {"Wood": "正东 (East)", "Fire": "正南 (South)", "Earth": "中心/本地 (Center)", "Metal": "正西 (West)", "Water": "正北 (North)"}
    best_dir = DIR_MAP.get(remedy['optimal_element'], "未知") if remedy else "本地 (Local)"
    report.append(f"- **明确输出**: 建议向 **`[{best_dir}]`** 移动。")
    report.append(f"- **物理原理**: 利用特定方位地磁场补偿系统相位偏移。")

    # 2.2 Particle
    report.append("\n### 2.2 粒子注入处方 (Element Injection)")
    if remedy:
        report.append(f"- **明确输出**: 注入 **`[{remedy['best_particle']}]`** 粒子流 ({remedy['optimal_element']})。")
        report.append(f"  - 推荐行为: 增加与 {remedy['optimal_element']} 频率相关的外部输入。")
    
    # 2.3 Time-Domain
    report.append("\n### 2.3 时域攻守策略 (Time-Domain Strategy)")
    if resonance.mode == "ANNIHILATION":
        report.append("- **操作指令**: **[静默加固]**。系统由于结构性湮灭，目前处于极度脆性期，严禁能量扩张。")
    elif resonance.is_follow:
        report.append("- **操作指令**: **[全速推进]**。系统处于超导态，应最大化释放动能，捕捉市场/人生高能波段。")
    else:
        report.append("- **操作指令**: **[周期套利]**。在波动中寻找基态提升点。")

    report.append("\n\n---\n**Antigravity AUF V9.3 | Full Holographic Compliance**")
    
    # Save Report
    file_name = f"reports/HOLOGRAPHIC_SCAN_{profile_name}.md"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"✅ Holographic Scan Complete. Report: {file_name}")
    return file_name

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "王金星"
    run_holographic_scan(name)
