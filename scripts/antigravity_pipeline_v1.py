import sys
import os
import json
import numpy as np
import datetime
from typing import Dict, List, Any, Optional

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants, ArbitrationNexus
from core.profile_manager import ProfileManager
from core.calculator import BaziCalculator

class AntigravityPipelineV1:
    """
    Industrialized Triple-Phase Analytics Pipeline.
    Phase 1: Global Topology Sensing
    Phase 2: Cascading Simulation Engine
    Phase 3: Synthesis & Action
    """
    
    def __init__(self):
        self.oracle = TrinityOracle()
        self.pm = ProfileManager()
        self.version = "1.0.0-Industrial"

    def run_full_stack(self, profile_name: str) -> Dict[str, Any]:
        """Executes the full Pipeline for a given subject."""
        # --- Phase 0: Data Hydration ---
        profiles = self.pm.get_all()
        prof = next((p for p in profiles if p['name'] == profile_name), None)
        if not prof:
            raise ValueError(f"Profile {profile_name} not found.")

        calc = BaziCalculator(
            prof['year'], 
            prof['month'], 
            prof['day'], 
            prof['hour'], 
            prof.get('minute', 0),
            longitude=prof.get('longitude')
        )
        chart = calc.get_chart()
        bazi = [
            f"{chart['year']['stem']}{chart['year']['branch']}",
            f"{chart['month']['stem']}{chart['month']['branch']}",
            f"{chart['day']['stem']}{chart['day']['branch']}",
            f"{chart['hour']['stem']}{chart['hour']['branch']}"
        ]
        dm = bazi[2][0]

        # --- Phase 1: Global Topology Sensing ---
        # Identifying structural locks and rule triggers via LogicArbitrator (inside Oracle)
        analysis_res = self.oracle.analyze(bazi, dm)
        interactions = analysis_res.get('interactions', [])
        
        # Priority Arbitration
        sorted_triggers = sorted(interactions, key=lambda x: x['priority'])
        primary_trigger = sorted_triggers[0] if sorted_triggers else None
        
        # --- Phase 2: Cascading Simulation Engine ---
        # Wave Resonance + Flux Energy + Unified Dynamics
        resonance = analysis_res.get('resonance')
        waves = analysis_res.get('waves')
        unified = analysis_res.get('unified_metrics')
        remedy = analysis_res.get('remedy')
        
        # --- Phase 3: Synthesis & Action ---
        # Generating the actionable insight structure
        # Pass birth_info for higher report precision
        birth_info = {
            "year": prof['year'], "month": prof['month'], "day": prof['day'], 
            "hour": prof['hour'], "minute": prof.get('minute', 0), 
            "longitude": prof.get('longitude')
        }
        report = self._assemble_report(profile_name, bazi, resonance, primary_trigger, sorted_triggers, unified, remedy, analysis_res.get('verdict'), birth_info)
        
        return {
            "profile": profile_name,
            "bazi": bazi,
            "resonance": resonance,
            "primary_trigger": primary_trigger,
            "report_content": report
        }

    def _assemble_report(self, name, bazi, resonance, primary, all_triggers, unified, remedy, verdict, birth_info=None):
        lines = []
        lines.append(f"# 🧬 Antigravity Pipeline V1: 全息测算报告")
        
        # Header with minute-precision
        b_str = "未知 (Unknown)"
        if birth_info:
            try:
                # Safely format components if they are not None
                y = birth_info.get('year')
                m = birth_info.get('month')
                d = birth_info.get('day')
                h = birth_info.get('hour')
                mn = birth_info.get('minute', 0)
                
                parts = []
                if y is not None: parts.append(str(y))
                if m is not None: parts.append(f"{m:02d}")
                if d is not None: parts.append(f"{d:02d}")
                
                dt_str = "-".join(parts) if parts else ""
                
                time_parts = []
                if h is not None: time_parts.append(f"{h:02d}")
                if mn is not None: time_parts.append(f"{mn:02d}")
                
                tm_str = ":".join(time_parts) if time_parts else ""
                
                if dt_str or tm_str:
                    b_str = f"{dt_str} {tm_str}".strip()
            except (ValueError, TypeError):
                b_str = "格式占位 (Placeholder)"

            if birth_info.get('longitude'):
                 b_str += f" | 经度 (Long): {birth_info.get('longitude')}°"

        lines.append(f"**档案对象**: {name} | **出生时间**: {b_str}")
        lines.append(f"**核心命盘**: {' '.join(bazi)} | **计算引擎**: Quantum Trinity V2.2")
        lines.append(f"**报告生成**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---")

        # Translation Maps
        TYPE_MAP = {
            "SAN_HUI": "三会局", "SAN_HE": "三合局", "LIU_HE": "六合局",
            "CLASH": "地支相冲", "HARMONY": "半合/五合", "HARM": "地支相害",
            "PUNISHMENT": "地支相刑", "RESONANCE": "相位谐振", "OPPOSE": "毁灭对冲",
            "CAPTURE": "逻辑捕获", "CUTTING": "频率切断", "CONTAMINATION": "介质污染"
        }
        MODE_MAP = {
            "ANNIHILATION": "湮灭模式 (Annihilation)",
            "COHERENT": "相干锁定 (Coherent)",
            "BEATING": "拍频震荡 (Beating)",
            "DAMPED": "高阻尼态 (Damped)"
        }

        lines.append("\n## 1. 八字物理诊断报告 (The Destiny Audit)")
        m_icon = "☢️" if resonance.mode == "ANNIHILATION" else "💎" if resonance.mode == "COHERENT" else "🐌"
        lines.append(f"### 1.1 相态判定 (Phase Result)")
        lines.append(f"- **系统相态**: {m_icon} **`{MODE_MAP.get(resonance.mode, resonance.mode)}`**")
        lines.append(f"- **稳态标签**: `{verdict.get('label', 'Unknown')}`")
        
        lines.append(f"\n### 1.2 核心病灶识别 (Bottleneck Identification)")
        if not all_triggers:
            lines.append("- 系统状态: **[BASE_STATE]** 基态运行，未探测到显著波动。")
        else:
            p_desc = "毁灭级" if primary['priority'] == 0 else "结构级" if primary['priority'] < 4 else "工程级"
            p_type = TYPE_MAP.get(primary['type'], primary['type'])
            lines.append(f"- 探测到核心冲突: **`[{p_type}]`**")
            lines.append(f"- 冲突能级: `PRIO {primary['priority']}` ({p_desc})")
            lines.append(f"- 拓扑描述: *{primary['name']}* 正在发生频谱干涉，导致系统总熵激增。")

        lines.append(f"\n### 1.3 能量健康度指标 (Energy Metrics)")
        # Calculate SNR mapping (simple proxy for now)
        snr = resonance.sync_state * 1.2
        lines.append("| 指标项 | 物理量 | 状态说明 |")
        lines.append("| :--- | :--- | :--- |")
        lines.append(f"| **SNR (信噪比)** | `{snr:.2f}` | {'理想 (Pure)' if snr > 0.8 else '中庸 (Noisy)' if snr > 0.4 else '混沌 (Chaos)'} |")
        lines.append(f"| **Sync (同步率)** | `{resonance.sync_state:.4f}` | 系数 η，代表日主与背景场的耦合度 |")
        lines.append(f"| **Frag (碎片化)** | `{resonance.fragmentation_index:.2f}` | 代表结构稳定性，>0.5 存在解体风险 |")
        lines.append(f"| **Flow (能效比)** | `{resonance.flow_efficiency:.2f}` | 系数 Φ，代表能量转换效率 |")

        lines.append("\n---")
        lines.append("## 2. 八字优化建议与规划 (The Quantum Remedy)")
        
        # 2.1 Spatial Fix
        lines.append("### 2.1 空间能级修复 (Geospatial Fix)")
        DIR_MAP = {"Wood": "正东 (East)", "Fire": "正南 (South)", "Earth": "中心/本地 (Center)", "Metal": "正西 (West)", "Water": "正北 (North)"}
        best_dir = DIR_MAP.get(remedy['optimal_element'], "未知") if remedy else "本地 (Local)"
        lines.append(f"- **明确输出**: 建议向 **`[{best_dir}]`** 移动。")
        lines.append(f"- **物理原理**: 利用该方位的特定地磁场频率对冲原局的“相位偏差”，实现能级补偿。")

        # 2.2 Injection
        lines.append("\n### 2.2 粒子注入处方 (Element Injection)")
        if remedy:
            lines.append(f"- **推荐粒子**: **`[{remedy['best_particle']}]`** ({remedy['optimal_element']})")
            lines.append(f"- **落地方案**: 建议增加相关颜色的视觉波段输入，并刻意进行“高频行为”（如特定环境的深度阅读或协作）。")
        else:
            lines.append("- **状态**: 当前系统处于自稳态，暂无需额外粒子注入。")

        # 2.3 Time-Domain
        lines.append("\n### 2.3 时域攻守策略 (Time-Domain Strategy)")
        if resonance.mode == "ANNIHILATION":
            lines.append("- **当前策略**: **[静默加固]**。系统处于波谷 (Wave Trough)，严禁任何大宗能量交换（如投资、扩张），直至屏蔽层重新凝聚。")
        elif resonance.is_follow:
            lines.append("- **当前策略**: **[全速推进]**。系统处于波峰 (Wave Crest)，阻抗极低，应全力释放动能，实现跨维度扩张。")
        else:
            lines.append("- **当前策略**: **[震荡磨合]**。建议保持基态，在波动中寻找结构性机会。")

        lines.append("\n---\n**Antigravity Pipeline V1 | Full Holographic Compliance**")
        return "\n".join(lines)

def start_pipeline_stress_test():
    pipeline = AntigravityPipelineV1()
    # Stress test on 3 archetypes
    test_subjects = ["蒋柯栋", "王金星", "陈晓龙"]
    
    print(f"🚀 [START_PIPELINE_STRESS_TEST] Initiating industrial batch processing for {len(test_subjects)} subjects...")
    
    os.makedirs("reports/pipeline_v1", exist_ok=True)
    
    for subject in test_subjects:
        try:
            print(f"⚙️  Processing {subject}...")
            result = pipeline.run_full_stack(subject)
            report_path = f"reports/pipeline_v1/PIPELINE_STRESS_TEST_{subject}.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(result['report_content'])
            print(f"✅ {subject}: Complete. Mode: {result['resonance'].mode}")
        except Exception as e:
            print(f"❌ {subject}: Failed. Error: {e}")

    print(f"\n✨ Stress Test Finished. Reports saved in reports/pipeline_v1/")

if __name__ == "__main__":
    start_pipeline_stress_test()
