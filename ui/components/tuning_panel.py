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
        'f_gen_drain': 流转.get('generationDrain', 0.3),
        'f_ctrl_imp': 流转.get('controlImpact', 0.5),
        'f_damp_fac': 流转.get('dampingFactor', 0.1),
        'pc_scorched': 相变.get('scorchedEarthDamping', 0.15),
        'pc_frozen': 相变.get('frozenWaterDamping', 0.3),
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
    if 'p2_clash_damping' in st.session_state: 事件['clashDamping'] = st.session_state['p2_clash_damping']

    # 能量流转
    流转 = config.setdefault('flow', {})
    if 'f_ri_b' in st.session_state: 流转.setdefault('resourceImpedance', {})['base'] = st.session_state['f_ri_b']
    if 'f_ri_wp' in st.session_state: 流转.setdefault('resourceImpedance', {})['weaknessPenalty'] = st.session_state['f_ri_wp']
    if 'f_ov_df' in st.session_state: 流转.setdefault('outputViscosity', {})['drainFriction'] = st.session_state['f_ov_df']
    if 'f_gen_drain' in st.session_state: 流转['generationDrain'] = st.session_state['f_gen_drain']
    if 'f_ctrl_imp' in st.session_state: 流转['controlImpact'] = st.session_state['f_ctrl_imp']
    if 'f_damp_fac' in st.session_state: 流转['dampingFactor'] = st.session_state['f_damp_fac']

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
    st.sidebar.markdown("### 🧬 量子真言 | 调优控制台")
    
    # 操作按钮组
    列1, 列2 = st.sidebar.columns(2)
    with 列1:
        if st.button("🔃 从文件同步", help="从 parameters.json 强制重新加载，放弃未保存的手动调整"):
            最新配置 = config_model.load_config()
            初始化界面状态(最新配置, 强制=True)
            st.rerun()
    with 列2:
        if st.button("💾 保存到文件", help="将当前界面所有的手动滑块参数同步到 parameters.json"):
            待保存配置 = merge_sidebar_values_to_config(copy.deepcopy(fp))
            if config_model.save_config(待保存配置, merge=True):
                st.sidebar.success("已同步到参数表!")
            else:
                st.sidebar.error("同步失败")

    st.sidebar.divider()

    # --- 层次化展开栏 ---
    
    # Phase 1: 基础物理场
    with st.sidebar.expander("🌍 Phase 1: 初始能量场", expanded=True):
        st.markdown("**📍 宫位引力 (Pillar Weights)**")
        st.slider("年柱 (Year)", 0.5, 2.0, key='pg_y', step=0.05)
        st.slider("月令 (Month) ⭐", 0.5, 2.0, key='pg_m', step=0.05)
        st.slider("日主 (Day)", 0.5, 2.0, key='pg_d', step=0.05)
        st.slider("时柱 (Hour)", 0.5, 2.0, key='pg_h', step=0.05)
        
        st.divider()
        st.markdown("**🌰 藏干比例 (Hidden Stems)**")
        c1, c2, c3 = st.columns(3)
        with c1: st.number_input("本气", 0.0, 1.0, key='hs_main', step=0.05)
        with c2: st.number_input("中气", 0.0, 1.0, key='hs_mid', step=0.05)
        with c3: st.number_input("余气", 0.0, 1.0, key='hs_rem', step=0.05)
        
        st.divider()
        st.markdown("**⚡ 季节衰减 (Seasonality)**")
        st.slider("旺 (Prosperous)", 1.0, 2.0, key='sw_wang', step=0.05)
        st.slider("相 (Assist)", 0.8, 1.5, key='sw_xiang', step=0.05)
        st.slider("休 (Rest)", 0.6, 1.2, key='sw_xiu', step=0.05)
        st.slider("囚 (Trapped)", 0.4, 1.0, key='sw_qiu', step=0.05)
        st.slider("死 (Dead)", 0.2, 0.8, key='sw_si', step=0.05)
        
        st.divider()
        st.slider("自刑惩罚系数", 0.0, 1.0, key='physics_self_punishment_damping', step=0.05)

    # Phase 2: 动态交互层
    with st.sidebar.expander("⚡ Phase 2: 动态生克场", expanded=True):
        st.info("ℹ️ V10.0 内核锁定：交互逻辑基于 Sigmoid 非线性算子")
        st.markdown("**🧲 性质参数**")
        st.slider("合化阈值", 0.8, 2.5, key='p2_combine_threshold', step=0.1)
        st.slider("合化增益", 1.0, 2.5, key='p2_combine_bonus', step=0.1)
        st.slider("合化失败折损", 0.0, 1.0, key='p2_combine_penalty', step=0.05)
        st.slider("争合损耗 (Jealousy)", 0.0, 1.0, key='p2_jealousy', step=0.05)
        st.slider("冲的折损 (Clash)", 0.0, 1.0, key='p2_clash_damping', step=0.05)
        
        st.divider()
        st.markdown("**🤝 合局物理 (Harmony)**")
        st.slider("三合增益", 1.0, 3.0, key='p2_three_harmony_bonus', step=0.1)
        st.slider("半合增益", 1.0, 2.0, key='p2_half_harmony_bonus', step=0.1)
        st.slider("三会增益", 1.5, 4.0, key='p2_three_meeting_bonus', step=0.1)
        st.slider("六合增益", 1.0, 2.0, key='p2_six_harmony_bonus', step=0.1)
        st.slider("六合羁绊惩罚", 0.0, 1.0, key='p2_six_harmony_binding', step=0.05)

    # 粒子结构
    with st.sidebar.expander("⚛️ 粒子结构 (Structure)", expanded=True):
        st.slider("通根系数", 0.5, 2.0, key='s_rw', step=0.1)
        st.slider("透干加成", 1.0, 3.0, key='s_eb', step=0.1)
        st.slider("同柱物理加成", 1.0, 5.0, key='s_sp', step=0.1)

    # 能量流转
    with st.sidebar.expander("🌊 能量流转 (Flow)", expanded=True):
        st.markdown("**🛡️ 阻尼协议**")
        st.slider("基础资源阻抗", 0.0, 1.0, key='f_ri_b', step=0.05)
        st.slider("虚不受补 (Weakness)", 0.0, 1.0, key='f_ri_wp', step=0.05)
        st.slider("输出粘滞 (Viscosity)", 0.0, 1.0, key='f_ov_df', step=0.05)
        st.slider("能量消耗 (Gen Drain)", 0.1, 0.9, key='f_gen_drain', step=0.05)
        st.slider("克制杀伤力 (Control)", 0.1, 1.5, key='f_ctrl_imp', step=0.05)
        st.slider("系统自然阻尼", 0.0, 0.5, key='f_damp_fac', step=0.01)
        
        st.divider()
        st.markdown("**🧊 相变协议 (Phase Change)**")
        st.slider("焦土不生 (Scorched)", 0.0, 1.0, key='pc_scorched', step=0.05)
        st.slider("冻水不生 (Frozen)", 0.0, 1.0, key='pc_frozen', step=0.05)

    # 旺衰场
    with st.sidebar.expander("📊 旺衰判定 (Strength Field)", expanded=True):
        st.slider("能量阈值中心点", 1.0, 6.0, key='strength_energy_threshold', step=0.01)
        st.slider("相变平滑宽度", 1.0, 20.0, key='strength_phase_width', step=0.5)
        st.checkbox("启用 GAT 动态注意力", key='gat_use_gat')
        st.slider("注意力稀疏度 (Dropout)", 0.0, 1.0, key='strength_attention_dropout', step=0.01)

    # 十神权重校准
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚛️ 十神权重校准")
    consts = get_constants()
    最终十神权重 = {}
    for i in range(0, 10, 2):
        l_col, r_col = st.sidebar.columns(2)
        if i < len(consts.TEN_GODS):
            神 = consts.TEN_GODS[i]
            键 = f"pw_p2_{神}"
            with l_col: 
                值 = st.slider(f"{神}", 50, 150, key=键, step=5)
                最终十神权重[神] = 值 / 100.0
        if i + 1 < len(consts.TEN_GODS):
            神 = consts.TEN_GODS[i+1]
            键 = f"pw_p2_{神}"
            with r_col: 
                值 = st.slider(f"{神}", 50, 150, key=键, step=5)
                最终十神权重[神] = 值 / 100.0

    # 最后合并当前 session 状态到返回的配置对象中
    merge_sidebar_values_to_config(fp)
            
    return fp, 最终十神权重
