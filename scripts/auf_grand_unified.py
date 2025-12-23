import sys
import os
import json
import numpy as np
import datetime
from typing import Dict, List, Any

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants
from core.trinity.core.physics.wave_laws import WaveState
from core.bazi_profile import VirtualBaziProfile

def generate_grand_unified_report(case_id: str):
    print(f"🚀 [INIT_GRAND_UNIFIED_SIMULATION] Starting full-spectrum audit for {case_id}...")
    
    # 1. Load Case
    case_path = os.path.join(os.path.dirname(__file__), "../tests/data/integrated_extreme_cases.json")
    with open(case_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    case = next((c for c in cases if c['id'] == case_id), None)
    if not case:
        print(f"❌ Case {case_id} not found.")
        return

    # 2. AUF Orchestration
    oracle = TrinityOracle()
    bazi = case['bazi']
    dm = case['day_master']
    
    # Simulate current luck and annual (using birth year as start)
    bi = case['birth_info']
    profile = VirtualBaziProfile(
        pillars={'year': bazi[0], 'month': bazi[1], 'day': bazi[2], 'hour': bazi[3]},
        gender=1 if case['gender'] == '男' else 0,
        day_master=dm,
        birth_date=datetime.datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'])
    )
    
    luck_pillar = profile.get_luck_pillar_at(2024) # Target year
    annual_pillar = profile.get_year_pillar(2024)
    
    # Run Oracle Analysis
    res = oracle.analyze(bazi, dm, luck_pillar=luck_pillar, annual_pillar=annual_pillar)
    
    resonance = res['resonance']
    verdict = res['verdict']
    unified = res['unified_metrics']
    remedy = res['remedy']
    breakdown = res['breakdown']
    
    # --- Generate AUF Report ---
    report_lines = []
    report_lines.append(f"# 🛡️ ANTIGRAVITY V9.3: 大一统集成报告 (AUF Report)")
    report_lines.append(f"**审计对象**: {case_id} | {case['description']}")
    report_lines.append(f"**生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**引擎版本**: Quantum Trinity V2.2 (Genesis Mode)\n")

    report_lines.append("---")
    
    # Phase 1: Diagnostic
    report_lines.append("## 第一部分：物理稳态诊断 (The Diagnostic)")
    report_lines.append(f"### 1.1 系统相态 (Phase State)")
    m_color = "🟢" if resonance.mode == "COHERENT" else "🟡" if resonance.mode == "BEATING" else "🔴"
    report_lines.append(f"- **运行模式**: {m_color} `{resonance.mode}` Mode")
    report_lines.append(f"- **秩序参数 (O)**: `{verdict['order_parameter']:.4f}`")
    report_lines.append(f"- **相干度 (η)**: `{resonance.sync_state:.4f}`")
    report_lines.append(f"- **能效比 (Φ)**: `{resonance.flow_efficiency:.2f}`")
    report_lines.append(f"- **系统碎片化**: `{resonance.fragmentation_index:.2f}`")
    
    report_lines.append(f"\n### 1.2 风险雷达 (Risk Radar)")
    if resonance.mode == "BEATING":
        report_lines.append(f"> [!WARNING]")
        report_lines.append(f"> 检测到 **拍频震荡 (Beating)**。系统包络频率为 ω={resonance.envelop_frequency:.2f}。未来流年与原局相位差可能导致周期性坍缩点。")
    elif resonance.mode == "ANNIHILATION":
        report_lines.append(f"> [!CAUTION]")
        report_lines.append(f"> 检测到 **高能级湮灭 (Annihilation)**。波函数发生严重坍缩，核心稳定性不足。")
    else:
         report_lines.append(f"🟢 系统结构稳定，具备极强的相干锁定。")

    # Unified Metrics Analysis
    if unified:
        report_lines.append(f"\n### 1.3 集成场分析 (Unified Field Analysis)")
        if 'capture' in unified:
            cap = unified['capture']
            c_icon = "✅" if cap['status'] == 'STABLE' else "⚠️"
            report_lines.append(f"- {c_icon} **引力捕获 (Capture η)**: `{cap['efficiency']:.2%}` (食神制杀模式)")
        if 'cutting' in unified:
            cut = unified['cutting']
            ct_icon = "🟢" if cut['status'] == 'STABLE' else "🔥"
            report_lines.append(f"- {ct_icon} **频谱切断 (Cut Depth)**: `{cut['depth']:.2%}` (枭神夺食风险)")
        if 'contamination' in unified:
            cont = unified['contamination']
            cn_icon = "🛡️" if cont['status'] == 'CLEAR' else "☢️"
            report_lines.append(f"- {cn_icon} **介质污染 (Pollution Index)**: `{cont['index']:.2%}` (财星坏印效应)")

    report_lines.append("\n---")
    
    # Phase 2: Remediation
    report_lines.append("## 第二部分：量子干预建议 (The Remediation)")
    
    # Geophysics K_geo Fix
    # Based on DM element, suggest beneficial longitude/latitude shift
    dm_elem, _, _ = BaziParticleNexus.STEMS.get(dm, ("Earth", "", 0))
    geo_remedy = {
        "Wood": "向东移动或回归沿海带 (K_geo: East/Coastal Cluster) 以增强生发能。",
        "Fire": "向南移动 (K_geo: South Cluster) 利用地磁场强度补足红外辐射能。",
        "Earth": "留在中原或山地 (K_geo: Center/Mountain Cluster) 增加质量惯性。",
        "Metal": "向西移动 (K_geo: West Cluster) 提升收敛度与磁场屏蔽力。",
        "Water": "向北移动 (K_geo: North Cluster) 降低环境熵值，利用极向场稳定能量。"
    }
    
    report_lines.append(f"### 2.1 空间修正 (Geophysics Fix)")
    # Logic: if system is weak or unstable, suggest a loc fix based on DM element (or preferred element)
    preferred_elem = dm_elem # Simple logic for demo, usually it's Yong Shen
    if remedy:
        preferred_elem = remedy['optimal_element']

    report_lines.append(f"- **建议坐标微调**: {geo_remedy.get(preferred_elem, '维持现状')}")
    
    # External Particle Injection
    report_lines.append(f"\n### 2.2 量子处方 (Quantum Prescription)")
    if remedy:
        best_p = remedy['best_particle']
        report_lines.append(f"- **核心注入粒子**: `[{best_p}]` (Optimal Particle)")
        report_lines.append(f"- **预期提升**: 相干度有效提升 `+{remedy['improvement']*100:.1f}%` η")
        report_lines.append(f"- **临床建议**: {remedy['description']}")
    else:
        report_lines.append(f"- **量子状态**: 系统已达临界最优相干态，无需外部粒子干预。")

    report_lines.append("\n---")
    
    # Phase 3: Strategic Roadmap
    report_lines.append("## 第三部分：动态人生规划 (The Strategic Roadmap)")
    
    # Strategy based on Brittleness
    report_lines.append(f"### 3.1 攻守策略 (Strategic Stance)")
    b_val = resonance.brittleness
    if b_val > 0.7:
        report_lines.append("- **状态**: **高维极刚态 (High Brittleness)**")
        report_lines.append("- **建议**: 严禁硬碰硬 (Collision Warning)。此时系统虽强但脆，应采取“柔性避障”策略，收缩投机性资产。")
    elif resonance.is_follow:
        report_lines.append("- **状态**: **超导锁定态 (Superconducting)**")
        report_lines.append("- **建议**: 全速扩张 (All-in Momentum)。系统阻抗近乎为零，此阶段应最大化外部做功。")
    else:
        report_lines.append("- **状态**: **平稳阻尼态 (Damped/Normal)**")
        report_lines.append("- **建议**: 稳健经营。利用阶段性波动进行低吸高抛，不宜进行跨量级的行业切换。")
        
    # Rhythm based on Envelope
    report_lines.append(f"\n### 3.2 节律管理 (Rhythm & Timing)")
    if resonance.mode == "BEATING":
        report_lines.append(f"- **节律频率**: ω={resonance.envelop_frequency:.2f}")
        report_lines.append("- **关键波动期**: 每隔 `3-4 单元时间` 将出现一次相位波谷。在波谷期（能量坍缩点）严禁进行重大决策或健康过载。")
    else:
        report_lines.append("- **节律稳态**: 能量波形连续。建议按标准季节周期性调节即可。")

    report_lines.append("\n\n---\n**Antigravity AUF V9.3 | Signature Logic: Phase 31 Unified Simulation**")
    
    # Save report
    report_name = f"reports/AUF_REPORT_{case_id}.md"
    report_content = "\n".join(report_lines)
    
    # Ensure directory exists
    os.makedirs("reports", exist_ok=True)
    
    with open(report_name, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ Full-Spectrum Audit Complete. Report saved to: {report_name}")
    return report_name

if __name__ == "__main__":
    case_to_run = "INTEGRATED_EXTREME_001"
    if len(sys.argv) > 1:
        case_to_run = sys.argv[1]
    
    report_path = generate_grand_unified_report(case_to_run)
    # Output path for agent to read
    print(f"RESULT_FILE:{os.path.abspath(report_path)}")
