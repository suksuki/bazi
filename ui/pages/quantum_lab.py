import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import numpy as np
import datetime
# V13.0: 已删除未使用的类型导入
from ui.components.unified_input_panel import render_and_collect_input
from facade.bazi_facade import BaziFacade
from utils.constants_manager import get_constants
from utils.notification_manager import get_notification_manager

# MVC Controllers
from controllers.bazi_controller import BaziController
from controllers.quantum_lab_controller import QuantumLabController

# V13.0: 已删除 render_sidebar_case_summary 函数（档案信息显示）

def render():
    st.set_page_config(page_title="Quantum Lab", page_icon="🧪", layout="wide")

    # --- CSS: Quantum Glassmorphism & Animations ---
    st.markdown("""
    <style>
    /* Animation Keyframes */
    @keyframes oat-float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    @keyframes oat-pulse-shield {
        0% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); }
        100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
    }
    @keyframes oat-flow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes oat-alert {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }

    /* Narrative Card Styles */
    .narrative-card {
        position: relative;
        padding: 24px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .narrative-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Card Types */
    .card-mountain {
        background: linear-gradient(135deg, rgba(120, 53, 15, 0.15) 0%, rgba(251, 191, 36, 0.1) 100%);
        border-top: 2px solid rgba(251, 191, 36, 0.4);
    }
    .icon-mountain {
        font-size: 32px;
        animation: oat-float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    }
    
    .card-shield {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(56, 189, 248, 0.1) 100%);
        border-top: 2px solid rgba(56, 189, 248, 0.4);
    }
    .icon-shield {
        font-size: 32px;
        border-radius: 50%;
        animation: oat-pulse-shield 2s infinite;
    }
    
    .card-flow {
        background: linear-gradient(270deg, rgba(6, 78, 59, 0.2), rgba(52, 211, 153, 0.15), rgba(6, 78, 59, 0.2));
        background-size: 200% 200%;
        animation: oat-flow 6s ease infinite;
        border-top: 2px solid rgba(52, 211, 153, 0.4);
    }
    .icon-flow {
        font-size: 32px;
        display: inline-block;
        animation: oat-float 2s ease-in-out infinite;
    }

    .card-danger {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.2) 0%, rgba(248, 113, 113, 0.1) 100%);
        border-top: 2px solid rgba(248, 113, 113, 0.4);
    }
    .icon-danger {
        font-size: 32px;
        animation: oat-alert 1.5s infinite;
    }

    /* Typography */
    .card-title { font-weight: 700; font-size: 1.1rem; margin-bottom: 4px; color: #f1f5f9; letter-spacing: 0.5px; }
    .card-subtitle { font-size: 0.9rem; color: #cbd5e1; margin-bottom: 8px; line-height: 1.4; }
    .card-impact { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; background: rgba(0,0,0,0.3); display: inline-block; color: #a5b4fc; }
    </style>
    """, unsafe_allow_html=True)
    
    def render_narrative_card(event):
        """Renders a single narrative card based on the event payload."""
        ctype = event.get('card_type', 'default')
        
        config = {
            "mountain_alliance": {"css": "card-mountain", "icon": "⛰️", "icon_css": "icon-mountain"},
            "penalty_cap": {"css": "card-shield", "icon": "🛡️", "icon_css": "icon-shield"},
            "mediation": {"css": "card-flow", "icon": "🌊", "icon_css": "icon-flow"},
            "pressure": {"css": "card-danger", "icon": "⚠️", "icon_css": "icon-danger"},
            "control": {"css": "card-shield", "icon": "⚡", "icon_css": "icon-shield"}, 
            "vault_open": {"css": "card-mountain", "icon": "💰", "icon_css": "icon-mountain"},
            "tomb_break": {"css": "card-danger", "icon": "⚰️", "icon_css": "icon-danger"},
            "default": {"css": "", "icon": "📜", "icon_css": ""}
        }
        
        cfg = config.get(ctype, config['default'])
        
        # Determine animation class based on triggers
        anim_trigger = event.get('animation_trigger', '')
        extra_icon_style = ""
        
        html = f"""
        <div class="narrative-card {cfg['css']}">
            <div style="display: flex; align-items: start; gap: 16px;">
                <div class="{cfg['icon_css']}" style="{extra_icon_style}">{cfg['icon']}</div>
                <div style="flex-grow: 1;">
                    <div class="card-title">{event.get('title', 'Unknown Event')}</div>
                    <div class="card-subtitle">{event.get('desc', '')}</div>
                    <div class="card-impact">{event.get('score_delta', '')}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    # --- Load Data ---
    @st.cache_data
    def load_cases():
        path = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
        data = []
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        # Normalize required fields via controller helper (no view-layer inference)
        data = BaziController.normalize_cases(data)
        
        # Load Truth Scores (Side-car)
        truth_path = os.path.join(os.path.dirname(__file__), "../../data/truth_values.json")
        if os.path.exists(truth_path):
            with open(truth_path, 'r') as f:
                truths = json.load(f)
                truth_map = {t['id']: t.get('truth_scores', {}) for t in truths}
                # Merge
                for c in data:
                    if c['id'] in truth_map:
                        c['truth_scores'] = truth_map[c['id']]
        
        # V13.0: MCP上下文注入已移至Controller层，不再在View层处理
        
        return data

    cases = load_cases()


    # --- 统一输入面板置顶（P2 专用） ---
    st.session_state["era_key_prefix"] = "era_p2"
    consts = get_constants()
    controller = BaziController()
    bazi_facade = BaziFacade(controller=controller)
    selected_case, era_factor, city_for_controller = render_and_collect_input(
        bazi_facade, cases=cases, is_quantum_lab=True
    )

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    
    # V50.0: 提前加载黄金配置（供所有边栏参数使用）
    # [V10.3] 使用ConfigModel统一管理配置，确保实时同步
    from core.models.config_model import ConfigModel
    config_model = ConfigModel()
    golden_config = config_model.load_config()
    
    # === 算法参数调优控制台 ===（移到最顶部）
    st.sidebar.subheader("🎛️ 算法参数调优")
    
    # 导入配置（仅用于读取默认值）
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    
    # Defaults
    import copy
    fp = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # V50.0: golden_config 已在前面加载，这里直接使用
    
    # V13.0: 统一的深度合并函数
    def deep_merge_params(target, source):
        """深度合并参数，source 覆盖 target"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                deep_merge_params(target[key], value)
            else:
                target[key] = value
    
    # V13.0: 合并边栏滑块的值到配置中
    def merge_sidebar_values_to_config(config):
        """将边栏滑块的值合并到配置中"""
        # 宫位权重
        if 'pg_y' in st.session_state:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['year'] = st.session_state['pg_y']
        if 'pg_m' in st.session_state:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['month'] = st.session_state['pg_m']
        if 'pg_d' in st.session_state:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['day'] = st.session_state['pg_d']
        if 'pg_h' in st.session_state:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['hour'] = st.session_state['pg_h']
        
        # Phase 1 其他参数
        # [V13.1] 参数清洗：删除 season_dominance_boost, floating_peer_penalty, dayun/liunian 参数
        # 这些参数在 Phase 1 中不再使用，避免干扰自动校准器
        if 'physics_self_punishment_damping' in st.session_state:
            config.setdefault('physics', {})['self_punishment_damping'] = st.session_state['physics_self_punishment_damping']
        
        # Structure 参数
        if 's_rw' in st.session_state:
            config.setdefault('structure', {})['rootingWeight'] = st.session_state['s_rw']
        if 's_eb' in st.session_state:
            config.setdefault('structure', {})['exposedBoost'] = st.session_state['s_eb']
        if 's_sp' in st.session_state:
            config.setdefault('structure', {})['samePillarBonus'] = st.session_state['s_sp']
        
        # V13.1: 季节权重参数
        if 'sw_wang' in st.session_state:
            config.setdefault('physics', {}).setdefault('seasonWeights', {})['wang'] = st.session_state['sw_wang']
        if 'sw_xiang' in st.session_state:
            config.setdefault('physics', {}).setdefault('seasonWeights', {})['xiang'] = st.session_state['sw_xiang']
        if 'sw_xiu' in st.session_state:
            config.setdefault('physics', {}).setdefault('seasonWeights', {})['xiu'] = st.session_state['sw_xiu']
        if 'sw_qiu' in st.session_state:
            config.setdefault('physics', {}).setdefault('seasonWeights', {})['qiu'] = st.session_state['sw_qiu']
        if 'sw_si' in st.session_state:
            config.setdefault('physics', {}).setdefault('seasonWeights', {})['si'] = st.session_state['sw_si']
        
        # Phase 2: 动态交互层参数
        interactions_config = config.setdefault('interactions', {})
        branch_events = interactions_config.setdefault('branchEvents', {})
        stem_combine = interactions_config.setdefault('stemFiveCombination', {})
        
        # 天干五合参数
        if 'p2_combine_threshold' in st.session_state:
            stem_combine['threshold'] = st.session_state['p2_combine_threshold']
        if 'p2_combine_bonus' in st.session_state:
            stem_combine['bonus'] = st.session_state['p2_combine_bonus']
        if 'p2_combine_penalty' in st.session_state:
            stem_combine['penalty'] = st.session_state['p2_combine_penalty']
        
        # 冲的折损
        if 'p2_clash_damping' in st.session_state:
            branch_events['clashDamping'] = st.session_state['p2_clash_damping']
        
        # 合局参数
        if 'p2_three_harmony_bonus' in st.session_state:
            branch_events.setdefault('threeHarmony', {})['bonus'] = st.session_state['p2_three_harmony_bonus']
        if 'p2_half_harmony_bonus' in st.session_state:
            branch_events.setdefault('halfHarmony', {})['bonus'] = st.session_state['p2_half_harmony_bonus']
        if 'p2_arch_harmony_bonus' in st.session_state:
            branch_events.setdefault('archHarmony', {})['bonus'] = st.session_state['p2_arch_harmony_bonus']
        if 'p2_six_harmony_bonus' in st.session_state:
            branch_events.setdefault('sixHarmony', {})['bonus'] = st.session_state['p2_six_harmony_bonus']
        if 'p2_six_harmony_binding' in st.session_state:
            branch_events.setdefault('sixHarmony', {})['bindingPenalty'] = st.session_state['p2_six_harmony_binding']
        if 'p2_three_meeting_bonus' in st.session_state:
            branch_events.setdefault('threeMeeting', {})['bonus'] = st.session_state['p2_three_meeting_bonus']
        
        return config
        
    # 将黄金参数合并到 fp（用于深度调优面板）
    if golden_config:
        deep_merge_params(fp, golden_config)
    
    # V13.0: 已删除 AI Command Center 功能（远程控制功能不再使用）
    
    # --- Panel 1: 基础场域 (Physics) ---
    # [V12.1] Phase 1: 初始能量场参数调优
    with st.sidebar.expander("🌍 Phase 1: 初始能量场 (Initial Energy Field)", expanded=True):
        st.caption("**V12.1 核心参数** - 这是能量的源头，源头错了，后面传播得再好也是错的")
        
        st.markdown("**📍 宫位引力 (Pillar Gravity)**")
        # V13.0: 只在首次加载时从 Model 读取，之后保留用户的修改
        # 如果 session_state 中已有值，使用 session_state 的值（保留用户修改）
        # 如果 session_state 中没有值，从 Model 读取默认值
        if 'pg_y' not in st.session_state or 'pg_m' not in st.session_state or 'pg_d' not in st.session_state or 'pg_h' not in st.session_state:
            # 首次加载：从 Model 读取配置
            current_golden_config = config_model.load_config()
            default_year = current_golden_config.get('physics', {}).get('pillarWeights', {}).get('year', fp['physics']['pillarWeights']['year'])
            default_month = current_golden_config.get('physics', {}).get('pillarWeights', {}).get('month', fp['physics']['pillarWeights']['month'])
            default_day = current_golden_config.get('physics', {}).get('pillarWeights', {}).get('day', fp['physics']['pillarWeights']['day'])
            default_hour = current_golden_config.get('physics', {}).get('pillarWeights', {}).get('hour', fp['physics']['pillarWeights']['hour'])
            
            # 初始化 session_state（仅在首次加载时）
            st.session_state['pg_y'] = default_year
            st.session_state['pg_m'] = default_month
            st.session_state['pg_d'] = default_day
            st.session_state['pg_h'] = default_hour
        else:
            # 使用 session_state 中的值（保留用户修改）
            default_year = st.session_state['pg_y']
            default_month = st.session_state['pg_m']
            default_day = st.session_state['pg_d']
            default_hour = st.session_state['pg_h']
        
        pg_year = st.slider("年柱 (Year)", 0.5, 1.5, value=default_year, step=0.05, key='pg_y')
        pg_month = st.slider("月令 (Month) ⭐", 0.5, 2.0, value=default_month, step=0.1, key='pg_m',
                            help="**核心参数**：月令权重是身强身弱判定的基石，建议范围 1.0-1.5")
        pg_day = st.slider("日主 (Day)", 0.5, 2.0, value=default_day, step=0.05, key='pg_d',
                          help="**V13.1调优**：日支权重从1.2提升到1.35，解决Group C倒挂问题")
        pg_hour = st.slider("时柱 (Hour)", 0.5, 1.5, value=default_hour, step=0.05, key='pg_h')
        
        st.divider()
        st.markdown("**⚡ 五态相对论 (Five States Relativity)**")
        st.caption("**V2.6 核心算法总纲** - 五行能量取决于与月令的相对关系")
        
        # V13.1: 添加季节权重滑块（旺相休囚死）
        cal_season_weights = golden_config.get('physics', {}).get('seasonWeights', fp['physics'].get('seasonWeights', {}))
        
        # 初始化季节权重到 session_state
        if 'sw_wang' not in st.session_state:
            st.session_state['sw_wang'] = cal_season_weights.get('wang', 1.2)
        if 'sw_xiang' not in st.session_state:
            st.session_state['sw_xiang'] = cal_season_weights.get('xiang', 1.0)
        if 'sw_xiu' not in st.session_state:
            st.session_state['sw_xiu'] = cal_season_weights.get('xiu', 0.9)
        if 'sw_qiu' not in st.session_state:
            st.session_state['sw_qiu'] = cal_season_weights.get('qiu', 0.6)
        if 'sw_si' not in st.session_state:
            st.session_state['sw_si'] = cal_season_weights.get('si', 0.45)
        
        sw_wang = st.slider("旺 (Wang/Prosperous)", 1.0, 1.5, value=st.session_state['sw_wang'], step=0.05, key='sw_wang',
                           help="同频共振：日干与月令五行相同")
        sw_xiang = st.slider("相 (Xiang/Assist)", 0.8, 1.2, value=st.session_state['sw_xiang'], step=0.05, key='sw_xiang',
                            help="能量注入：月令生助日干")
        sw_xiu = st.slider("休 (Xiu/Rest)", 0.6, 1.0, value=st.session_state['sw_xiu'], step=0.05, key='sw_xiu',
                          help="**V13.1调优**：能量耗散（泄气），从0.85提升到0.90")
        sw_qiu = st.slider("囚 (Qiu/Trapped)", 0.4, 0.8, value=st.session_state['sw_qiu'], step=0.05, key='sw_qiu',
                          help="能量做功：日干克月令（耗身）")
        sw_si = st.slider("死 (Si/Dead)", 0.2, 0.6, value=st.session_state['sw_si'], step=0.05, key='sw_si',
                         help="**V13.1调优**：能量坍缩（被克），从0.50降低到0.45")
        
        st.divider()
        st.markdown("**⚡ Phase 1 其他参数**")
        
        # [V13.1] 参数清洗：删除季节主导加成（season_dominance_boost）
        # 理由：已有 seasonWeights.wang (1.2) 和 pillarWeights.month (1.2-1.3)，避免能量通胀
        
        # [V12.1] 自刑惩罚
        # V13.0: 保留用户修改，只在首次加载时从 Model 读取
        if 'physics_self_punishment_damping' not in st.session_state:
            default_self_punishment = golden_config.get('physics', {}).get('self_punishment_damping', fp['physics'].get('self_punishment_damping', 0.2))
            st.session_state['physics_self_punishment_damping'] = default_self_punishment
        else:
            default_self_punishment = st.session_state['physics_self_punishment_damping']
        
        self_punishment_damping = st.slider(
            "自刑惩罚 (Self-Punishment Damping)",
            min_value=0.0, max_value=1.0,
            value=default_self_punishment,
            step=0.05, key='physics_self_punishment_damping',
            help="自刑地支能量保留比例（原硬编码0.2=保留20%）。建议范围：0.1-0.3"
        )
        
        # [V13.1] 参数清洗：隐藏大运/流年参数（Phase 1 只看原局）
        # 大运流年是 Phase 2+ 才需要的"时间引力场"，在 Phase 1 中会干扰自动校准器
        # 这些参数在代码中仍然保留（用于 Phase 2+），但不在 Phase 1 UI 中显示
        
        # [V13.1] 参数清洗：删除虚浮比劫惩罚（floating_peer_penalty）
        # 理由：无根的虚弱应完全由通根饱和函数 (Tanh/Sigmoid) 的低端形态决定
        
        # V13.3: Phase 1 已完成，只显示状态
        st.divider()
        st.markdown("**✅ Phase 1 验证状态**")
        st.caption("**V13.3 已完成** - 所有规则验证通过")

    # [V13.5] Phase 2: 动态交互层参数调优
    with st.sidebar.expander("⚡ Phase 2: 动态生克场 (Dynamic Interaction Field)", expanded=False):
        st.caption("**V13.5 核心参数** - 这是能量的舞蹈，生克制化的流转规则（已解耦合局参数）")
        
        # 获取 flow 和 interactions 配置
        flow_config = golden_config.get('flow', {})
        interactions_config = golden_config.get('interactions', {})
        
        # ===== 第一组：流体力学参数 (Fluid Dynamics) =====
        st.markdown("**🌊 流体力学参数 (Fluid Dynamics)**")
        st.caption("用于计算普通的生克泄耗（对应 Group D 和 E）")
        
        # generationEfficiency: 生的效率
        if 'p2_gen_eff' not in st.session_state:
            st.session_state['p2_gen_eff'] = flow_config.get('generationEfficiency', 0.7)
        gen_eff = st.slider(
            "生的效率 (Generation Efficiency)",
            min_value=0.3, max_value=1.0,
            value=st.session_state['p2_gen_eff'],
            step=0.05, key='p2_gen_eff',
            help="甲木生丙火，甲木付出100，丙火实际得到70（传输损耗30%）"
        )
        
        # generationDrain: 泄的程度
        if 'p2_gen_drain' not in st.session_state:
            st.session_state['p2_gen_drain'] = flow_config.get('generationDrain', 0.3)
        gen_drain = st.slider(
            "泄的程度 (Generation Drain)",
            min_value=0.1, max_value=0.6,
            value=st.session_state['p2_gen_drain'],
            step=0.05, key='p2_gen_drain',
            help="甲木生丙火，甲木自身减损30%（生别人很累）"
        )
        
        # controlImpact: 克的破坏力
        if 'p2_ctrl_impact' not in st.session_state:
            st.session_state['p2_ctrl_impact'] = flow_config.get('controlImpact', 0.5)
        ctrl_impact = st.slider(
            "克的破坏力 (Control Impact)",
            min_value=0.2, max_value=0.8,
            value=st.session_state['p2_ctrl_impact'],
            step=0.05, key='p2_ctrl_impact',
            help="水克火，火的能量直接打5折（防止克过头变成'斩尽杀绝'）"
        )
        
        # dampingFactor: 系统阻尼
        if 'p2_damping' not in st.session_state:
            st.session_state['p2_damping'] = flow_config.get('dampingFactor', 0.1)
        damping = st.slider(
            "系统阻尼/熵增 (Damping Factor)",
            min_value=0.0, max_value=0.3,
            value=st.session_state['p2_damping'],
            step=0.01, key='p2_damping',
            help="每次能量传递的自然损耗，防止数值爆炸"
        )
        
        st.divider()
        
        # ===== 第二组：空间场参数 (Spatial Field) =====
        st.markdown("**📏 空间场参数 (Spatial Field)**")
        st.caption("用于计算距离对生克的影响（对应 Group C 在动态中的表现）")
        
        spatial_config = flow_config.get('spatialDecay', {})
        
        # gap0: 同柱
        if 'p2_gap0' not in st.session_state:
            st.session_state['p2_gap0'] = spatial_config.get('gap0', 1.0)
        gap0 = st.slider(
            "同柱 (Same Pillar)",
            min_value=0.8, max_value=1.0,
            value=st.session_state['p2_gap0'],
            step=0.05, key='p2_gap0',
            help="如甲寅中的甲和寅：无衰减"
        )
        
        # gap1: 相邻
        if 'p2_gap1' not in st.session_state:
            st.session_state['p2_gap1'] = spatial_config.get('gap1', 0.9)
        gap1 = st.slider(
            "相邻 (Adjacent)",
            min_value=0.6, max_value=1.0,
            value=st.session_state['p2_gap1'],
            step=0.05, key='p2_gap1',
            help="年干生月干：损失小"
        )
        
        # gap2: 隔一柱
        if 'p2_gap2' not in st.session_state:
            st.session_state['p2_gap2'] = spatial_config.get('gap2', 0.6)
        gap2 = st.slider(
            "隔一柱 (One Gap)",
            min_value=0.3, max_value=0.8,
            value=st.session_state['p2_gap2'],
            step=0.05, key='p2_gap2',
            help="年干生日干：损失大"
        )
        
        # gap3: 隔两柱
        if 'p2_gap3' not in st.session_state:
            st.session_state['p2_gap3'] = spatial_config.get('gap3', 0.3)
        gap3 = st.slider(
            "隔两柱 (Two Gaps)",
            min_value=0.1, max_value=0.5,
            value=st.session_state['p2_gap3'],
            step=0.05, key='p2_gap3',
            help="年干生时干：遥不可及"
        )
        
        st.divider()
        
        # ===== 第三组：量子纠缠参数 (Quantum Interactions) =====
        st.markdown("**🧲 量子纠缠参数 (Quantum Interactions)**")
        st.caption("用于计算干支的合化与刑冲（对应 Group F）")
        
        stem_combine = interactions_config.get('stemFiveCombination', {})
        branch_events = interactions_config.get('branchEvents', {})
        
        # stemFiveCombination.threshold: 合化阈值
        if 'p2_combine_threshold' not in st.session_state:
            st.session_state['p2_combine_threshold'] = stem_combine.get('threshold', 1.5)
        combine_threshold = st.slider(
            "合化阈值 (Combine Threshold)",
            min_value=0.8, max_value=2.5,
            value=st.session_state['p2_combine_threshold'],
            step=0.1, key='p2_combine_threshold',
            help="需要月令支持度 > 1.5 才能合化成功（决定甲己合土是'化气'还是'羁绊'）"
        )
        
        # stemFiveCombination.bonus: 合化增益
        if 'p2_combine_bonus' not in st.session_state:
            st.session_state['p2_combine_bonus'] = stem_combine.get('bonus', 1.5)
        combine_bonus = st.slider(
            "合化增益 (Combine Bonus)",
            min_value=1.0, max_value=2.5,
            value=st.session_state['p2_combine_bonus'],
            step=0.1, key='p2_combine_bonus',
            help="如果合化成功（如甲己化土），产生的新土能量的倍率"
        )
        
        # stemFiveCombination.penalty: 合化失败惩罚
        if 'p2_combine_penalty' not in st.session_state:
            st.session_state['p2_combine_penalty'] = stem_combine.get('penalty', 0.5)
        combine_penalty = st.slider(
            "合化失败惩罚 (Combine Penalty)",
            min_value=0.2, max_value=0.8,
            value=st.session_state['p2_combine_penalty'],
            step=0.05, key='p2_combine_penalty',
            help="合而不化时，双方能量均受损的折损率"
        )
        
        # branchEvents.clashDamping: 冲的折损
        if 'p2_clash_damping' not in st.session_state:
            st.session_state['p2_clash_damping'] = branch_events.get('clashDamping', 0.4)
        clash_damping = st.slider(
            "冲的折损 (Clash Damping)",
            min_value=0.2, max_value=0.7,
            value=st.session_state['p2_clash_damping'],
            step=0.05, key='p2_clash_damping',
            help="子午冲导致双方能量都大幅削减，且σ(不确定度)暴增"
        )
        
        # [V13.5] 解耦"合"的参数，区分三合/半合/拱合/六合的物理差异
        st.markdown("**🔗 合局参数 (Harmony Parameters)**")
        st.caption("**V13.5 物理模型** - 三合(共振质变) > 半合(不完全共振) > 拱合(虚拱) > 六合(磁力吸附)")
        
        # threeHarmony: 三合 (120°相位，共振质变)
        three_harmony_config = branch_events.get('threeHarmony', {})
        if isinstance(three_harmony_config, dict):
            three_bonus_default = three_harmony_config.get('bonus', 2.0)
        else:
            three_bonus_default = 2.0  # 向后兼容
        
        if 'p2_three_harmony_bonus' not in st.session_state:
            st.session_state['p2_three_harmony_bonus'] = three_bonus_default
        three_harmony_bonus = st.slider(
            "三合增益 (Three Harmony Bonus)",
            min_value=1.5, max_value=3.0,
            value=st.session_state['p2_three_harmony_bonus'],
            step=0.1, key='p2_three_harmony_bonus',
            help="120°相位，共振质变，能量翻倍（化气）"
        )
        
        # halfHarmony: 半合 (不完全共振)
        half_harmony_config = branch_events.get('halfHarmony', {})
        if isinstance(half_harmony_config, dict):
            half_bonus_default = half_harmony_config.get('bonus', 1.4)
        else:
            half_bonus_default = 1.4
        
        if 'p2_half_harmony_bonus' not in st.session_state:
            st.session_state['p2_half_harmony_bonus'] = half_bonus_default
        half_harmony_bonus = st.slider(
            "半合增益 (Half Harmony Bonus)",
            min_value=1.0, max_value=2.0,
            value=st.session_state['p2_half_harmony_bonus'],
            step=0.1, key='p2_half_harmony_bonus',
            help="不完全共振，能量中等提升（生旺半合/墓旺半合）"
        )
        
        # archHarmony: 拱合 (缺中神，虚拱)
        arch_harmony_config = branch_events.get('archHarmony', {})
        if isinstance(arch_harmony_config, dict):
            arch_bonus_default = arch_harmony_config.get('bonus', 1.1)
        else:
            arch_bonus_default = 1.1
        
        if 'p2_arch_harmony_bonus' not in st.session_state:
            st.session_state['p2_arch_harmony_bonus'] = arch_bonus_default
        arch_harmony_bonus = st.slider(
            "拱合增益 (Arch Harmony Bonus)",
            min_value=1.0, max_value=1.5,
            value=st.session_state['p2_arch_harmony_bonus'],
            step=0.05, key='p2_arch_harmony_bonus',
            help="缺中神，虚拱，能量微升（生墓半合）"
        )
        
        # sixHarmony: 六合 (磁力吸附，物理羁绊)
        six_harmony_config = branch_events.get('sixHarmony', {})
        if isinstance(six_harmony_config, dict):
            six_bonus_default = six_harmony_config.get('bonus', 1.3)
            six_binding_default = six_harmony_config.get('bindingPenalty', 0.2)
        else:
            six_bonus_default = 1.3  # 向后兼容
            six_binding_default = 0.2
        
        if 'p2_six_harmony_bonus' not in st.session_state:
            st.session_state['p2_six_harmony_bonus'] = six_bonus_default
        six_harmony_bonus = st.slider(
            "六合增益 (Six Harmony Bonus)",
            min_value=1.0, max_value=2.0,
            value=st.session_state['p2_six_harmony_bonus'],
            step=0.1, key='p2_six_harmony_bonus',
            help="磁力吸附，物理羁绊，能量提升但活性降低"
        )
        
        if 'p2_six_harmony_binding' not in st.session_state:
            st.session_state['p2_six_harmony_binding'] = six_binding_default
        six_harmony_binding = st.slider(
            "六合羁绊惩罚 (Six Harmony Binding Penalty)",
            min_value=0.0, max_value=0.5,
            value=st.session_state['p2_six_harmony_binding'],
            step=0.05, key='p2_six_harmony_binding',
            help="羁绊惩罚：活性/对外输出降低（贪合忘生/贪合忘冲）"
        )
        
        # threeMeeting: 三会 (方局，力量最强)
        three_meeting_config = branch_events.get('threeMeeting', {})
        if isinstance(three_meeting_config, dict):
            three_meeting_bonus_default = three_meeting_config.get('bonus', 2.5)
        else:
            three_meeting_bonus_default = 2.5  # 向后兼容
        
        if 'p2_three_meeting_bonus' not in st.session_state:
            st.session_state['p2_three_meeting_bonus'] = three_meeting_bonus_default
        three_meeting_bonus = st.slider(
            "三会增益 (Three Meeting Bonus)",
            min_value=2.0, max_value=5.0,
            value=st.session_state['p2_three_meeting_bonus'],
            step=0.1, key='p2_three_meeting_bonus',
            help="方局能量，力量最强（寅卯辰=东方木等），应超过三合局"
        )
        
        st.divider()
        st.markdown("**🚧 Phase 2 验证状态**")
        st.caption("**开发中** - 动态交互验证器即将上线")

    # --- Panel 2: 粒子动态 (Structure) ---
    with st.sidebar.expander("⚛️ 粒子动态 (Structure)", expanded=False):
        st.caption("垂直作用 (Vertical)")
        # V13.0: 保留用户修改，只在首次加载时从 Model 读取
        cal_structure = golden_config.get('structure', {})
        
        if 's_rw' not in st.session_state:
            default_rooting = cal_structure.get('rootingWeight', fp['structure']['rootingWeight'])
            st.session_state['s_rw'] = default_rooting
        else:
            default_rooting = st.session_state['s_rw']
        
        if 's_eb' not in st.session_state:
            default_exposed = cal_structure.get('exposedBoost', fp['structure']['exposedBoost'])
            st.session_state['s_eb'] = default_exposed
        else:
            default_exposed = st.session_state['s_eb']
        
        if 's_sp' not in st.session_state:
            default_same = cal_structure.get('samePillarBonus', fp['structure']['samePillarBonus'])
            st.session_state['s_sp'] = default_same
        else:
            default_same = st.session_state['s_sp']
        
        root_w = st.slider("通根系数 (Rooting)", 0.5, 2.0, default_rooting, 0.1, key='s_rw')
        exposed_b = st.slider("透干加成 (Exposed)", 1.0, 3.0, default_exposed, 0.1, key='s_eb')
        same_pill = st.slider("自坐强根 (Sitting)", 2.0, 4.0, default_same, 0.1, key='s_sp',
                             help="**V13.2调优**：搜索范围从2.0开始（原1.0），默认3.0，确保自坐强根优势足够明显")
        
        st.caption("特殊状态 (Special)")
        void_p = st.slider("⚫ 黑洞/空亡 (Void)", 0.0, 1.0, fp['structure']['voidPenalty'], 0.1, key='s_vp', help="0=空掉，1=不空")

    # --- Panel 3: 几何交互 (Interactions) ---
    with st.sidebar.expander("⚗️ 几何交互 (Interactions)", expanded=False):
        st.caption("⚠️ 部分参数已移至 Phase 2，请使用 Phase 2 参数调优面板")
        
        # [V13.3] 删除重复参数：stemFiveCombination (threshold, bonus, penalty) 和 branchEvents.clashDamping
        # 这些参数已在 Phase 2 中统一管理
        
        # 保留争合损耗（Phase 2 中没有）
        jealousy_d = st.slider("争合损耗 (Jealousy)", 0.0, 0.5, fp['interactions']['stemFiveCombination'].get('jealousyDamping', 0.3), 0.05, key='i_s5_jd')

        st.caption("地支成局 (Branch Combo)")
        cp = fp['interactions'].get('comboPhysics', {'resolutionCost': 0.1})
        
        # [V15.3] 参数清理：删除重复的三合/半合/拱合/三会参数（已移至 Phase 2）
        # 保留解冲消耗（Phase 2 中没有这个参数）
        resolution_cost_val = cp.get('resolutionCost', 0.1)
        
        cp_rc = st.number_input("解冲消耗 (Resolution Cost)", 0.0, 1.0, resolution_cost_val, 0.05, key='cp_rc',
                               help="贪合忘冲：当节点被合住时，冲的伤害降低或失效")
        
        # 添加提示信息
        st.info("💡 **三合/半合/拱合/三会** 参数已移至 **Phase 2: 动态生克场**，请使用 Phase 2 参数调优面板")

    # --- Panel 4: 能量流转 (Flow) ---
    with st.sidebar.expander("🌊 能量流转 (Flow / Damping)", expanded=False):
        st.caption("🛡️ 阻尼协议 (Damping Protocol)")
        
        # safely get nested dicts
        f_conf = fp.get('flow', {})
        res_imp = f_conf.get('resourceImpedance', {'base': 0.3, 'weaknessPenalty': 0.5})
        out_vis = f_conf.get('outputViscosity', {'maxDrainRate': 0.6, 'drainFriction': 0.2})
        entropy = f_conf.get('globalEntropy', 0.05)
        
        st.markdown("**输入阻抗 (Resource Impedance)**")
        imp_base = st.slider("基础阻抗 (Base)", 0.0, 0.9, res_imp.get('base', 0.3), 0.05, key='f_ri_b')
        imp_weak = st.slider("虚不受补 (Weak Penalty)", 0.0, 1.0, res_imp.get('weaknessPenalty', 0.5), 0.1, key='f_ri_wp')
        
        st.markdown("**输出粘滞 (Output Viscosity)**")
        vis_rate = st.slider("最大泄耗 (Max Drain)", 0.1, 1.0, out_vis.get('maxDrainRate', 0.6), 0.05, key='f_ov_md')
        vis_fric = st.slider("输出阻力 (Friction)", 0.0, 0.5, out_vis.get('drainFriction', 0.2), 0.05, key='f_ov_df')
        
        st.markdown("**系统熵 (System Entropy)**")
        sys_ent = st.slider("全局熵增 (Entropy)", 0.0, 0.3, entropy, 0.01, key='f_ge')
        
        st.divider()
        st.caption("核心流转参数 (Core Flow)")
        output_drain = st.slider("食伤泄耗 (Output Drain)", 1.0, 4.5, f_conf.get('outputDrainPenalty', 2.0), 0.1, key='f_od',
                                help="日主生食伤时的额外损耗惩罚（影响能量计算）")
        
        # [V13.3] 删除重复参数：controlImpact 和 spatialDecay
        # 这些参数已在 Phase 2 中统一管理（Phase 2 有完整的 gap0, gap1, gap2, gap3）
        st.info("💡 **controlImpact** 和 **spatialDecay** 参数已移至 **Phase 2: 动态生克场**，请使用 Phase 2 参数调优面板")
        
        # Update param struct for write-back (不包含已移至 Phase 2 的参数)
        fp['flow'] = {
            'resourceImpedance': {'base': imp_base, 'weaknessPenalty': imp_weak},
            'outputViscosity': {'maxDrainRate': vis_rate, 'drainFriction': vis_fric},
            'globalEntropy': sys_ent,
            'outputDrainPenalty': output_drain
            # controlImpact 和 spatialDecay 已移至 Phase 2
        }

    # --- Panel 6: 旺衰概率场 (Strength Probability Field) [V10.0] ---
    # 注意：这是第一层验证（旺衰判定）专用参数，不包含财富相关参数
    with st.sidebar.expander("⚛️ 旺衰概率场 (V10.0 Strength Probability Field)", expanded=False):
        st.caption("V10.0 旺衰判定核心参数（第一层物理验证）")
        st.caption("💡 提示：调优后的参数会自动从 config/parameters.json 加载")
        
        # [V10.3] 确保使用最新的配置（从ConfigModel加载）
        strength_config = golden_config.get('strength', fp.get('strength', {}))
        gat_config = golden_config.get('gat', fp.get('gat', {}))
        
        st.markdown("**⚡ 相变临界点 (Critical Point)**")
        energy_threshold_center = st.slider(
            "能量阈值中心点 (Energy Threshold Center)",
            min_value=1.0, max_value=5.0,
            value=strength_config.get('energy_threshold_center', 2.89),
            step=0.01, key='strength_energy_threshold',
            help="定义身强身弱的物理中枢。Jason D案例优化：2.89（从3.0调整）"
        )
        
        st.markdown("**🌊 概率波带宽 (Transition Width)**")
        phase_transition_width = st.slider(
            "相变宽度 (Phase Transition Width)",
            min_value=1.0, max_value=20.0,
            value=strength_config.get('phase_transition_width', 10.0),
            step=0.5, key='strength_phase_width',
            help="定义强弱转换的模糊带宽度（Sigmoid斜率），值越大曲线越平缓"
        )
        
        st.markdown("**🛡️ 从格阈值 (Follower Threshold)**")
        follower_threshold = st.slider(
            "从格判定阈值 (Follower Threshold)",
            min_value=0.05, max_value=0.3,
            value=strength_config.get('follower_threshold', 0.15),
            step=0.01, key='strength_follower_threshold',
            help="当strength_probability < 此值时，判定为Follower（从格）。用于解决乔丹、溥仪等从格案例。调优建议：0.1-0.2"
        )
        
        st.markdown("**⚖️ 判定阈值 (Judgment Thresholds)** [V12.1]")
        st.caption("💡 调整这些阈值可以解决'概率高却判定为弱'的问题")
        
        weak_score_threshold = st.slider(
            "弱判定分数阈值 (Weak Score Threshold)",
            min_value=20.0, max_value=60.0,
            value=strength_config.get('weak_score_threshold', 40.0),
            step=1.0, key='strength_weak_score_threshold',
            help="分数 ≤ 此值，直接判定为弱（默认40.0）。降低此值可以让更多案例有机会判定为强。"
        )
        
        strong_score_threshold = st.slider(
            "强判定分数阈值 (Strong Score Threshold)",
            min_value=30.0, max_value=70.0,
            value=strength_config.get('strong_score_threshold', 50.0),
            step=1.0, key='strength_strong_score_threshold',
            help="分数 > 此值 且 概率 ≥ 60%，判定为强（默认50.0）。降低此值可以让更多案例判定为强。"
        )
        
        strong_probability_threshold = st.slider(
            "强判定概率阈值 (Strong Probability Threshold)",
            min_value=0.40, max_value=0.80,
            value=strength_config.get('strong_probability_threshold', 0.60),
            step=0.05, key='strength_strong_probability_threshold',
            help="概率 ≥ 此值 且 分数 > 50，判定为强（默认0.60）。降低此值可以让概率稍低的案例也判定为强。"
        )
        
        st.markdown("**🧠 GAT 动态注意力 (Graph Attention Network)**")
        use_gat = st.checkbox(
            "启用 GAT 动态注意力",
            value=gat_config.get('use_gat', True),
            key='gat_use_gat',
            help="启用图注意力网络，实现局部隔离调优"
        )
        
        if use_gat:
            attention_dropout = st.slider(
                "噪声过滤 (GAT Dropout)",
                min_value=0.0, max_value=0.5,
                value=strength_config.get('attention_dropout', gat_config.get('attention_dropout', 0.29)),
                step=0.01, key='strength_attention_dropout',
                help="GAT注意力稀疏度，过滤杂气（从敏感度分析得出：0.29）"
            )
        else:
            attention_dropout = strength_config.get('attention_dropout', gat_config.get('attention_dropout', 0.29))
        
        # [V10.0] 实时旺衰概率曲线可视化
        st.markdown("**📈 旺衰概率波函数预览**")
        try:
            from ui.utils.strength_probability_visualization import plot_strength_probability_curve
            
            # 不在此处获取案例能量，因为可能还没有选择案例
            # 图表会在选择案例后自动更新（通过key触发重绘）
            probability_fig = plot_strength_probability_curve(
                energy_threshold_center=energy_threshold_center,
                phase_transition_width=phase_transition_width,
                current_case_energy=None  # 将在主界面显示时动态计算
            )
            st.plotly_chart(probability_fig, use_container_width=True, key='strength_probability_curve')
            st.caption("💡 提示：选择案例后，图表会自动标记当前案例的能量位置")
        except Exception as e:
            st.caption(f"⚠️ 可视化加载失败: {e}")

    # --- Particle Weights Calibration (P2 only) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚛️ 粒子权重校准 (Particle Weights)")
    st.sidebar.caption("调整核心十神粒子对模型的影响强度（50%-150%）。")
    
    # V16.0: Load particle weights from Controller (which reads from config/parameters.json)
    config_weights = controller.get_current_particle_weights()
    
    particle_weights = {}
    # 使用常量列表，保持原有中文标签顺序分组
    # V16.0: Slider value now comes from config file via Controller
    pw_res_col1, pw_res_col2 = st.sidebar.columns(2)
    zheng_yin_val = int(config_weights.get(consts.TEN_GODS[0], 1.0) * 100)
    particle_weights[consts.TEN_GODS[0]] = pw_res_col1.slider("正印 (Zheng Yin)", 50, 150, zheng_yin_val, step=5, key="pw_p2_zhengyin") / 100
    pian_yin_val = int(config_weights.get(consts.TEN_GODS[1], 1.0) * 100)
    particle_weights[consts.TEN_GODS[1]] = pw_res_col2.slider("偏印 (Pian Yin)", 50, 150, pian_yin_val, step=5, key="pw_p2_pianyin") / 100
    pw_cai_col1, pw_cai_col2 = st.sidebar.columns(2)
    zheng_cai_val = int(config_weights.get(consts.TEN_GODS[6], 1.0) * 100)
    particle_weights[consts.TEN_GODS[6]] = pw_cai_col1.slider("正财 (Zheng Cai)", 50, 150, zheng_cai_val, step=5, key="pw_p2_zhengcai") / 100
    pian_cai_val = int(config_weights.get(consts.TEN_GODS[7], 1.0) * 100)
    particle_weights[consts.TEN_GODS[7]] = pw_cai_col2.slider("偏财 (Pian Cai)", 50, 150, pian_cai_val, step=5, key="pw_p2_piancai") / 100
    pw_gs_col1, pw_gs_col2 = st.sidebar.columns(2)
    zheng_guan_val = int(config_weights.get(consts.TEN_GODS[8], 1.0) * 100)
    particle_weights[consts.TEN_GODS[8]] = pw_gs_col1.slider("正官 (Zheng Guan)", 50, 150, zheng_guan_val, step=5, key="pw_p2_zhengguan") / 100
    qi_sha_val = int(config_weights.get(consts.TEN_GODS[9], 1.0) * 100)
    particle_weights[consts.TEN_GODS[9]] = pw_gs_col2.slider("七杀 (Qi Sha)", 50, 150, qi_sha_val, step=5, key="pw_p2_qisha") / 100
    pw_ss_col1, pw_ss_col2 = st.sidebar.columns(2)
    shi_shen_val = int(config_weights.get(consts.TEN_GODS[4], 1.0) * 100)
    particle_weights[consts.TEN_GODS[4]] = pw_ss_col1.slider("食神 (Shi Shen)", 50, 150, shi_shen_val, step=5, key="pw_p2_shishen") / 100
    shang_guan_val = int(config_weights.get(consts.TEN_GODS[5], 1.0) * 100)
    particle_weights[consts.TEN_GODS[5]] = pw_ss_col2.slider("伤官 (Shang Guan)", 50, 150, shang_guan_val, step=5, key="pw_p2_shangguan") / 100
    pw_bj_col1, pw_bj_col2 = st.sidebar.columns(2)
    bi_jian_val = int(config_weights.get(consts.TEN_GODS[2], 1.0) * 100)
    particle_weights[consts.TEN_GODS[2]] = pw_bj_col1.slider("比肩 (Bi Jian)", 50, 150, bi_jian_val, step=5, key="pw_p2_bijian") / 100
    jie_cai_val = int(config_weights.get(consts.TEN_GODS[3], 1.0) * 100)
    particle_weights[consts.TEN_GODS[3]] = pw_bj_col2.slider("劫财 (Jie Cai)", 50, 150, jie_cai_val, step=5, key="pw_p2_jiecai") / 100
    
    # V16.0: Save button to write slider values back to config file
    if st.sidebar.button("💾 保存粒子权重到配置", type="secondary"):
        if controller._save_particle_weights_config(particle_weights):
            st.sidebar.success("✅ 粒子权重已保存到 config/parameters.json")
            st.rerun()
        else:
            st.sidebar.error("❌ 保存失败，请检查日志")

    # [V10.3] 参数来源和刷新按钮（移到最底部）
    st.sidebar.markdown("---")
    col_refresh1, col_refresh2 = st.sidebar.columns([3, 1])
    with col_refresh1:
        st.sidebar.caption("📊 参数来源: config/parameters.json")
    with col_refresh2:
        if st.sidebar.button("🔄", help="刷新参数（从配置文件重新加载）", key="refresh_params_btn"):
            # V13.2: 强制清除所有参数滑块的 session_state，确保从配置文件重新加载
            param_keys_to_clear = [
                'pg_y', 'pg_m', 'pg_d', 'pg_h',  # 宫位权重
                'sw_wang', 'sw_xiang', 'sw_xiu', 'sw_qiu', 'sw_si',  # 季节权重
                'physics_self_punishment_damping',  # 自刑惩罚
                's_rw', 's_eb', 's_sp',  # 通根、透干、自坐
            ]
            for key in param_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 清除 golden_config 缓存，强制重新加载
            if 'golden_config' in st.session_state:
                del st.session_state['golden_config']
            
            st.sidebar.success("✅ 参数已从配置文件重新加载")
            st.rerun()  # 重新渲染页面以应用新参数

    # V13.0: 已删除"应用并回测"按钮和"全局回归检查"开关（不再使用）
    
    # [V12.1] 注意：财富/感情/事业相关参数已移除
    # 这些参数属于第二层验证（财富预测），应在 wealth_verification.py 中调优
    # 量子验证页面专注于第一层验证（旺衰判定）

    # --- MAIN ENGINE SETUP ---
    # 所有算法调用都通过 controller，不再需要 engine_mode
    
    # Refresh controller input with particle weights via Facade
    user_data = controller.get_user_data()
    try:
        bazi_facade.process_and_set_inputs(
            user_data={
                "name": user_data.get('name', 'LabUser'),
                "gender": user_data.get('gender', '男'),
                "date": user_data.get('date', datetime.date(1990, 1, 1)),
                "time": user_data.get('time', 12),
                "city": user_data.get('city', city_for_controller or "Beijing"),
                "enable_solar": user_data.get('enable_solar', True),
                "longitude": user_data.get('longitude', 116.46),
            },
            geo_city=city_for_controller or "Beijing",
            era_factor=era_factor if era_factor else None,
            particle_weights=particle_weights
        )
    except Exception as e:
        st.warning(f"无法刷新 Controller 输入（粒子权重）: {e}")

    get_notification_manager().display_all()
    
    # [V10.0] 初始化QuantumLabController（如果还没有初始化）
    if 'quantum_lab_controller' not in st.session_state:
        st.session_state['quantum_lab_controller'] = QuantumLabController()
    
    quantum_controller = st.session_state['quantum_lab_controller']
    
    # === V6.0+ 热更新：从 session_state 读取并应用算法配置 ===
    # [V10.0] 使用Controller更新配置
    if 'algo_config' in st.session_state:
        quantum_controller.update_config(st.session_state['algo_config'])
        
    if 'full_algo_config' in st.session_state:
        quantum_controller.update_config(st.session_state['full_algo_config'])

    # --- UI HEADER ---
    st.title("🧪 量子验证工作台")
    st.markdown("**V12.1 旺衰判定验证系统** - 基于GraphNetworkEngine与SVM模型")
    st.caption("专注于第一层验证（旺衰判定），使用最新的V11.0 SVM模型和V10.0非线性算法")

    # --- TABS ---
    tab_phase1, tab_phase2, tab_global, tab_single = st.tabs([
        "🧪 Phase 1 验证",
        "⚡ Phase 2 动态交互",
        "🔭 批量验证", 
        "🔬 单点分析"
    ])

    # ==========================
    # TAB 0: Phase 1 验证
    # ==========================
    with tab_phase1:
        st.subheader("✅ Phase 1 基础物理层验证")
        st.caption("**V13.3 已完成** - 所有规则验证通过，基础物理层已完善")
        
        # 自动加载测试案例并运行验证
        phase1_path = os.path.join(os.path.dirname(__file__), "../../data/phase1_test_cases.json")
        phase1_data = {}
        if os.path.exists(phase1_path):
            try:
                with open(phase1_path, 'r', encoding='utf-8') as f:
                    phase1_data = json.load(f)
                st.session_state['phase1_test_cases'] = phase1_data
            except Exception as e:
                st.error(f"❌ 加载测试案例失败: {e}")
        
        if phase1_data:
            # V13.0: 构建当前配置（合并边栏滑块的值）
            from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
            current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
            if golden_config:
                deep_merge_params(current_config, golden_config)
            current_config = merge_sidebar_values_to_config(current_config)
            
            # 运行验证
            from core.phase1_auto_calibrator import Phase1AutoCalibrator
            calibrator = Phase1AutoCalibrator(current_config, phase1_data, default_config=current_config.copy())
            verification_result = calibrator.run_verification(current_config)
            
            # 显示最终结果（极简版）
            st.markdown("---")
            st.markdown("### 📊 验证结果")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                status_icon = "✅" if verification_result['group_a_passed'] else "❌"
                st.markdown(f"#### {status_icon} Group A (月令)")
                st.caption("得令 > 得生 > 泄气 > 被克")
            with col2:
                status_icon = "✅" if verification_result['group_b_passed'] else "❌"
                st.markdown(f"#### {status_icon} Group B (通根)")
                st.caption("自坐强根 > 远根 > 无根")
            with col3:
                status_icon = "✅" if verification_result['group_c_passed'] else "❌"
                st.markdown(f"#### {status_icon} Group C (宫位)")
                st.caption("日支 > 时支 > 年支")
            
            # 总体状态
            if verification_result['all_passed']:
                st.success("🎉 **Phase 1 全绿！所有规则验证通过！**")
            else:
                st.warning("⚠️ **部分规则未通过**，建议运行自动校准")
            
            # 显示关键参数（简洁版）
            st.markdown("---")
            st.markdown("### ⚙️ 关键参数")
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            with col_p1:
                st.metric("月令权重", f"{current_config.get('physics', {}).get('pillarWeights', {}).get('month', 1.2):.2f}")
            with col_p2:
                st.metric("日柱权重", f"{current_config.get('physics', {}).get('pillarWeights', {}).get('day', 1.0):.2f}")
            with col_p3:
                st.metric("自坐加成", f"{current_config.get('structure', {}).get('samePillarBonus', 3.0):.2f}")
            with col_p4:
                st.metric("通根系数", f"{current_config.get('structure', {}).get('rootingWeight', 1.2):.2f}")
        else:
            st.info("💡 测试案例文件未找到，无法运行验证")
        
        # V13.3: 已删除详细报告生成、操作按钮、自动校准等功能（Phase 1 已完成）
        # 所有详细功能代码已删除，只保留最终结果展示
    
    # ==========================
    # TAB 1: Phase 2 动态交互层验证
    # ==========================
    with tab_phase2:
        st.subheader("⚡ Phase 2: 动态生克场验证")
        st.caption("**V13.5 启动** - 验证能量交互矩阵（生克制化规则，精细合局参数）")
        
        # 导入 Phase 2 验证组按钮
        st.markdown("---")
        if st.button("📥 导入 Phase 2 验证组", type="primary", use_container_width=True):
            try:
                phase2_path = os.path.join(os.path.dirname(__file__), "../../data/phase2_test_cases.json")
                if os.path.exists(phase2_path):
                    with open(phase2_path, 'r', encoding='utf-8') as f:
                        phase2_data = json.load(f)
                    st.session_state['phase2_test_cases'] = phase2_data
                    st.success("✅ Phase 2 验证组已加载")
                    st.rerun()
                else:
                    st.error(f"❌ 未找到测试样本文件: {phase2_path}")
            except Exception as e:
                st.error(f"❌ 加载失败: {e}")
        
        # 加载并运行验证
        phase2_data = st.session_state.get('phase2_test_cases', {})
        if phase2_data:
            # V13.0: 构建当前配置（合并边栏滑块的值）
            from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
            current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
            if golden_config:
                deep_merge_params(current_config, golden_config)
            current_config = merge_sidebar_values_to_config(current_config)
            
            # 运行 Phase 2 验证
            st.markdown("---")
            st.markdown("### 📊 动态交互验证结果 (V13.6 量子热力学)")
            st.caption("**验证重点**: 观察波动的形态（标准差的变化）")
            
            # [V13.6] 创建 Phase2Verifier 并运行验证
            from core.phase2_verifier import Phase2Verifier
            verifier = Phase2Verifier(current_config)
            
            # 显示测试案例分组
            if 'group_d_generation' in phase2_data:
                st.markdown("#### 🌱 Group D: 生成规则 (Generation)")
                st.caption("**验证重点**: 强木生火 > 弱木生火，且生方（甲木）能量必须减少（generationDrain 生效）")
                for case in phase2_data['group_d_generation']:
                    with st.expander(f"**{case.get('id', 'N/A')}**: {case.get('desc', 'N/A')}", expanded=False):
                        st.code(f"八字: {' '.join(case.get('bazi', []))}")
                        st.caption(f"预期: {case.get('expected_behavior', 'N/A')}")
                        st.caption(f"预期能量比: {case.get('expected_energy_ratio', 'N/A')}")
            
            if 'group_e_control' in phase2_data:
                st.markdown("#### ⚔️ Group E: 克制规则 (Control)")
                st.caption("**验证重点**: 强水克火 > 弱水克火")
                for case in phase2_data['group_e_control']:
                    with st.expander(f"**{case.get('id', 'N/A')}**: {case.get('desc', 'N/A')}", expanded=False):
                        st.code(f"八字: {' '.join(case.get('bazi', []))}")
                        st.caption(f"预期: {case.get('expected_behavior', 'N/A')}")
                        st.caption(f"预期能量比: {case.get('expected_energy_ratio', 'N/A')}")
            
            if 'group_f_combination' in phase2_data:
                st.markdown("#### 🔗 Group F: 合化规则 (Combination) - **V13.5 精细合局**")
                st.caption("**验证重点**: 三合(2.0) > 半合(1.4) > 六合(1.3) > 拱合(1.1)，六合有bindingPenalty")
                for case in phase2_data['group_f_combination']:
                    with st.expander(f"**{case.get('id', 'N/A')}**: {case.get('desc', 'N/A')}", expanded=False):
                        st.code(f"八字: {' '.join(case.get('bazi', []))}")
                        st.caption(f"预期: {case.get('expected_behavior', 'N/A')}")
                        st.caption(f"预期能量比: {case.get('expected_energy_ratio', 'N/A')}")
                        
                        # V13.5: 显示物理模型说明
                        case_id = case.get('id', '')
                        if 'SanHe' in case_id:
                            st.info("🔬 **物理模型**: 120°相位，共振质变，能量翻倍（化气）")
                        elif 'LiuHe' in case_id:
                            st.info("🔬 **物理模型**: 磁力吸附，物理羁绊，能量提升但活性降低")
                        elif 'BanHe' in case_id:
                            st.info("🔬 **物理模型**: 不完全共振，能量中等提升")
                        elif 'ArchHarmony' in case_id:
                            st.info("🔬 **物理模型**: 缺中神，虚拱，能量微升")
            
            # 显示关键交互参数
            st.markdown("---")
            st.markdown("### ⚙️ 交互参数")
            flow_config = current_config.get('flow', {})
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.metric("生成效率 (Generation)", f"{flow_config.get('generationEfficiency', 1.2):.2f}")
            with col_i2:
                st.metric("克制影响 (Control)", f"{flow_config.get('controlImpact', 0.7):.2f}")
        else:
            st.info("💡 请点击「导入 Phase 2 验证组」加载测试案例")
    
    # ==========================
    # TAB 2: 批量验证
    # ==========================
    with tab_global:
        st.subheader("批量验证")
        st.caption("批量验证所有案例的旺衰判定准确率")
        
        # [V12.1] Phase 1 自检指标
        with st.expander("🔬 Phase 1 自检指标 (Self-Check Metrics)", expanded=False):
            st.caption("**目的**：确保参数调整有物理意义，而不是在制造噪声")
            
            # 选择5个标准案例
            standard_cases = [
                {'id': 'VAL_001', 'name': '标准身强案例', 'expected': 'Strong'},
                {'id': 'VAL_002', 'name': '标准身弱案例', 'expected': 'Weak'},
                {'id': 'VAL_003', 'name': '标准从格案例', 'expected': 'Follower'},
                {'id': 'VAL_004', 'name': '标准专旺案例', 'expected': 'Special_Strong'},
                {'id': 'VAL_005', 'name': '标准平衡案例', 'expected': 'Balanced'}
            ]
            
            if st.button("📊 计算 Phase 1 自检指标", type="secondary"):
                try:
                    # 获取当前配置
                    current_config = st.session_state.get('full_algo_config', {})
                    if not current_config:
                        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
                        current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
                    
                    from core.engine_graph import GraphNetworkEngine
                    temp_engine = GraphNetworkEngine(config=current_config)
                    
                    # 计算5个标准案例的初始能量分布标准差
                    std_devs = []
                    case_names = []
                    
                    for std_case in standard_cases:
                        # 查找对应的案例
                        found_case = None
                        for c in cases:
                            if str(c.get('id', '')) == std_case['id']:
                                found_case = c
                                break
                        
                        if not found_case:
                            continue
                        
                        # 计算初始能量
                        bazi_list = found_case.get('bazi', [])
                        day_master = found_case.get('day_master', '甲')
                        
                        if len(bazi_list) >= 4:
                            temp_engine.initialize_nodes(bazi_list, day_master)
                            initial_energies = [node.initial_energy for node in temp_engine.nodes]
                            std_dev = np.std(initial_energies)
                            std_devs.append(std_dev)
                            case_names.append(std_case['name'])
                    
                    if std_devs:
                        # 显示结果
                        col1, col2 = st.columns(2)
                        with col1:
                            avg_std = np.mean(std_devs)
                            st.metric("平均能量标准差", f"{avg_std:.2f}",
                                    help="标准差越大，能量分布越不均匀。建议范围：0.5-2.0")
                        with col2:
                            max_std = max(std_devs)
                            min_std = min(std_devs)
                            st.metric("标准差范围", f"{min_std:.2f} - {max_std:.2f}")
                        
                        # 显示详细数据
                        check_data = {
                            '案例': case_names,
                            '能量标准差': [f"{s:.2f}" for s in std_devs]
                        }
                        st.dataframe(pd.DataFrame(check_data), use_container_width=True)
                        
                        # 健康度评估
                        if avg_std < 0.3:
                            st.warning("⚠️ 能量分布过于均匀，可能无法区分强弱")
                        elif avg_std > 3.0:
                            st.warning("⚠️ 能量分布过于不均匀，可能导致极端判定")
                        else:
                            st.success("✅ Phase 1 能量分布健康")
                    else:
                        st.info("未找到标准案例，请确保 calibration_cases.json 中包含标准案例")
                        
                except Exception as e:
                    st.error(f"❌ Phase 1 自检失败: {e}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
        
        if not cases:
            st.error("No cases loaded.")
        else:
            if st.button("🚀 开始批量回测 (Start Batch Run)", type="primary"):
                results = []
                passed = 0
                total = 0
                
                progress_bar = st.progress(0)
                
                with st.spinner("Quantum Computing Batch Jobs..."):
                    for idx, c in enumerate(cases):
                        # Filter for valid ground truth
                        gt = c.get('ground_truth')
                        if not gt: continue
                        
                        total += 1
                        
                        # 1. Create Profile / Adapter
                        # Luck pillar logic: use dynamic check default or just first luck?
                        # For Wang Shuai (Base Strength), luck pillar usually doesn't affect Base Chart Strength 
                        # UNLESS we consider "Dynamic Strength" in context.
                        # Usually Ground Truth refers to NATIVE Chart Strength.
                        # So we can ignore Luck for Base Strength Assessment?
                        # Wait, V6.0 Profile includes Luck. 
                        # Let's pass "unknown" if not critical.
                        presets = c.get("dynamic_checks", [])
                        luck_p = presets[0]['luck'] if presets else "癸卯"
                        
                        # [V10.0] 使用Controller创建profile
                        profile = quantum_controller.create_profile_from_case(c, luck_p)
                        
                        # 2. Evaluate Base Strength
                        # [V10.0] 使用Controller评估旺衰
                        bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                        
                        # Catch errors
                        try:
                            # [V10.0] 使用Controller的方法
                            ws_tuple = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                            comp_str = ws_tuple[0] # e.g. "Strong"
                            comp_score = ws_tuple[1]
                        except Exception as e:
                            comp_str = "Error"
                            comp_score = 0.0
                        
                        # 3. Verify
                        target_str = gt.get('strength', 'Unknown')
                        is_match = False
                        
                        if target_str != "Unknown":
                            # V12.0: 改进匹配逻辑 - 精确匹配优先，然后处理特殊情况
                            # 标准化标签（去除空格、统一大小写）
                            target_str = target_str.strip()
                            comp_str = comp_str.strip()
                            
                            # 1. 精确匹配
                            if target_str == comp_str:
                                is_match = True
                            # 2. 处理Special_Strong vs Strong的情况
                            # 如果target是"Strong"，comp是"Special_Strong"，也算匹配（Special_Strong是Strong的子集）
                            elif target_str == "Strong" and comp_str == "Special_Strong":
                                is_match = True
                            # 3. 处理Weak vs Follower的情况
                            # 如果target是"Follower"，comp是"Follower"或"Weak"，都算匹配（Follower是极弱，可以接受Weak）
                            elif target_str == "Follower" and (comp_str == "Follower" or comp_str == "Weak"):
                                is_match = True
                            # 如果target是"Weak"，comp是"Weak"或"Follower"，都算匹配
                            elif target_str == "Weak" and (comp_str == "Weak" or comp_str == "Follower"):
                                is_match = True
                            # 4. 处理Balanced的情况
                            elif target_str == "Balanced" and comp_str == "Balanced":
                                is_match = True
                            # 5. 其他情况：如果target包含comp或comp包含target（但排除已处理的情况）
                            elif (target_str in comp_str or comp_str in target_str) and not (
                                (target_str == "Strong" and comp_str == "Special_Strong") or
                                (comp_str == "Strong" and target_str == "Special_Strong")
                            ):
                                is_match = True
                        
                        if is_match: passed += 1
                        
                        results.append({
                            "Case ID": c.get('id', idx),
                            "Name": c.get('description', ''),
                            "Target": target_str,
                            "Computed": comp_str,
                            "Score": f"{comp_score:.1f}",
                            "Result": "✅ Pass" if is_match else "❌ Fail"
                        })
                        
                        progress_bar.progress((idx + 1) / len(cases))
                
                # Report
                accuracy = (passed / total) * 100 if total > 0 else 0.0
                st.metric("综合准确率 (Global Accuracy)", f"{accuracy:.1f}%", f"{passed}/{total} Cases")
                
                # DataFrame
                st.dataframe(results, width='stretch')
                
                if accuracy < 60:
                    st.error("Low Accuracy! Tuning Required.")
                elif accuracy < 90:
                    st.warning("Moderate Accuracy. Check Failed Cases.")
                else:
                    st.success("Exclellent Fit! Ready for Deployment.")
            else:
                st.info("Click button to run batch verification on 25 cases.")
            
            # End of Tab Global Logic

    # ==========================
    # TAB 2: 单点分析
    # ==========================
    with tab_single:
        st.subheader("单点分析")
        
        # Mode Selection
        verify_mode = st.radio("数据源 (Data Source)", ["📚 预设案例 (Presets)", "✍️ 手动录入 (Manual Input)"], horizontal=True)
        
        selected_case = None
        user_year = "甲辰"
        user_luck = "癸卯"

        if verify_mode == "📚 预设案例 (Presets)":
            if not cases:
                st.error("No preset data.")
            else:
                c_sel, c_ctx = st.columns([2, 3])
                with c_sel:
                    def _fmt(i):
                        c = cases[i]
                        birth = ""
                        if c.get("birth_date"):
                            bt = c.get("birth_time", "")
                            birth = f" | {c.get('birth_date')} {bt}"
                        return f"No.{c.get('id','?')} {c.get('day_master','?')}日主 ({c.get('gender','?')}){birth}"
                    case_idx = st.selectbox("📂 选择档案", range(len(cases)), format_func=_fmt)
                    selected_case = cases[case_idx]
                
                with c_ctx:
                    presets = selected_case.get("dynamic_checks", []) or []
                    c_y, c_l = st.columns(2)
                    first_chk = presets[0] if presets else {}
                    # Prefer dynamic check year; else use derived birth year; else empty
                    derived_year = (selected_case.get("birth_date") or "")[:4]
                    def_year = first_chk.get('year') or derived_year or ""
                    def_luck = first_chk.get('luck', "")
                    user_year = c_y.text_input("流年 (Year)", value=def_year)
                    user_luck = c_l.text_input("大运 (Luck)", value=def_luck)
                    
        else: # Manual Input
            st.markdown("#### 📝 新案例录入")
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            in_year = mc1.number_input("年 (Year)", 1900, 2100, 1991) # Example: 1991 (Wei Month case?)
            in_month = mc2.number_input("月 (Month)", 1, 12, 7) # Wei Month approx July
            in_day = mc3.number_input("日 (Day)", 1, 31, 15)
            in_hour = mc4.number_input("时 (Hour)", 0, 23, 12)
            in_gender = mc5.selectbox("性别", ["男", "女"])
            
            # Ground Truth
            st.markdown("#### 🎯 真值设定 (Ground Truth)")
            gt1, gt2 = st.columns(2)
            gt_strength = gt1.selectbox("真实身强", ["Unknown", "Strong", "Weak", "Follower"], index=2) # Default Weak
            gt_fav = gt2.multiselect("真实喜用", ["Wood", "Fire", "Earth", "Metal", "Water"], default=[])
            
            # Run Calculation to form Case
            if st.button("🚀 载入并计算 (Load & Run)", type="primary"):
                with st.spinner("Quantum Computing... Note: Manual Mode calculates chart on the fly."):
                    req = {'birth_year': in_year, 'birth_month': in_month, 'birth_day': in_day, 'birth_hour': in_hour, 'gender': in_gender}
                    # [V10.0] 使用Controller计算排盘
                    res = quantum_controller.calculate_chart(req)
                    
                    # Convert to Case Format
                    bazi_strs = [f"{p[0]}{p[1]}" for p in res['bazi']]
                    
                    manual_case = {
                        'id': 'MANUAL',
                        'gender': in_gender,
                        'bazi': bazi_strs, # [Year, Month, Day, Hour]
                        'day_master': res['bazi'][2][0],
                        'dynamic_checks': [],
                        # Custom fields for verification
                        'ground_truth': {
                            'strength': gt_strength,
                            'favorable': gt_fav
                        },
                        'computed_result': res # Store for comparison
                    }
                    st.session_state['manual_case'] = manual_case
                    st.rerun()
            
            if 'manual_case' in st.session_state:
                selected_case = st.session_state['manual_case']
                st.success(f"✅ Loaded: {selected_case['bazi']} | DM: {selected_case['day_master']}")
                
                # Comparison
                if 'computed_result' in selected_case and 'ground_truth' in selected_case:
                    cr = selected_case['computed_result']
                    gt = selected_case['ground_truth']
                    
                    # Determine Computed Strength String
                    # cr['wang_shuai'] is (str, score), e.g. ('Weak', 0.45)
                    comp_str = cr['wang_shuai'][0]
                    comp_score = cr['energy_score']
                    
                    # Display Feedback
                    st.divider()
                    col_res, col_verdict = st.columns([3, 2])
                    
                    with col_res:
                        st.metric("算法判定 (Computed)", f"{comp_str} ({comp_score:.1f})")
                        st.write(f"喜用神: {cr['favorable_elements']}")
                        
                    with col_verdict:
                        is_match = (gt['strength'] == "Unknown") or (gt['strength'] in comp_str) or (comp_str in gt['strength'])
                        # Loose matching "Strong" vs "Strong"
                        
                        if is_match:
                            st.success(f"MATCH! ✅\nTarget: {gt['strength']}")
                        else:
                            st.error(f"MISMATCH ❌\nTarget: {gt['strength']}")
                            
                        # Favorable overlap?
                        comp_fav_set = set(cr['favorable_elements'])
                        gt_fav_set = set(gt['favorable'])
                        if gt_fav_set:
                            overlap = comp_fav_set.intersection(gt_fav_set)
                            if overlap:
                                st.caption(f"✅ Favorable Overlap: {overlap}")
                            else:
                                st.caption(f"⚠️ Favorable Divergence!")
                
                st.divider()

        if selected_case:
            # === Trinity V6.0: Single Microscope ===
            # Continue with existing logic using selected_case
            
                # [V10.0] MCP上下文注入：注入GEO、ERA、大运、流年等信息
            try:
                import logging
                _logger = logging.getLogger(__name__)
                
                # 解析用户输入的年份（如果是干支，转换为年份；如果是数字，直接使用）
                selected_year_int = None
                if user_year and user_year.isdigit():
                    selected_year_int = int(user_year)
                elif user_year:
                    # 如果是干支格式，暂时无法反向转换，使用默认值
                    # 这里可以改进，但暂时保持兼容性
                    pass
                
                # [V10.0] 使用Controller注入MCP上下文
                case_with_context = quantum_controller.inject_mcp_context(selected_case, selected_year_int)
                
                # [V10.0] 使用Controller获取大运（优先级：MCP上下文 -> timeline -> VirtualBaziProfile自动反推）
                if not user_luck or user_luck == "" or user_luck == "未知":
                    user_luck = quantum_controller.get_luck_pillar(selected_case, selected_year_int, mcp_context=case_with_context)
                    if user_luck and user_luck != "未知":
                        st.info(f"💡 大运已获取: {user_luck} (年份: {selected_year_int})")
                
                # [V10.0] 使用Controller计算流年干支
                if selected_year_int:
                    user_year = quantum_controller.calculate_year_pillar(selected_year_int)
                
                # 使用上下文中的GEO和ERA信息
                geo_city = case_with_context.get('geo_city', 'Unknown')
                geo_latitude = case_with_context.get('geo_latitude', 0.0)
                geo_longitude = case_with_context.get('geo_longitude', 0.0)
                era_element = case_with_context.get('era_element', 'Fire')
                
                _logger.debug(f"📍 MCP上下文: GEO={geo_city}, ERA={era_element}, 大运={user_luck}, 流年={user_year}")
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"⚠️ MCP上下文注入失败，使用默认值: {e}")
                geo_city = selected_case.get('geo_city', 'Unknown')
                geo_latitude = selected_case.get('geo_latitude', 0.0)
                geo_longitude = selected_case.get('geo_longitude', 0.0)
                era_element = 'Fire'
            
            st.info(f"Analyzing Case: {selected_case['bazi']}")
            
            # [V12.1] Phase 1 可视化：显示初始能量 H^(0) 分布
            with st.expander("📊 Phase 1: 初始能量场可视化 (H^(0) Distribution)", expanded=True):
                st.caption("**实时显示**：调整Phase 1参数后，查看初始能量分布的变化")
                
                try:
                    # 获取当前配置（优先使用session_state中的配置）
                    current_config = st.session_state.get('full_algo_config', {})
                    if not current_config:
                        # 如果没有配置，使用默认配置
                        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
                        current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
                    
                    # 创建临时引擎计算初始能量
                    from core.engine_graph import GraphNetworkEngine
                    temp_engine = GraphNetworkEngine(config=current_config)
                    
                    # 准备数据
                    bazi_list = [
                        selected_case['bazi'][0] if len(selected_case['bazi']) > 0 else '',
                        selected_case['bazi'][1] if len(selected_case['bazi']) > 1 else '',
                        selected_case['bazi'][2] if len(selected_case['bazi']) > 2 else '',
                        selected_case['bazi'][3] if len(selected_case['bazi']) > 3 else ''
                    ]
                    day_master = selected_case.get('day_master', '甲')
                    
                    # 初始化节点（只计算初始能量，不传播）
                    temp_engine.initialize_nodes(bazi_list, day_master, luck_pillar=user_luck, year_pillar=user_year)
                    
                    # 提取初始能量数据
                    node_labels = []
                    initial_energies = []
                    node_types = []
                    pillar_names = []
                    
                    for node in temp_engine.nodes:
                        label = f"{node.char}"
                        if node.pillar_idx < 4:  # 原局节点
                            pillar_name = ['年', '月', '日', '时'][node.pillar_idx]
                            label = f"{pillar_name}{node.char}"
                        elif node.pillar_idx == 4:  # 大运节点
                            label = f"运{node.char}"
                        elif node.pillar_idx == 5:  # 流年节点
                            label = f"岁{node.char}"
                        
                        node_labels.append(label)
                        initial_energies.append(node.initial_energy)
                        node_types.append(node.node_type)
                        pillar_names.append(node.pillar_name if hasattr(node, 'pillar_name') else '')
                    
                    # 创建柱状图（使用全局导入的 go）
                    fig_h0 = go.Figure()
                    
                    # 按节点类型分组着色
                    colors = []
                    for i, node_type in enumerate(node_types):
                        if node_type == 'stem':
                            colors.append('#4A90E2')  # 蓝色：天干
                        else:
                            colors.append('#E24A4A')  # 红色：地支
                    
                    fig_h0.add_trace(go.Bar(
                        x=node_labels,
                        y=initial_energies,
                        marker_color=colors,
                        text=[f"{e:.2f}" for e in initial_energies],
                        textposition='outside',
                        name='初始能量 H^(0)'
                    ))
                    
                    # 标记月令节点（最重要）
                    month_idx = None
                    for i, (label, pname) in enumerate(zip(node_labels, pillar_names)):
                        if pname == 'month' and node_types[i] == 'branch':
                            month_idx = i
                            break
                    
                    if month_idx is not None:
                        fig_h0.add_annotation(
                            x=node_labels[month_idx],
                            y=initial_energies[month_idx],
                            text="⭐ 月令",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor='#FFD700',
                            font=dict(color='#FFD700', size=12, family='Arial Black')
                        )
                    
                    fig_h0.update_layout(
                        title="Phase 1: 初始能量分布 H^(0)",
                        xaxis_title="节点",
                        yaxis_title="初始能量",
                        height=400,
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0.05)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig_h0, use_container_width=True)
                    
                    # 显示统计信息
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("总初始能量", f"{sum(initial_energies):.2f}")
                    with col_stat2:
                        max_idx = initial_energies.index(max(initial_energies))
                        st.metric("最大能量节点", f"{node_labels[max_idx]} ({max(initial_energies):.2f})")
                    with col_stat3:
                        std_dev = np.std(initial_energies)
                        st.metric("能量标准差", f"{std_dev:.2f}", 
                                help="标准差越大，能量分布越不均匀")
                    
                    st.caption("💡 **调优提示**：调整月令权重后，观察月令节点的初始能量是否真的'一家独大'")
                    
                except Exception as e:
                    st.warning(f"⚠️ Phase 1 可视化失败: {e}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
            
            # [V10.0] 使用Controller创建profile和计算
            current_mcp_context = case_with_context if 'case_with_context' in locals() else {}
            profile = quantum_controller.create_profile_from_case(selected_case, user_luck, mcp_context=current_mcp_context)
            
            # [V10.0] 使用Controller计算年份上下文
            try:
                ctx = quantum_controller.calculate_year_context(profile, selected_year_int or 2024)
                
                # [V10.0] 准备数据并调用Controller计算能量
                b_date = getattr(profile, 'birth_date', None)
                birth_info_mock = {
                    'year': b_date.year,
                    'month': b_date.month,
                    'day': b_date.day,
                    'hour': getattr(b_date, 'hour', 12),
                    'gender': profile.gender
                } if b_date else {
                    'year': 2000, 'month': 1, 'day': 1, 'hour': 12, 'gender': profile.gender
                }
                
                bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                wang_shuai_str = "身中和"
                try:
                    ws, _ = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                    wang_shuai_str = "身旺" if "Strong" in ws else "身弱"
                except: pass

                case_data_mock = {
                    'id': selected_case.get('id', 999), 
                    'gender': selected_case.get('gender', '男'),
                    'day_master': profile.day_master,
                    'wang_shuai': wang_shuai_str,
                    'bazi': bazi_list,
                    'birth_info': birth_info_mock,
                    'city': geo_city,
                    'geo_latitude': geo_latitude,
                    'geo_longitude': geo_longitude
                }
                
                dyn_ctx_mock = {
                    'year': user_year,
                    'dayun': user_luck,
                    'luck': user_luck,
                    'era_element': era_element
                }
                
                # [V10.0] 使用Controller计算能量（不再直接调用engine）
                detailed_res = quantum_controller.calculate_energy(case_data_mock, dyn_ctx_mock)
                
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"❌ 计算失败: {e}", exc_info=True)
                st.error(f"计算失败: {e}")
                detailed_res = {}
            
            
            # [V10.0] Map to format compatible with UI (只保留旺衰相关，删除财富/情感/事业)
            pred_res = {
                'desc': ctx.narrative_prompt if 'ctx' in locals() else '', # Use the rich prompt
                'pillar_energies': detailed_res.get('pillar_energies', [0]*8),
                'narrative_events': detailed_res.get('narrative_events', [])
            }
            
            # --- Rendering Bazi Chart ---
            pe = pred_res.get('pillar_energies', [0]*8)
            bazi = selected_case['bazi'] # [Year, Month, Day, Hour]
            def split_sb(pillar): return (pillar[0], pillar[1]) if pillar and len(pillar)>1 else ("?","?")
            
            y_s, y_b = split_sb(bazi[0])
            m_s, m_b = split_sb(bazi[1])
            d_s, d_b = split_sb(bazi[2])
            h_s, h_b = split_sb(bazi[3])
            l_s, l_b = split_sb(user_luck)
            n_s, n_b = split_sb(user_year)

            # === GROUND TRUTH VERIFICATION ===
            # [V10.0] 注意：只保留旺衰判定验证，删除财富、情感、事业等宏观指标
            gt = selected_case.get('ground_truth')
            
            if gt:
                # [V10.0] 旺衰概率波函数可视化（可选显示）
                # 添加折叠选项，让用户可以选择是否显示
                with st.expander("📈 旺衰概率波函数 (当前案例能量位置)", expanded=False):
                    st.caption("""
                    **功能说明**：
                    - 这是一个Sigmoid概率曲线，展示日主能量占比与身强概率的关系
                    - X轴：日主能量占比（0-10，表示日主能量/总能量的比例）
                    - Y轴：身强概率（0%-100%）
                    - 红色星标：当前案例的能量位置
                    - 橙色虚线：临界点（相变阈值）
                    - 灰色虚线：50%概率线（身强/身弱分界线）
                    
                    **用途**：帮助理解当前案例在能量空间中的位置，以及判定为身强的概率。
                    """)
                    
                    try:
                        from ui.utils.strength_probability_visualization import plot_strength_probability_curve
                        
                        # 获取当前案例的能量值（直接计算，不依赖ws变量）
                        current_case_energy_value = None
                        try:
                            # [V10.0] 使用Controller评估旺衰，获取详细结果
                            ws_tuple = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                            if isinstance(ws_tuple, tuple) and len(ws_tuple) >= 2:
                                # 方法1: 从引擎直接获取能量占比（更准确）
                                engine = quantum_controller.engine
                                if hasattr(engine, 'nodes') and engine.nodes:
                                    # 重新初始化引擎以确保能量值是最新的
                                    engine.initialize_nodes(bazi_list, profile.day_master)
                                    engine.build_adjacency_matrix()
                                    engine.propagate(max_iterations=10)
                                    
                                    # 计算能量占比
                                    total_energy = 0.0
                                    self_team_energy = 0.0
                                    dm_element = engine.STEM_ELEMENTS.get(profile.day_master, 'earth')
                                    
                                    for node in engine.nodes:
                                        node_energy = node.current_energy
                                        total_energy += node_energy
                                        if node.element == dm_element:
                                            self_team_energy += node_energy
                                    
                                    # 能量占比 = self_team_energy / total_energy
                                    # 映射到0-10范围（与概率波函数的energy_range一致）
                                    if total_energy > 0:
                                        energy_ratio = self_team_energy / total_energy
                                        # 映射到0-10范围（概率波函数使用0-10范围）
                                        current_case_energy_value = energy_ratio * 10.0
                                    else:
                                        # 如果总能量为0，使用strength_score作为后备
                                        strength_score = ws_tuple[1]
                                        current_case_energy_value = (strength_score / 100.0) * 10.0
                                else:
                                    # 后备方法：使用strength_score估算
                                    strength_score = ws_tuple[1]  # 0-100
                                    current_case_energy_value = (strength_score / 100.0) * 10.0
                        except Exception as e:
                            import logging
                            _logger = logging.getLogger(__name__)
                            _logger.warning(f"⚠️ 计算当前案例能量值失败: {e}", exc_info=True)
                            current_case_energy_value = None
                        
                        # 从session_state获取当前参数
                        energy_threshold_center = st.session_state.get('strength_energy_threshold', 2.89)
                        phase_transition_width = st.session_state.get('strength_phase_width', 10.0)
                        
                        # 显示当前案例的能量值
                        if current_case_energy_value is not None:
                            current_prob = 1.0 / (1.0 + np.exp(-(10.0 / phase_transition_width) * (current_case_energy_value - energy_threshold_center)))
                            
                            # 计算旺衰分数（0-100分）
                            strength_score = current_case_energy_value * 10.0
                            
                            # 判定逻辑说明
                            if strength_score <= 40.0:
                                judgment_reason = "⚠️ 分数≤40分，判定为弱（即使概率高）"
                                judgment_color = "🔴"
                            elif strength_score > 50.0 and current_prob >= 0.60:
                                judgment_reason = "✅ 分数>50分且概率≥60%，判定为强"
                                judgment_color = "🟢"
                            elif strength_score <= 50.0:
                                judgment_reason = "⚠️ 分数≤50分，判定为弱"
                                judgment_color = "🔴"
                            else:
                                judgment_reason = "⚪ 中间状态，判定为平衡"
                                judgment_color = "🟡"
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("能量占比", f"{current_case_energy_value:.2f}", "0-10范围")
                            with col2:
                                st.metric("旺衰分数", f"{strength_score:.1f}", "0-100分")
                            with col3:
                                st.metric("身强概率", f"{current_prob:.1%}", "Sigmoid计算")
                            with col4:
                                st.metric("临界点", f"{energy_threshold_center:.2f}", f"带宽: {phase_transition_width:.1f}")
                            
                            # 显示判定逻辑说明
                            st.info(f"{judgment_color} **判定逻辑**: {judgment_reason}")
                            st.caption("💡 **说明**: 最终判定优先考虑旺衰分数（0-100分），而不是身强概率。只有当分数>50分且概率≥60%时，才判定为强。")
                        
                        probability_fig = plot_strength_probability_curve(
                            energy_threshold_center=energy_threshold_center,
                            phase_transition_width=phase_transition_width,
                            current_case_energy=current_case_energy_value
                        )
                        st.plotly_chart(probability_fig, use_container_width=True, key='case_strength_probability_curve')
                        if current_case_energy_value is None:
                            st.caption("💡 提示：当前案例能量值未计算，图表中未显示标记点")
                    except Exception as e:
                        st.caption(f"⚠️ 概率曲线可视化失败: {e}")
                        import traceback
                        with st.expander("查看错误详情"):
                            st.code(traceback.format_exc())
                
                # Strength Verification
                if 'strength' in gt:
                    st.markdown("---")
                    st.markdown("#### 🧬 旺衰判定 (Strength Judgment)")
                    
                    # Computed Strength
                    comp_ws_raw = ws if 'ws' in locals() else "Unknown"
                    
                    # Match Logic
                    is_match = False
                    if gt['strength'] != "Unknown":
                        is_match = (gt['strength'] in comp_ws_raw) or (comp_ws_raw in gt['strength'])
                        if "Follower" in gt['strength'] and "Follower" in comp_ws_raw: 
                            is_match = True
                    
                    c_ver, c_det = st.columns([1, 3])
                    with c_ver:
                        if is_match:
                            st.success(f"MATCH ✅\n{comp_ws_raw}")
                        else:
                            st.error(f"MISMATCH ❌\nGot: {comp_ws_raw}")
                            
                    with c_det:
                        st.caption(f"Target: **{gt.get('strength', '?')}** | Note: {gt.get('note', '')}")
                        if 'favorable' in gt:
                            st.caption(f"Target Favorable: {gt['favorable']}")

            st.markdown(f"""
            <style>
                .bazi-box {{ background-color: #1E1E1E; padding: 15px; border-radius: 8px; text-align: center; font-family: 'Courier New'; }}
                .stem {{ font-size: 1.8em; font-weight: bold; color: #FFF; }}
                .branch {{ font-size: 1.8em; font-weight: bold; color: #DDD; }}
                .day-master {{ color: #FF4500 !important; }}
                .dynamic {{ color: #00BFFF !important; }}
                .dynamic-year {{ color: #FF69B4 !important; }}
                .energy-val {{ font-size: 0.5em; color: #4CAF50; }}
            </style>
            <div class="bazi-box">
                <table style="width:100%; text-align:center;">
                    <tr style="color:#888;"><td>年</td><td>月</td><td>日</td><td>时</td><td width="20"></td><td>运</td><td>岁</td></tr>
                    <tr>
                        <td class="stem">{y_s}<div class="energy-val">{pe[0]}</div></td>
                        <td class="stem">{m_s}<div class="energy-val">{pe[2]}</div></td>
                        <td class="stem day-master">{d_s}<div class="energy-val">{pe[4]}</div></td>
                        <td class="stem">{h_s}<div class="energy-val">{pe[6]}</div></td>
                        <td></td>
                        <td class="stem dynamic">{l_s}</td>
                        <td class="stem dynamic-year">{n_s}</td>
                    </tr>
                    <tr>
                        <td class="branch">{y_b}<div class="energy-val">{pe[1]}</div></td>
                        <td class="branch">{m_b}<div class="energy-val">{pe[3]}</div></td>
                        <td class="branch day-master">{d_b}<div class="energy-val">{pe[5]}</div></td>
                        <td class="branch">{h_b}<div class="energy-val">{pe[7]}</div></td>
                        <td></td>
                        <td class="branch dynamic">{l_b}</td>
                        <td class="branch dynamic-year">{n_b}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # --- Results ---
            # [V10.0] 只显示旺衰相关结果，删除财富/情感/事业等宏观指标
            st.markdown("#### 结果分析")
            if pred_res.get('desc'):
                st.info(f"AI 判词: {pred_res['desc']}")

            # Narrative Cards (New in V2.9)
            narrative_events = pred_res.get('narrative_events', [])
            if narrative_events:
                st.markdown("#### 📜 核心叙事 (Narrative Events)")
                nc1, nc2 = st.columns(2)
                for i, event in enumerate(narrative_events):
                    with nc1 if i % 2 == 0 else nc2:
                        render_narrative_card(event)

            # Timeline
            st.divider()
            with st.expander("⏳ 12年运势模拟 (Timeline Simulation)"):
                # [V10.0] 使用Controller，不再直接创建engine
                # 如果需要更新配置，使用controller.update_config()
                
                years = range(2024, 2036)
                sim_data = []
                
                for y in years:
                    gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"][(y - 2024) % 10]
                    zhi = ["辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯"][(y - 2024) % 12]
                    sim_year_pillar = f"{gan}{zhi}"
                    
                    # Prepare Case Data for Calculate Energy
                    b_date = getattr(profile, 'birth_date', None)
                    birth_info_sim = {
                        'year': b_date.year, 'month': b_date.month, 'day': b_date.day,
                        'hour': getattr(b_date, 'hour', 12), 'gender': profile.gender
                    } if b_date else { 'year': 2000, 'month': 1, 'day': 1, 'hour': 12, 'gender': profile.gender }
                    
                    bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                    
                    # [V10.0] Estimate Wang Shuai for simulation (使用Controller)
                    try:
                        ws_sim, _ = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                        ws_str_sim = "身旺" if "Strong" in ws_sim else "身弱"
                    except:
                        ws_str_sim = "身中和"

                    case_data_sim = {
                        'id': selected_case.get('id', 999), 
                        'gender': selected_case.get('gender', '男'),
                        'day_master': profile.day_master,
                        'wang_shuai': ws_str_sim,
                        'bazi': bazi_list,
                        'birth_info': birth_info_sim,
                        # Pass physics sources if available? 
                        # Ideally flux engine runs inside calculate_energy if missing
                    }
                    
                    dyn_ctx_sim = {
                        'year': sim_year_pillar,
                        'dayun': user_luck, # Static luck for Lab
                        'luck': user_luck
                    }
                    
                    # [V10.0] 使用Controller计算能量（不再直接调用engine）
                    det_res = quantum_controller.calculate_energy(case_data_sim, dyn_ctx_sim)

                    # [V10.0] 只保留旺衰相关数据，删除财富/情感/事业
                    sim_data.append({
                        "year": y,
                        "desc": det_res.get('desc', '')
                    })
                
                # [V10.0] 删除财富/情感/事业的时间线图表（这些属于第二层验证）
                # 如果将来需要显示旺衰趋势，可以添加strength_score的时间线
                if sim_data:
                    st.info(f"已计算 {len(sim_data)} 年的数据（财富/情感/事业趋势图表已移除，这些属于第二层验证）")

            # === V33.0: Engine Comparison (引擎对比) ===
            if 'graph_data' in detailed_res:
                st.divider()
            
            # === V9.6: GEO 能量轨迹对比 (GEO Comparison) ===
            st.divider()
            st.markdown("### 🌍 GEO 能量轨迹对比 (GEO Energy Trajectory Comparison)")
            st.caption("对比基线 (Baseline) 与 GEO 修正后的能量轨迹")
            
            # V9.6: Use city from sidebar if available, otherwise provide selection in main area
            # Check if sidebar city is set and valid
            sidebar_city = st.session_state.get('p2_sidebar_city', 'Unknown')
            
            if sidebar_city and sidebar_city.lower() not in ['unknown', 'none', '']:
                # Use sidebar city selection
                comparison_city = sidebar_city
                st.info(f"📍 使用侧边栏选择的城市: **{comparison_city}** (可在侧边栏「时空修正」面板中修改)")
            else:
                # Fallback: Provide city selection in main area
                def load_geo_cities():
                    """Load available cities from geo_coefficients.json"""
                    geo_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
                    try:
                        with open(geo_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cities = list(data.get("cities", {}).keys())
                            return ["None"] + sorted(cities) if cities else ["None", "Beijing", "Shanghai", "Singapore"]
                    except:
                        return ["None", "Beijing", "Shanghai", "Singapore", "Harbin", "Guangzhou", "Sydney"]
                
                geo_cities = load_geo_cities()
                comparison_city = st.selectbox(
                    "🌍 选择 GEO 对比城市 (Select City for GEO Comparison)",
                    geo_cities,
                    index=0,
                    help="选择一个城市以查看 GEO 修正后的能量轨迹与基线的对比（或使用侧边栏「时空修正」面板中的城市选择）"
                )
                
                # Convert "None" to None for controller
                if comparison_city == "None":
                    comparison_city = None
            
            # Check if we have a valid case and city for comparison
            if selected_case and comparison_city and comparison_city.lower() not in ['unknown', 'none', '']:
                # Ensure controller has user input set (needed for get_geo_comparison)
                # We need to set user input from selected_case
                try:
                    # Try to derive birth info from case
                    # For preset cases, we might not have exact birth date
                    # Use a default date if needed
                    from datetime import date
                    default_date = date(2000, 1, 1)
                    default_gender = selected_case.get('gender', '男')
                    
                    # Set controller input (minimal required fields)
                    controller.set_user_input(
                        name=selected_case.get('description', 'Test Case'),
                        gender=default_gender,
                        date_obj=default_date,
                        time_int=12,
                        city=comparison_city,
                        enable_solar=True,
                        longitude=116.46  # Default Beijing longitude
                    )
                    
                    st.subheader(f"📊 GEO 能量轨迹对比 ({comparison_city} vs. Baseline)")
                    
                    # Get comparison data
                    start_year_geo = 2024  # Default start year
                    duration_geo = 12     # Default duration
                    
                    with st.spinner(f"正在计算 {comparison_city} 的 GEO 修正轨迹..."):
                        comparison_df, geo_modifiers = controller.get_geo_comparison(
                            city=comparison_city,
                            start_year=start_year_geo,
                            duration=duration_geo
                        )
                    
                    if not comparison_df.empty:
                        # Display GEO modifiers
                        if geo_modifiers:
                            st.markdown("#### 🌍 GEO 修正系数")
                            modifier_display = {k: v for k, v in geo_modifiers.items()
                                              if k not in ['desc'] and isinstance(v, (int, float))}
                            if modifier_display:
                                st.json(modifier_display)
                            if geo_modifiers.get('desc'):
                                st.caption(f"📍 {geo_modifiers.get('desc')}")
                        
                        # [V10.0] 删除财富/情感/事业的GEO轨迹对比（这些属于第二层验证）
                        # 如果将来需要显示旺衰的GEO轨迹，可以添加strength_score的对比
                        st.info("⚠️ GEO能量轨迹对比图表已移除。财富/情感/事业等宏观指标属于第二层验证，不应在此页面显示。")
                        
                        # Display data table (保留数据表供参考)
                        with st.expander("📋 详细数据表 (Detailed Data Table)"):
                            st.dataframe(comparison_df, width='stretch')
                    else:
                        st.warning(f"⚠️ 无法生成 {comparison_city} 的对比数据。请检查 Controller 配置。")
                        
                except Exception as e:
                    st.error(f"❌ 轨迹计算错误: {e}")
                    st.exception(e)
            elif selected_case:
                st.info("请选择一个城市以生成 GEO 能量轨迹对比图。")
            else:
                st.info("请先选择一个案例以进行 GEO 对比分析。")
    

if __name__ == "__main__":
    render()
