import streamlit as st
import copy
import os
import json
from datetime import datetime
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from utils.constants_manager import get_constants
from core.models.config_model import ConfigModel

# =================================================================
# 量子真言调优面板 (Quantum Mantra Tuning Panel) - V10.0
# =================================================================

def deep_merge_params(target, source):
    """
    深度合并参数配置：source 字典的内容会递归覆盖 target 字典。
    """
    if not source:
        return
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge_params(target[key], value)
        else:
            target[key] = value

def 初始化界面状态(配置数据, 强制=False):
    """
    将 JSON 配置数据同步到 Streamlit 的 session_state 中。
    支持手动调整与文件的双向平衡。
    """
    # 物理参数 (Physics)
    物理 = 配置数据.get('physics', {})
    宫位 = 物理.get('pillarWeights', {})
    
    参数映射 = {
        'pg_y': 宫位.get('year', 0.7),
        'pg_m': 宫位.get('month', 1.42),
        'pg_d': 宫位.get('day', 1.35),
        'pg_h': 宫位.get('hour', 0.77),
        'physics_self_punishment_damping': 物理.get('self_punishment_damping', 0.2),
    }
    
    # 季节权重 (Season Weights)
    季节 = 物理.get('seasonWeights', {})
    参数映射.update({
        'sw_wang': 季节.get('wang', 1.2),
        'sw_xiang': 季节.get('xiang', 1.0),
        'sw_xiu': 季节.get('xiu', 0.9),
        'sw_qiu': 季节.get('qiu', 0.6),
        'sw_si': 季节.get('si', 0.45),
    })
    
    # 藏干比例 (Hidden Stem Ratios)
    藏干 = 物理.get('hiddenStemRatios', {})
    参数映射.update({
        'hs_main': 藏干.get('main', 0.6),
        'hs_mid': 藏干.get('middle', 0.3),
        'hs_rem': 藏干.get('remnant', 0.1),
    })
    
    # 结构 (Structure)
    结构 = 配置数据.get('structure', {})
    参数映射.update({
        's_rw': 结构.get('rootingWeight', 1.0),
        's_eb': 结构.get('exposedBoost', 1.5),
        's_sp': 结构.get('samePillarBonus', 1.5),
    })
    
    # 交互 (Interactions)
    交互 = 配置数据.get('interactions', {})
    天干合 = 交互.get('stemFiveCombination', {})
    事件 = 交互.get('branchEvents', {})
    参数映射.update({
        'p2_combine_threshold': 天干合.get('threshold', 1.5),
        'p2_combine_bonus': 天干合.get('bonus', 1.5),
        'p2_combine_penalty': 天干合.get('penalty', 0.5),
        'p2_jealousy': 天干合.get('jealousyDamping', 0.3),
        'p2_clash_damping': 事件.get('clashDamping', 0.4),
        # 墓库 (Vault) - V11.0
        'p2_vault_thresh': 交互.get('vault', {}).get('threshold', 3.5),
        'p2_vault_sealed': 交互.get('vault', {}).get('sealedDamping', 0.4),
        'p2_vault_open': 交互.get('vault', {}).get('openBonus', 1.8),
        'p2_vault_break': 交互.get('vault', {}).get('breakPenalty', 0.5),
    })
    
    # 时空背景 (Spacetime) - V11.0
    时空 = 配置数据.get('spacetime', {})
    参数映射.update({
        'st_luck_w': 时空.get('luckPillarWeight', 1.5),
        'st_annual_w': 时空.get('annualPillarWeight', 0.5),
        'st_geo_heat': 时空.get('geo', {}).get('latitudeHeat', 0.08),
        'st_era_bonus': 时空.get('era', {}).get('eraBonus', 0.25),
    })
    
    # 合局 (Harmony)
    参数映射.update({
        'p2_three_harmony_bonus': 事件.get('threeHarmony', {}).get('bonus', 2.0),
        'p2_half_harmony_bonus': 事件.get('halfHarmony', {}).get('bonus', 1.4),
        'p2_arch_harmony_bonus': 事件.get('archHarmony', {}).get('bonus', 1.1),
        'p2_six_harmony_bonus': 事件.get('sixHarmony', {}).get('bonus', 1.3),
        'p2_six_harmony_binding': 事件.get('sixHarmony', {}).get('bindingPenalty', 0.2),
        'p2_three_meeting_bonus': 事件.get('threeMeeting', {}).get('bonus', 2.5),
    })
    
    # 流转与相变 (Flow & Phase Change)
    流转 = 配置数据.get('flow', {})
    相变 = 流转.get('phaseChange', {})
    参数映射.update({
        'f_ri_b': 流转.get('resourceImpedance', {}).get('base', 0.3),
        'f_ri_wp': 流转.get('resourceImpedance', {}).get('weaknessPenalty', 0.5),
        'f_ov_mdr': 流转.get('outputViscosity', {}).get('maxDrainRate', 0.6),
        'f_ov_df': 流转.get('outputViscosity', {}).get('drainFriction', 0.2),
        'p2_gen_drain': 流转.get('generationDrain', 0.3),
        'p2_ctrl_imp': 流转.get('controlImpact', 0.5),
        'f_damp_fac': 流转.get('dampingFactor', 0.1),
        'pc_scorched': 相变.get('scorchedEarthDamping', 0.15),
        'pc_frozen': 相变.get('frozenWaterDamping', 0.3),
        # V12.1 波动力学 (Wave Physics)
        'wp_clash_phase': 事件.get('clashPhase', 2.618),
        'wp_clash_entropy': 事件.get('clashEntropy', 0.6),
        'wp_punish_phase': 事件.get('punishPhase', 2.513),
        'wp_punish_entropy': 事件.get('punishEntropy', 0.7),
        'wp_resonance_q': 事件.get('resonanceQ', 1.5),
        'wp_harm_damping': 事件.get('harmDamping', 0.2),
        # V12.2 控制论 (Cybernetics)
        'fb_inv_threshold': 流转.get('feedback', {}).get('inverseControlThreshold', 4.0),
        'fb_inv_recoil': 流转.get('feedback', {}).get('inverseRecoilMultiplier', 2.0),
        'fb_era_shield': 流转.get('feedback', {}).get('eraShieldingFactor', 0.5),
        'ys_resonance': 流转.get('yongshen', {}).get('resonanceBoost', 1.2),
    })
    
    # 旺衰与 GAT (Strength & GAT)
    旺衰 = 配置数据.get('strength', {})
    参数映射.update({
        'strength_energy_threshold': 旺衰.get('energy_threshold_center', 4.16),
        'strength_phase_width': 旺衰.get('phase_transition_width', 10.0),
        'gat_use_gat': 配置数据.get('gat', {}).get('use_gat', True),
        'strength_attention_dropout': 配置数据.get('gat', {}).get('attention_dropout', 0.29),
    })

    # 应用到 session_state (只有强制刷新或键不存在时才覆盖)
    for k, v in 参数映射.items():
        if 强制 or k not in st.session_state:
            st.session_state[k] = v
            
    # 十神权重 (Particle Weights)
    权重组 = 配置数据.get('particleWeights', {})
    consts = get_constants()
    for 神 in consts.TEN_GODS:
        键 = f"pw_p2_{神}"
        if 强制 or 键 not in st.session_state:
            默认值 = int(权重组.get(神, 1.0) * 100)
            st.session_state[键] = 默认值

def merge_sidebar_values_to_config(config):
    """
    将侧边栏界面状态的值合并回配置对象中，用于计算和持久化。
    """
    # 物理参数
    物理 = config.setdefault('physics', {})
    宫位 = 物理.setdefault('pillarWeights', {})
    if 'pg_y' in st.session_state: 宫位['year'] = st.session_state['pg_y']
    if 'pg_m' in st.session_state: 宫位['month'] = st.session_state['pg_m']
    if 'pg_d' in st.session_state: 宫位['day'] = st.session_state['pg_d']
    if 'pg_h' in st.session_state: 宫位['hour'] = st.session_state['pg_h']
    if 'physics_self_punishment_damping' in st.session_state:
        物理['self_punishment_damping'] = st.session_state['physics_self_punishment_damping']
    
    季节 = 物理.setdefault('seasonWeights', {})
    if 'sw_wang' in st.session_state: 季节['wang'] = st.session_state['sw_wang']
    if 'sw_xiang' in st.session_state: 季节['xiang'] = st.session_state['sw_xiang']
    if 'sw_xiu' in st.session_state: 季节['xiu'] = st.session_state['sw_xiu']
    if 'sw_qiu' in st.session_state: 季节['qiu'] = st.session_state['sw_qiu']
    if 'sw_si' in st.session_state: 季节['si'] = st.session_state['sw_si']

    # 结构
    结构 = config.setdefault('structure', {})
    if 's_rw' in st.session_state: 结构['rootingWeight'] = st.session_state['s_rw']
    if 's_eb' in st.session_state: 结构['exposedBoost'] = st.session_state['s_eb']
    if 's_sp' in st.session_state: 结构['samePillarBonus'] = st.session_state['s_sp']

    # 交互
    交互 = config.setdefault('interactions', {})
    天干合 = 交互.setdefault('stemFiveCombination', {})
    事件 = 交互.setdefault('branchEvents', {})
    if 'p2_combine_threshold' in st.session_state: 天干合['threshold'] = st.session_state['p2_combine_threshold']
    if 'p2_combine_bonus' in st.session_state: 天干合['bonus'] = st.session_state['p2_combine_bonus']
    if 'p2_combine_penalty' in st.session_state: 天干合['penalty'] = st.session_state['p2_combine_penalty']
    if 'p2_jealousy' in st.session_state: 天干合['jealousyDamping'] = st.session_state['p2_jealousy']
    
    # V12.1 波动力学参数回写
    if 'wp_clash_phase' in st.session_state: 事件['clashPhase'] = st.session_state['wp_clash_phase']
    if 'wp_clash_entropy' in st.session_state: 事件['clashEntropy'] = st.session_state['wp_clash_entropy']
    if 'wp_punish_phase' in st.session_state: 事件['punishPhase'] = st.session_state['wp_punish_phase']
    if 'wp_punish_entropy' in st.session_state: 事件['punishEntropy'] = st.session_state['wp_punish_entropy']
    if 'wp_resonance_q' in st.session_state: 事件['resonanceQ'] = st.session_state['wp_resonance_q']
    if 'wp_harm_damping' in st.session_state: 事件['harmDamping'] = st.session_state['wp_harm_damping']
    
    # 墓库 (Vault)
    库 = 交互.setdefault('vault', {})
    if 'p2_vault_thresh' in st.session_state: 库['threshold'] = st.session_state['p2_vault_thresh']
    if 'p2_vault_sealed' in st.session_state: 库['sealedDamping'] = st.session_state['p2_vault_sealed']
    if 'p2_vault_open' in st.session_state: 库['openBonus'] = st.session_state['p2_vault_open']
    if 'p2_vault_break' in st.session_state: 库['breakPenalty'] = st.session_state['p2_vault_break']

    # 时空背景 (Spacetime)
    时空 = config.setdefault('spacetime', {})
    if 'st_luck_w' in st.session_state: 时空['luckPillarWeight'] = st.session_state['st_luck_w']
    if 'st_annual_w' in st.session_state: 时空['annualPillarWeight'] = st.session_state['st_annual_w']
    
    geo = 时空.setdefault('geo', {})
    if 'st_geo_heat' in st.session_state: geo['latitudeHeat'] = st.session_state['st_geo_heat']
    
    era = 时空.setdefault('era', {})
    if 'st_era_bonus' in st.session_state: era['eraBonus'] = st.session_state['st_era_bonus']

    # 能量流转
    流转 = config.setdefault('flow', {})
    if 'f_ri_b' in st.session_state: 流转.setdefault('resourceImpedance', {})['base'] = st.session_state['f_ri_b']
    if 'f_ri_wp' in st.session_state: 流转.setdefault('resourceImpedance', {})['weaknessPenalty'] = st.session_state['f_ri_wp']
    if 'f_ov_df' in st.session_state: 流转.setdefault('outputViscosity', {})['drainFriction'] = st.session_state['f_ov_df']
    if 'p2_gen_drain' in st.session_state: 流转['generationDrain'] = st.session_state['p2_gen_drain']
    if 'p2_ctrl_imp' in st.session_state: 流转['controlImpact'] = st.session_state['p2_ctrl_imp']
    if 'f_damp_fac' in st.session_state: 流转['dampingFactor'] = st.session_state['f_damp_fac']
    
    # Cybernetics
    反馈 = 流转.setdefault('feedback', {})
    if 'fb_inv_threshold' in st.session_state: 反馈['inverseControlThreshold'] = st.session_state['fb_inv_threshold']
    if 'fb_inv_recoil' in st.session_state: 反馈['inverseRecoilMultiplier'] = st.session_state['fb_inv_recoil']
    if 'fb_era_shield' in st.session_state: 反馈['eraShieldingFactor'] = st.session_state['fb_era_shield']
    
    用神 = 流转.setdefault('yongshen', {})
    if 'ys_resonance' in st.session_state: 用神['resonanceBoost'] = st.session_state['ys_resonance']

    # 相变
    相变 = 流转.setdefault('phaseChange', {})
    if 'pc_scorched' in st.session_state: 相变['scorchedEarthDamping'] = st.session_state['pc_scorched']
    if 'pc_frozen' in st.session_state: 相变['frozenWaterDamping'] = st.session_state['pc_frozen']

    # 藏干
    藏干 = 物理.setdefault('hiddenStemRatios', {})
    if 'hs_main' in st.session_state: 藏干['main'] = st.session_state['hs_main']
    if 'hs_mid' in st.session_state: 藏干['middle'] = st.session_state['hs_mid']
    if 'hs_rem' in st.session_state: 藏干['remnant'] = st.session_state['hs_rem']

    # 旺衰
    旺衰 = config.setdefault('strength', {})
    if 'strength_energy_threshold' in st.session_state: 旺衰['energy_threshold_center'] = st.session_state['strength_energy_threshold']
    if 'strength_phase_width' in st.session_state: 旺衰['phase_transition_width'] = st.session_state['strength_phase_width']
    
    gat = config.setdefault('gat', {})
    if 'gat_use_gat' in st.session_state: gat['use_gat'] = st.session_state['gat_use_gat']
    if 'strength_attention_dropout' in st.session_state: gat['attention_dropout'] = st.session_state['strength_attention_dropout']

    # 十神权重
    权重组 = config.setdefault('particleWeights', {})
    consts = get_constants()
    for 神 in consts.TEN_GODS:
        键 = f"pw_p2_{神}"
        if 键 in st.session_state:
            权重组[神] = st.session_state[键] / 100.0

    return config

def render_tuning_panel(controller, golden_config):
    """
    在侧边栏渲染量子真言调优面板。
    """
    config_model = ConfigModel()
    
    # 初始化状态 (如果 session 为空)
    if 'pg_y' not in st.session_state:
        最新配置 = config_model.load_config()
        初始化界面状态(最新配置)

    # 合并基准配置 (fp) - 用于计算返回
    fp = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    if golden_config:
        deep_merge_params(fp, golden_config)

    # === UI 渲染开始 ===
    st.sidebar.markdown("""
        <style>
        /* 消除侧边栏顶部空白，但保持合理间距 */
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div { padding-top: 0.5rem !important; }
        
        /* 针对侧边栏主容器的精细调整 */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        
        /* 标签页样式优化 */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 4px; 
            margin-bottom: 10px;
        }
        .stTabs [data-baseweb="tab"] { 
            padding: 6px 10px; 
            background: rgba(255,255,255,0.03); 
            border-radius: 4px;
            font-size: 0.85rem;
        }
        
        /* 滑块样式优化 */
        .stSlider { 
            padding-bottom: 5px; 
            margin-top: 0px;
        }
        .stSlider label { 
            font-size: 0.75rem !important; 
            font-weight: 500;
            /* margin-bottom: -15px !important; REMOVED to fix overlap */
            padding-bottom: 2px !important;
        }
        .stSlider [data-testid="stWidgetLabel"] p {
            font-size: 0.75rem !important;
        }
        
        /* 分隔线间距 */
        hr { margin: 1rem 0 !important; }
        
        /* 标题间距 */
        .tab-header {
            margin-top: 10px;
            margin-bottom: 15px;
            display: block;
            font-weight: bold;
            font-size: 0.9rem;
            color: #4facfe; /* 加入一点色彩区分 */
        }
        </style>
        <style>
        /* 更紧凑的布局 - 通用调整 */
        div[data-testid="stExpander"] div[role="button"] p {
            font-size: 0.9rem;
            font-weight: 600;
        }
        .stNumberInput { padding-bottom: 2px !important; margin-top: -2px !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### 🎚️ 量子实验室 | 调音混音台")
    
    # 操作按钮组
    列1, 列2 = st.sidebar.columns(2)
    with 列1:
        if st.button("🔃 同步", help="从 parameters.json 重新加载", use_container_width=True):
            最新配置 = config_model.load_config()
            初始化界面状态(最新配置, 强制=True)
            st.rerun()
    with 列2:
        if st.button("💾 固化", help="保存推子参数", use_container_width=True):
            待保存配置 = merge_sidebar_values_to_config(copy.deepcopy(fp))
            if config_model.save_config(待保存配置, merge=True):
                st.sidebar.success("已固化!")
            else:
                st.sidebar.error("失败")

    st.sidebar.divider()

    # --- 调音台标签页 ---
    标签_主控, 标签_初始, 标签_交互, 标签_时空 = st.sidebar.tabs(["🎛️ 主控", "🌱 初始", "⚡ 交互", "🌌 时空"])

    # --- 标签页 1: 主控 (Particle Weights / Ten Gods) ---
    with 标签_主控:
        st.markdown('<span class="tab-header">⚛️ 十神权重推子 (God Mixers) 🎖️</span>', unsafe_allow_html=True)
        consts = get_constants()
        最终十神权重 = {}
        for i in range(0, 10, 2):
            c1, c2 = st.columns(2)
            for idx, col in enumerate([c1, c2]):
                if i + idx < len(consts.TEN_GODS):
                    神 = consts.TEN_GODS[i+idx]
                    键 = f"pw_p2_{神}"
                    with col:
                        值 = st.slider(f"{神} 🎖️", 50, 150, key=键, step=5)
                        最终十神权重[神] = 值 / 100.0

    # --- 标签页 2: 初始能量场 (Phase 1 & Structure) ---
    with 标签_初始:
        with st.expander("📍 宫位权重 (Pillars) 🎖️", expanded=True):
            c1, c2 = st.columns(2)
            with c1: st.slider("年柱 (Y) 🎖️", 0.5, 2.0, key='pg_y', step=0.05)
            with c2: st.slider("月令 (M) ⭐🎖️", 0.5, 2.0, key='pg_m', step=0.05)
            with c1: st.slider("日主 (D) 🎖️", 0.5, 2.0, key='pg_d', step=0.05)
            with c2: st.slider("时柱 (H) 🎖️", 0.5, 2.0, key='pg_h', step=0.05)
            
        with st.expander("🌰 藏干比例 (Hidden) 🎖️", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1: st.number_input("本气 🎖️", 0.0, 1.0, key='hs_main', step=0.05)
            with c2: st.number_input("中气 🎖️", 0.0, 1.0, key='hs_mid', step=0.05)
            with c3: st.number_input("余气 🎖️", 0.0, 1.0, key='hs_rem', step=0.05)

        with st.expander("⚡ 粒子结构 (Structure) 🎖️", expanded=True):
            st.slider("通根系数 🎖️", 0.5, 2.0, key='s_rw', step=0.1)
            st.slider("透干加成 🎖️", 1.0, 2.5, key='s_eb', step=0.1)
            st.slider("同柱加成 🎖️", 1.0, 2.5, key='s_sp', step=0.1)

    # --- 标签页 3: 动态交互场 (Phase 2 & Strength) ---
    with 标签_交互:
        with st.expander("🌊 刑冲克害 (Physics) 🎖️", expanded=True):
            tc, tp = st.tabs(["相克/害 (Classic)", "波动力学 (Wave)"])
            with tc:
                c1, c2 = st.columns(2)
                with c1: st.slider("克制 (Ctrl) 🎖️", 0.0, 1.0, key='p2_ctrl_imp', step=0.05, help="五行相克的基础力度")
                with c2: st.slider("穿害 (Harm) 🎖️", 0.0, 1.0, key='wp_harm_damping', step=0.05, help="地支六害的穿透系数")
                st.caption("刑冲已移至波动力学")
            with tp:
                st.caption("V12.0 非线性干涉引擎")
                c1, c2 = st.columns(2)
                with c1: st.slider("冲相位 (Clash) 🎖️", 1.5, 3.14, key='wp_clash_phase', help="2.618=150度(强相消)")
                with c2: st.slider("熵损 (Entropy)", 0.1, 1.0, key='wp_clash_entropy')
                
                c3, c4 = st.columns(2)
                with c3: st.slider("刑相位 (Punish)", 1.5, 3.14, key='wp_punish_phase', help="2.513=144度")
                with c4: st.slider("共振Q值 (Reson)", 1.0, 2.0, key='wp_resonance_q', help="土刑共振激旺因子")

        with st.expander("⚔️ 生克与争合 (Interactions)", expanded=False):
            c1, c2 = st.columns(2)
            with c1: st.slider("生发耗泄 🎖️", 0.0, 1.0, key='p2_gen_drain', step=0.05)
            with c2: st.slider("争合妒合 🎖️", 0.0, 1.0, key='p2_jealousy', step=0.05)
            
        with st.expander("🔗 规模效应 (Combo/Vault) 🎖️", expanded=True):
            tc, tv = st.tabs(["合局 🎖️", "墓库 🎖️"])
            with tc:
                st.slider("三合增益 🎖️", 1.0, 3.0, key='p2_three_harmony_bonus', step=0.1)
                st.slider("三会增益 🎖️", 1.5, 4.0, key='p2_three_meeting_bonus', step=0.1)
                st.slider("六合增益 🎖️", 1.0, 2.0, key='p2_six_harmony_bonus', step=0.1)
            with tv:
                st.slider("阈值 🎖️", 0.0, 10.0, key='p2_vault_thresh', step=0.1)
                st.slider("爆发 🎖️", 1.0, 5.0, key='p2_vault_open', step=0.1)
                st.slider("惩罚 🎖️", 0.0, 1.0, key='p2_vault_break', step=0.05)

        with st.expander("📊 判定场 🎖️", expanded=False):
            st.slider("阈值中心点 🎖️", 1.0, 6.0, key='strength_energy_threshold', step=0.01)
            st.checkbox("启用 GAT 注意力 ✅", key='gat_use_gat')

    # --- 标签页 4: 时空与背景 (Phase 3 & Flow) ---
    with 标签_时空:
        with st.expander("⏳ 时空权重 (Weights) 🎖️", expanded=True):
            st.slider("大运 (Luck) 🎖️", 0.1, 3.0, key='st_luck_w', step=0.1)
            st.slider("流年 (Annual) 🎖️", 0.1, 3.0, key='st_annual_w', step=0.1)

        with st.expander("🌎 环境红利 (Field) 🎖️", expanded=True):
            st.slider("地理热力 🎖️", 0.0, 0.2, key='st_geo_heat', step=0.01)
            st.slider("九运时代 🎖️", 0.0, 0.5, key='st_era_bonus', step=0.01)

        with st.expander("🌊 能量流转 (Flow) ✅", expanded=True):
            st.slider("系统熵增 ✅", 0.0, 0.2, key='f_entropy', step=0.01)
            st.slider("焦土/冻水缩减 ✅", 0.0, 1.0, key='pc_scorched', step=0.05)

        with st.expander("🛡️ 控制论反馈 (Cybernetics) 🎖️", expanded=True):
            st.caption("V12.2 反克与屏蔽机制")
            st.slider("反克阈值 (Ratio) 🎖️", 2.0, 10.0, key='fb_inv_threshold', step=0.1, help="触发反克的能量倍率阈值")
            st.slider("反噬倍率 (Recoil) 🎖️", 1.0, 5.0, key='fb_inv_recoil', step=0.1, help="触发反克时的反噬伤害倍数")
            st.slider("环境屏蔽 (Shield) 🎖️", 0.0, 1.0, key='fb_era_shield', step=0.1, help="得令得地的伤害屏蔽率")
            st.slider("用神共振 (Resonance)", 1.0, 2.0, key='ys_resonance', step=0.1, help="和大运产生共振时的增益")

    # 最后合并当前 session 状态到返回的配置对象中
    merge_sidebar_values_to_config(fp)
            
    return fp, 最终十神权重
