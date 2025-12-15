import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import altair as alt
import datetime

from core.engine_v91 import EngineV91 as QuantumEngine  # V9.1 Spacetime Genesis
from core.context import DestinyContext  # Trinity V4.0
from core.bazi_profile import BaziProfile, VirtualBaziProfile
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

# V9.5 MVC Controller (for standard data access)
from controllers.bazi_controller import BaziController

# === Trinity V6.0 Helper Functions ===

def create_profile_from_case(case: dict, luck_pillar: str) -> VirtualBaziProfile:
    """
    Factory to create a VirtualBaziProfile from a JSON case (legacy format).
    """
    bazi_list = case.get('bazi', ['', '', '', '']) 
    pillars = {
        'year': bazi_list[0],
        'month': bazi_list[1],
        'day': bazi_list[2],
        'hour': bazi_list[3] if len(bazi_list) > 3 else ''
    }
    dm = case.get('day_master')
    gender = 1 if case.get('gender') == '男' else 0
    
    return VirtualBaziProfile(
        pillars=pillars,
        static_luck=luck_pillar,
        day_master=dm,
        gender=gender
    )

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
        return data

    # --- Load Params Helper ---
    def load_params_from_disk():
        path = os.path.join(os.path.dirname(__file__), "../../data/golden_parameters.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}
        
    def save_params_to_disk(new_params):
        path = os.path.join(os.path.dirname(__file__), "../../data/golden_parameters.json")
        original = load_params_from_disk()
        
        # Update global
        if 'weights' not in original: original['weights'] = {}
        if 'k_factors' not in original: original['k_factors'] = {}
        if 'logic_switches' not in original: original['logic_switches'] = {}

        # Update Weights
        w = original['weights']
        w['w_e_weight'] = new_params.get('w_e_weight', 1.0)
        w['f_yy_correction'] = new_params.get('f_yy_correction', 1.1)
        
        w['W_Career_Officer'] = new_params.get('w_career_officer', 0.8)
        w['W_Career_Resource'] = new_params.get('w_career_resource', 0.1)
        w['W_Career_Output'] = new_params.get('w_career_output', 0.0)
        w['W_Wealth_Cai'] = new_params.get('w_wealth_cai', 0.6)
        w['W_Wealth_Output'] = new_params.get('w_wealth_output', 0.4)
        
        w['W_Rel_Spouse'] = new_params.get('w_rel_spouse', 0.35)
        w['W_Rel_Self'] = new_params.get('w_rel_self', 0.20)
        w['W_Rel_Output'] = new_params.get('w_rel_output', 0.15)
        
        # Update K Factors
        k = original['k_factors']
        k['K_Control_Conversion'] = new_params.get('k_control', 0.55)
        k['K_Buffer_Defense'] = new_params.get('k_buffer', 0.40)
        k['K_Clash_Robbery'] = new_params.get('k_clash', 1.2)
        k['K_Mutiny_Betrayal'] = new_params.get('k_mutiny', 1.8)
        k['K_Leak_Drain'] = new_params.get('k_leak', 0.87)
        k['K_Pressure_Attack'] = new_params.get('k_pressure', 1.0)
        k['K_Burden_Wealth'] = new_params.get('k_burden', 1.0)
        k['K_Broken_Collapse'] = new_params.get('k_broken', 1.5)
        k['K_Capture_Wealth'] = new_params.get('k_capture', 0.0)
        
        # Flags
        original['logic_switches']['enable_mediation_exemption'] = new_params.get('enable_mediation_exemption', True)
        original['logic_switches']['enable_structural_clash'] = new_params.get('enable_structural_clash', True)

        with open(path, "w") as f:
            json.dump(original, f, indent=4, ensure_ascii=False)
        st.toast("✅ Parameters Saved to Disk!")

    cases = load_cases()
    defaults = load_params_from_disk()
    
    # Flatten defaults for sliders
    fd = {}
    if defaults:
        # 1. Weights (Mixed Global + Macro + Rel)
        w = defaults.get('weights', {})
        fd['w_e'] = w.get('w_e_weight', 1.0)
        fd['f_yy'] = w.get('f_yy_correction', 1.1)
        
        fd['w_off'] = w.get('W_Career_Officer', 0.8)
        fd['w_res'] = w.get('W_Career_Resource', 0.1)
        fd['w_out_c'] = w.get('W_Career_Output', 0.0)
        fd['w_cai'] = w.get('W_Wealth_Cai', 0.6)
        fd['w_out_w'] = w.get('W_Wealth_Output', 0.4)
        
        fd['w_spouse'] = w.get('W_Rel_Spouse', 0.35)
        fd['w_self'] = w.get('W_Rel_Self', 0.20)
        fd['w_out_r'] = w.get('W_Rel_Output', 0.15)
        
        # 2. K Factors
        k = defaults.get('k_factors', {})
        fd['k_ctl'] = k.get('K_Control_Conversion', 0.55)
        fd['k_buf'] = k.get('K_Buffer_Defense', 0.40)
        fd['k_mut'] = k.get('K_Mutiny_Betrayal', 1.8)
        fd['k_cap'] = k.get('K_Capture_Wealth', 0.0)
        fd['k_leak'] = k.get('K_Leak_Drain', 0.87)
        fd['k_clash'] = k.get('K_Clash_Robbery', 1.2)
        fd['k_press'] = k.get('K_Pressure_Attack', 1.0)
        fd['k_brk'] = k.get('K_Broken_Collapse', 1.5)
        fd['k_bur'] = k.get('K_Burden_Wealth', 1.0)
        
        # 3. Flags
        fl = defaults.get('logic_switches', {})
        fd['en_med'] = fl.get('enable_mediation_exemption', True)
        fd['en_str'] = fl.get('enable_structural_clash', True)


    # --- SIDEBAR CONTROLS ---
    st.sidebar.title("🎛️ 物理参数 (Physics)")
    
    # === V6.0+ 新增：算法核心控制台 ===
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ 算法核心控制台")
    st.sidebar.caption("基于马云/乔布斯案例调优的核心参数")
    
    # 导入默认配置值
    from core.config_rules import (
        SCORE_SKULL_CRASH, SCORE_TREASURY_BONUS, SCORE_TREASURY_PENALTY,
        ENERGY_THRESHOLD_STRONG, ENERGY_THRESHOLD_WEAK, SCORE_GENERAL_OPEN,
        SCORE_SANHE_BONUS, SCORE_LIUHE_BONUS, SCORE_CLASH_PENALTY
    )
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    
    # Skull Crash (骷髅协议崩塌分)
    score_skull_crash = st.sidebar.number_input(
        "💀 Skull Crash (三刑崩塌分)", 
        min_value=-100.0, max_value=0.0,
        value=SCORE_SKULL_CRASH,
        step=5.0,
        help="丑未戌三刑触发时的强制熔断分 (乔布斯2011案例调优)"
    )
    
    # Treasury Bonus (财库爆发分)
    score_treasury_bonus = st.sidebar.slider(
        "🏆 Treasury Bonus (身强暴富分)",
        min_value=0.0, max_value=50.0,
        value=SCORE_TREASURY_BONUS,
        step=1.0,
        help="身强冲开财库时的爆发加成 (马云2014 IPO案例调优)"
    )
    
    # Treasury Penalty (财库风险分)
    score_treasury_penalty = st.sidebar.slider(
        "⚠️ Treasury Penalty (身弱风险分)",
        min_value=-50.0, max_value=0.0,
        value=SCORE_TREASURY_PENALTY,
        step=1.0,
        help="身弱冲开财库时的风险惩罚 (伦理安全阀)"
    )
    
    # Energy Thresholds (能量阈值)
    st.sidebar.markdown("**能量阈值线**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        energy_strong = st.number_input(
            "🔥 身旺线",
            min_value=0.0, max_value=10.0,
            value=ENERGY_THRESHOLD_STRONG,
            step=0.5
        )
    with col2:
        energy_weak = st.number_input(
            "💧 身弱线",
            min_value=0.0, max_value=10.0,
            value=ENERGY_THRESHOLD_WEAK,
            step=0.5
        )
    
    # General Open Score (普通库开启分)
    score_general_open = st.sidebar.slider(
        "🗝️ General Open (普通开库分)",
        min_value=0.0, max_value=20.0,
        value=SCORE_GENERAL_OPEN,
        step=1.0
    )
    
    # === [Harmony & Conflict] 合化控制台 ===
    st.sidebar.markdown("**❤️ 合化与冲突 (Harmony)**")
    
    # SanHe (三合)
    score_sanhe_bonus = st.sidebar.slider(
        "✨ Trinity Bonus (三合加成)",
        min_value=0.0, max_value=30.0,
        value=SCORE_SANHE_BONUS,
        step=1.0,
        help="三合局且为喜用神时的强力加成"
    )
    
    # LiuHe (六合)
    score_liuhe_bonus = st.sidebar.slider(
        "🤝 Combo Bonus (六合加成)",
        min_value=0.0, max_value=20.0,
        value=SCORE_LIUHE_BONUS,
        step=1.0,
        help="六合（羁绊/解冲）的基础加分"
    )
    
    # Clash (六冲)
    score_clash_penalty = st.sidebar.slider(
        "💥 Clash Penalty (六冲惩罚)",
        min_value=-20.0, max_value=0.0,
        value=SCORE_CLASH_PENALTY,
        step=1.0,
        help="六冲且未被化解时的基础扣分"
    )

    # === [V7.0 Full Algo Tuning] 深度调优控制台 ===
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ 深度调优 (Deep Tuning)")
    
    # === [V7.3 Final Tuning Console] 上帝模式控制台 ===
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ 终极调优 (God Mode)")
    
    # Defaults
    import copy
    fp = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # --- 🤖 AI Command Center Listener ---
    cmd_path = os.path.join(os.path.dirname(__file__), "../../data/command_center_config.json")
    if os.path.exists(cmd_path):
        try:
            with open(cmd_path, "r") as f:
                cmd_cfg = json.load(f)
            
            last_ts = st.session_state.get('cmd_last_ts', 0)
            curr_ts = cmd_cfg.get('timestamp', 0)
            
            if curr_ts > last_ts:
                st.toast(f"🤖 AI Remote Override: {cmd_cfg.get('description', 'Update')}")
                st.session_state['cmd_last_ts'] = curr_ts
                st.session_state['ai_overrides'] = cmd_cfg.get('updates', {})
                
                # Reset Sliders to pick up new values
                # Keys usually start with pg_, s_, i_, m_
                keys_to_reset = [k for k in st.session_state.keys() if k.startswith(('pg_', 's_', 'i_', 'm_'))]
                for k in keys_to_reset:
                    del st.session_state[k]
                
                st.rerun()
                
        except Exception as e:
            st.warning(f"AI Link Unstable: {e}")

    # Apply AI Overrides to fp
    if 'ai_overrides' in st.session_state:
        def deep_merge(target, source):
            for k, v in source.items():
                if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                    deep_merge(target[k], v)
                else:
                    target[k] = v
        deep_merge(fp, st.session_state['ai_overrides'])
        
    
    # --- Panel 1: 基础场域 (Physics) ---
    with st.sidebar.expander("🌍 基础场域 (Physics)", expanded=True):
        st.caption("宫位引力 (Pillar Gravity)")
        pg_year = st.slider("年柱 (Year)", 0.5, 1.5, fp['physics']['pillarWeights']['year'], 0.1, key='pg_y')
        pg_month = st.slider("月令 (Month)", 0.5, 2.0, fp['physics']['pillarWeights']['month'], 0.1, key='pg_m')
        pg_day = st.slider("日主 (Day)", 0.5, 1.5, fp['physics']['pillarWeights']['day'], 0.1, key='pg_d')
        pg_hour = st.slider("时柱 (Hour)", 0.5, 1.5, fp['physics']['pillarWeights']['hour'], 0.1, key='pg_h')

    # --- Panel 2: 粒子动态 (Structure) ---
    with st.sidebar.expander("⚛️ 粒子动态 (Structure)", expanded=False):
        st.caption("垂直作用 (Vertical)")
        root_w = st.slider("通根系数 (Rooting)", 0.5, 2.0, fp['structure']['rootingWeight'], 0.1, key='s_rw')
        exposed_b = st.slider("透干加成 (Exposed)", 1.0, 3.0, fp['structure']['exposedBoost'], 0.1, key='s_eb')
        same_pill = st.slider("自坐强根 (Sitting)", 1.0, 2.0, fp['structure']['samePillarBonus'], 0.1, key='s_sp')
        
        st.caption("特殊状态 (Special)")
        void_p = st.slider("⚫ 黑洞/空亡 (Void)", 0.0, 1.0, fp['structure']['voidPenalty'], 0.1, key='s_vp', help="0=空掉，1=不空")

    # --- Panel 3: 几何交互 (Interactions) ---
    with st.sidebar.expander("⚗️ 几何交互 (Interactions)", expanded=False):
        st.caption("天干五合 (Stem Fusion)")
        s5_th = st.slider("合化阈值 (Threshold)", 0.5, 1.0, fp['interactions']['stemFiveCombination']['threshold'], 0.05, key='i_s5_th')
        s5_bo = st.slider("合化增益 (Bonus)", 1.0, 3.0, fp['interactions']['stemFiveCombination']['bonus'], 0.1, key='i_s5_bo')
        s5_pe = st.slider("合绊损耗 (Binding)", 0.0, 1.0, fp['interactions']['stemFiveCombination']['penalty'], 0.1, key='i_s5_pe')
        jealousy_d = st.slider("争合损耗 (Jealousy)", 0.0, 0.5, fp['interactions']['stemFiveCombination'].get('jealousyDamping', 0.3), 0.05, key='i_s5_jd')

        st.caption("地支成局 (Branch Combo)")
        cp = fp['interactions'].get('comboPhysics', {'trineBonus': 2.5, 'halfBonus': 1.5, 'archBonus': 1.1, 'directionalBonus': 3.0, 'resolutionCost': 0.1})
        
        c1, c2 = st.columns(2)
        with c1:
            cp_tb = st.number_input("三合(Trine)", 1.5, 5.0, cp['trineBonus'], 0.1, key='cp_tb')
            cp_hb = st.number_input("半合(Half)", 1.0, 3.0, cp['halfBonus'], 0.1, key='cp_hb')
        with c2:
            cp_db = st.number_input("三会(Dir)", 2.0, 6.0, cp['directionalBonus'], 0.1, key='cp_db')
            cp_rc = st.number_input("解冲消耗", 0.0, 0.5, cp['resolutionCost'], 0.05, key='cp_rc')
        
        st.divider()
        st.caption("地支事件 (Branch Events)")
        # Mapping legacy sliders to new structure
        be_clash_d = st.slider("冲的折损 (Clash Damp)", 0.1, 1.0, fp['interactions']['branchEvents']['clashDamping'], 0.1, key='i_be_cd')
        
        st.divider()
        st.caption("🔒 墓库物理 (Vault Physics)")
        vp = fp['interactions'].get('vaultPhysics', {
            'threshold': 20.0, 'sealedDamping': 0.4, 'openBonus': 1.5,
            'punishmentOpens': False, 'breakPenalty': 0.5
        })
        vp_th = st.slider("分界阈值 (Threshold)", 10.0, 50.0, vp['threshold'], 5.0, key='vp_th')
        vp_sd = st.slider("闭库折损 (Sealed)", 0.0, 1.0, vp['sealedDamping'], 0.1, key='vp_sd')
        vp_ob = st.slider("开库爆发 (Open Bonus)", 1.0, 3.0, vp['openBonus'], 0.1, key='vp_ob')
        vp_bp = st.slider("破墓伤害 (Broken P)", 0.0, 1.0, vp['breakPenalty'], 0.1, key='vp_bp')
        vp_po = st.checkbox("刑可开库 (Punishment Opens)", vp['punishmentOpens'], key='vp_po')

    # --- Panel 4: 能量流转 (Flow) ---
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
        sys_ent = st.slider("全局熵增 (Entropy)", 0.0, 0.2, entropy, 0.01, key='f_ge')
        
        st.divider()
        st.caption("Legacy Control")
        # Keep control impact for now if needed, or remove? 
        # Config schema might still have it? No, we removed standard keys.
        # But let's check config schema: controlImpact/Exhaust were REMOVED from default but FlowEngine still tries to use them (with fallbacks)?
        # Actually my FlowEngine V7.4 implementation read 'controlImpact'.
        # I should provide slider or default.
        ctl_imp = st.slider("克-打击力 (Impact)", 0.1, 1.0, f_conf.get('controlImpact', 0.5), 0.1, key='f_ci')
        
        st.caption("空间衰减 (Spatial)")
        sp_nodes = f_conf.get('spatialDecay', {'gap1': 0.6, 'gap2': 0.3})
        sp_g1 = st.slider("隔一柱 (Gap 1)", 0.1, 1.0, sp_nodes.get('gap1', 0.6), 0.1, key='f_sg1')
        sp_g2 = st.slider("隔两柱 (Gap 2)", 0.1, 1.0, sp_nodes.get('gap2', 0.3), 0.1, key='f_sg2')
        
        # Update param struct for write-back
        fp['flow'] = {
            'resourceImpedance': {'base': imp_base, 'weaknessPenalty': imp_weak},
            'outputViscosity': {'maxDrainRate': vis_rate, 'drainFriction': vis_fric},
            'globalEntropy': sys_ent,
            'controlImpact': ctl_imp,
            'spatialDecay': {'gap1': sp_g1, 'gap2': sp_g2}
        }

    # --- Panel 5: 时空修正 (Spacetime) ---
    with st.sidebar.expander("⏳ 时空修正 (Spacetime)", expanded=False):
        lp_w = st.slider("大运权重 (Luck Pillar)", 0.0, 1.0, fp['spacetime']['luckPillarWeight'], 0.1, key='st_lp')
        
        st.divider()
        st.caption("🌐 宏观场域 (Macro Field)")
        mp = fp.get('macroPhysics', {'eraElement': 'Fire', 'eraBonus': 0.2, 'eraPenalty': 0.1, 'latitudeHeat': 0.0, 'latitudeCold': 0.0, 'invertSeasons': False, 'useSolarTime': True})
        
        era_txt = st.selectbox("当前元运 (Era)", ["Period 9 (Fire)", "Period 8 (Earth)", "Period 1 (Water)"], index=0, key='mp_er')
        era_el = 'Fire' if 'Fire' in era_txt else ('Water' if 'Water' in era_txt else 'Earth')
        
        era_bon = st.slider("时代红利 (Bonus)", 0.0, 0.5, mp['eraBonus'], 0.1, key='mp_eb')
        era_pen = st.slider("时代阻力 (Penalty)", 0.0, 0.5, mp['eraPenalty'], 0.1, key='mp_ep')

        st.markdown("#### 🌐 时代修正因子 (ERA Factor)")
        st.caption("调整五行能量基线，模拟宏观环境影响。")

        col_wood, col_fire, col_earth, col_metal, col_water = st.columns(5)
        era_adjustment = {}
        era_adjustment['Wood'] = col_wood.slider("木 (ERA %)", -10, 10, 0, key='era_wood') / 100
        era_adjustment['Fire'] = col_fire.slider("火 (ERA %)", -10, 10, 0, key='era_fire') / 100
        era_adjustment['Earth'] = st.slider("土 (ERA %)", -10, 10, 0, key='era_earth') / 100
        era_adjustment['Metal'] = st.slider("金 (ERA %)", -10, 10, 0, key='era_metal') / 100
        era_adjustment['Water'] = st.slider("水 (ERA %)", -10, 10, 0, key='era_water') / 100
        
        st.caption("地理与时间 (Geo & Time)")
        
        # === V9.6: GEO 城市选择 (City Selection) ===
        def load_geo_cities_for_sidebar():
            """Load available cities from geo_coefficients.json for sidebar"""
            geo_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
            try:
                with open(geo_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cities = list(data.get("cities", {}).keys())
                    return ["Unknown"] + sorted(cities) if cities else ["Unknown", "Beijing", "Shanghai", "Singapore"]
            except:
                return ["Unknown", "Beijing", "Shanghai", "Singapore", "Harbin", "Guangzhou", "Sydney"]
        
        geo_cities_list = load_geo_cities_for_sidebar()
        p2_city_input = st.selectbox(
            "🌍 出生城市 (Birth City)",
            geo_cities_list,
            index=0,
            key='p2_sidebar_city',
            help="选择出生城市以应用 GEO 修正系数"
        )
        
        geo_hot = st.slider("南方火气 (South Heat)", 0.0, 0.5, mp['latitudeHeat'], 0.1, key='mp_gh')
        geo_cold = st.slider("北方水气 (North Cold)", 0.0, 0.5, mp['latitudeCold'], 0.1, key='mp_gc')
        
        c1, c2 = st.columns(2)
        with c1:
            inv_sea = st.toggle("南半球 (S.Hemi)", mp['invertSeasons'], key='mp_is')
        with c2:
            use_st = st.toggle("真太阳时 (True Solar)", mp['useSolarTime'], key='mp_st')

    # === 应用并回测按钮 ===
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 应用并回测 (Apply V7.3)", type="primary", width='stretch'):
        # 构建算法核心配置 (V6 Legacy Flat - Partial Map)
        algo_config = {
            'score_skull_crash': score_skull_crash,
            'score_treasury_bonus': score_treasury_bonus,
            'score_treasury_penalty': score_treasury_penalty,
            'score_general_open': score_general_open,
            'score_sanhe_bonus': score_sanhe_bonus,
            'score_liuhe_bonus': score_liuhe_bonus,
            'score_clash_penalty': score_clash_penalty,
            'energy_threshold_strong': energy_strong,
            'energy_threshold_weak': energy_weak,
        }
        
        # [V2.5] 构建终极全量配置
        final_full_config = {
            "physics": {
                "seasonWeights": fp['physics']['seasonWeights'],
                "hiddenStemRatios": fp['physics']['hiddenStemRatios'],
                "pillarWeights": {
                    "year": pg_year, "month": pg_month, "day": pg_day, "hour": pg_hour
                },
                "lifeStageImpact": 0.2
            },
            "structure": {
                "rootingWeight": root_w,
                "exposedBoost": exposed_b,
                "samePillarBonus": same_pill,
                "voidPenalty": void_p
            },
            "interactions": {
                "stemFiveCombine": {
                    "threshold": s5_th, "bonus": s5_bo, "penalty": s5_pe,
                    "jealousyDamping": jealousy_d
                },
                "comboPhysics": {
                    "trineBonus": cp_tb, "halfBonus": cp_hb, "archBonus": 1.1,
                    "directionalBonus": cp_db, "resolutionCost": cp_rc
                },
                "branchEvents": {
                    "threeHarmony": score_sanhe_bonus,
                    "sixHarmony": score_liuhe_bonus,
                    "clashDamping": be_clash_d,
                    "clashScore": score_clash_penalty,
                    "harmDamping": 0.2
                },
                "vaultPhysics": {
                    "threshold": vp_th,
                    "sealedDamping": vp_sd,
                    "openBonus": vp_ob,
                    "breakPenalty": vp_bp,
                    "punishmentOpens": vp_po
                },
                "treasury": {"bonus": score_treasury_bonus},
                "skull": {"crashScore": score_skull_crash}
            },
            "flow": {
                "resourceImpedance": {"base": imp_base, "weaknessPenalty": imp_weak},
                "outputViscosity": {"maxDrainRate": vis_rate, "drainFriction": vis_fric},
                "globalEntropy": sys_ent,
                "controlImpact": ctl_imp,
                "spatialDecay": {"gap1": sp_g1, "gap2": sp_g2}
            },
            "spacetime": {
                "luckPillarWeight": lp_w,
                "solarTimeImpact": 0.0, # Deprecated by macroPhysics.useSolarTime
                "regionClimateImpact": 0.0
            },
            "macroPhysics": {
                "eraElement": era_el,
                "eraBonus": era_bon, "eraPenalty": era_pen,
                "latitudeHeat": geo_hot, "latitudeCold": geo_cold,
                "invertSeasons": inv_sea, "useSolarTime": use_st
            },
            "global_logic": fp['global_logic']
        }
        
        # 存入 session_state
        st.session_state['algo_config'] = algo_config
        st.session_state['full_algo_config'] = final_full_config
        st.toast(f"✅ V7.3 终极参数注入成功！Void Penalty = {void_p}")
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Global (原有参数)
    with st.sidebar.expander("📊 物理权重参数 (高级)", expanded=False):
        w_e_val = st.slider("We: 全局能量增益", 0.5, 2.0, fd.get('w_e', 1.0), 0.1)
        f_yy_val = st.slider("F(阴阳): 异性耦合效率", 0.8, 1.5, fd.get('f_yy', 1.1), 0.05)
        
        # Career
        st.markdown("**W_事业 (Career)**")
        w_career_officer = st.slider("W_官杀 (Officer)", 0.0, 1.0, fd.get('w_off', 0.8), 0.05)
        w_career_resource = st.slider("W_印星 (Resource)", 0.0, 1.0, fd.get('w_res', 0.1), 0.05)
        w_career_output = st.slider("W_食伤 (Tech)", 0.0, 1.0, fd.get('w_out_c', 0.0), 0.05)
        k_control = st.slider("K_制杀 (Control)", 0.0, 1.0, fd.get('k_ctl', 0.55))
        k_buffer = st.slider("K_化杀 (Buffer)", 0.0, 1.0, fd.get('k_buf', 0.40))
        k_mutiny = st.slider("K_伤官见官 (Mutiny)", 0.0, 3.0, fd.get('k_mut', 1.8))
        k_pressure = st.slider("K_官杀攻身 (Pressure)", 0.0, 2.0, fd.get('k_press', 1.0))

        # Wealth
        st.markdown("**W_财富 (Wealth)**")
        w_wealth_cai = st.slider("W_财星 (Wealth)", 0.0, 1.0, fd.get('w_cai', 0.6), 0.05)
        w_wealth_output = st.slider("W_食伤 (Source)", 0.0, 1.0, fd.get('w_out_w', 0.4), 0.05)
        k_capture = st.slider("K_身旺担财 (Capture)", 0.0, 0.5, fd.get('k_cap', 0.0), 0.05)
        k_leak = st.slider("K_身弱泄气 (Leak)", 0.0, 2.0, fd.get('k_leak', 0.87), 0.01)
        k_burden = st.slider("K_财多身弱 (Burden)", 0.5, 2.0, fd.get('k_bur', 1.0), 0.1)

        # Relationship
        st.markdown("**W_感情 (Relationship)**")
        w_rel_spouse = st.slider("W_配偶星 (Spouse)", 0.1, 1.0, fd.get('w_spouse', 0.35), 0.05)
        w_rel_self = st.slider("W_日主 (Self)", -0.5, 0.5, fd.get('w_self', 0.20), 0.05)
        w_rel_output = st.slider("W_食伤 (Output)", 0.0, 1.0, fd.get('w_out_r', 0.15), 0.05)
        k_clash = st.slider("K_比劫夺财 (Clash)", 0.0, 2.0, fd.get('k_clash', 1.2), 0.1)

        # Advanced Logic
        st.markdown("**🚩 逻辑开关**")
        k_broken = st.slider("K_假从崩塌 (Broken)", 1.0, 3.0, fd.get('k_brk', 1.5), 0.1)
        enable_mediation = st.checkbox("通关豁免 (Mediation)", fd.get('en_med', True))
        enable_structural = st.checkbox("地支互斥 (Structural)", fd.get('en_str', True))
    
    current_params = {
        "w_e_weight": w_e_val,
        "f_yy_correction": f_yy_val,
        
        "w_career_officer": w_career_officer,
        "w_career_resource": w_career_resource,
        "w_career_output": w_career_output,
        "k_control": k_control,
        "k_buffer": k_buffer,
        "k_mutiny": k_mutiny,
        "k_pressure": k_pressure,
        
        "w_wealth_cai": w_wealth_cai,
        "w_wealth_output": w_wealth_output,
        "k_capture": k_capture,
        "k_leak": k_leak,
        "k_burden": k_burden,

        "w_rel_spouse": w_rel_spouse,
        "w_rel_self": w_rel_self,
        "w_rel_output": w_rel_output,
        "k_clash": k_clash,
        
        "k_broken": k_broken,
        "enable_mediation_exemption": enable_mediation,
        "enable_structural_clash": enable_structural,
        
        # === V6.0+ 新增算法核心参数 ===
        "score_skull_crash": score_skull_crash,
        "score_treasury_bonus": score_treasury_bonus,
        "score_treasury_penalty": score_treasury_penalty,
        "score_general_open": score_general_open,
        "energy_threshold_strong": energy_strong,
        "energy_threshold_weak": energy_weak,
    }
    
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 保存现有配置 (Save)"):
        save_params_to_disk(current_params)

    # --- MAIN ENGINE SETUP ---
    # V9.5 MVC Note: This is a Calibration Tool requiring direct engine access.
    engine = QuantumEngine()  # V9.1: Direct access for advanced tuning
    
    # V10.0: Unified input panel (P2 lab allows ERA tuning)
    controller = BaziController()
    selected_case, era_factor, city_for_controller = render_and_collect_input(controller, is_quantum_lab=True)
    
    # === V6.0+ 热更新：从 session_state 读取并应用算法配置 ===
    if 'algo_config' in st.session_state:
        engine.update_config(st.session_state['algo_config'])
        
    if 'full_algo_config' in st.session_state:
        engine.update_full_config(st.session_state['full_algo_config'])

    # --- UI HEADER ---
    st.title("🧪 量子八字 V8.0 验证工作台 (Phase Change)")
    st.markdown("Dynamic Space-Time Validation Module (Unified Arch)")
    st.caption(f"🔧 Engine Version: `{engine.VERSION}` (Modular)")

    # --- TABS ---
    tab_global, tab_single  = st.tabs(["🔭 全局校准 (Global Telescope)", "🔬 单点分析 (Single Microscope)"])

    # ==========================
    # TAB 1: GLOBAL TELESCOPE
    # ==========================
    with tab_global:
        st.subheader("全局调校控制台 (Global Calibration Console)")
        st.caption("批量验证所有案例的准确率 (Batch Accuracy Check)")
        
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
                        
                        profile = create_profile_from_case(c, luck_p)
                        
                        # 2. Evaluate Base Strength
                        # We need to use engine._evaluate_wang_shuai(dm, pillars)
                        bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                        
                        # Catch errors
                        try:
                            # IMPORTANT: evaluate_wang_shuai returns (strength_str, score)
                            ws_tuple = engine._evaluate_wang_shuai(profile.day_master, bazi_list)
                            comp_str = ws_tuple[0] # e.g. "Strong"
                            comp_score = ws_tuple[1]
                        except Exception as e:
                            comp_str = "Error"
                            comp_score = 0.0
                        
                        # 3. Verify
                        target_str = gt.get('strength', 'Unknown')
                        is_match = False
                        
                        if target_str != "Unknown":
                            # Loose Match
                            # If target is "Strong", comp should contain "Strong"
                            if (target_str in comp_str) or (comp_str in target_str):
                                is_match = True
                            # Follower handling
                            if "Follower" in target_str and "Follower" in comp_str:
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
    # TAB 2: SINGLE MICROSCOPE
    # ==========================
    with tab_single:
        st.subheader("🔬 案例实战验证 (Live Case Verification)")
        
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
                    case_idx = st.selectbox("📂 选择案例", range(len(cases)), format_func=lambda i: f"No.{cases[i]['id']} {cases[i]['day_master']}日主 ({cases[i]['gender']})")
                    selected_case = cases[case_idx]
                    
                with c_ctx:
                    presets = selected_case.get("dynamic_checks", [])
                    c_y, c_l = st.columns(2)
                    def_year = presets[0]['year'] if presets else "甲辰"
                    def_luck = presets[0]['luck'] if presets else "癸卯"
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
                    # Use engine to generate chart
                    res = engine.calculate_chart(req)
                    
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
            st.info(f"Analyzing Case: {selected_case['bazi']}")
            profile = create_profile_from_case(selected_case, user_luck)
            
            # Patch Engine Year to user input
            original_get_year = engine.get_year_pillar
            engine.get_year_pillar = lambda y: user_year
            
            try:
                # Call HIGH LEVEL context for the display
                ctx = engine.calculate_year_context(profile, 2024)
                
                # Call Low Level Engine directly to get Pillar Energies
                # 1. Mock case_data (similar to how calculate_year_context constructs it)
                # Handle VirtualProfile (Legacy/Test mode) without birth_date
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
                     ws, _ = engine._evaluate_wang_shuai(profile.day_master, bazi_list)
                     wang_shuai_str = "身旺" if "Strong" in ws else "身弱"
                except: pass

                case_data_mock = {
                    'id': selected_case.get('id', 999), 
                    'gender': selected_case.get('gender', '男'),
                    'day_master': profile.day_master,
                    'wang_shuai': wang_shuai_str,
                    'bazi': bazi_list,
                    'birth_info': birth_info_mock
                }
                
                # 2. Dynamic Context
                dyn_ctx_mock = {
                    'year': user_year,
                    'dayun': user_luck,
                    'luck': user_luck
                }
                
                # 3. Call Physics Engine
                detailed_res = engine.calculate_energy(case_data_mock, dyn_ctx_mock)
                
            finally:
                engine.get_year_pillar = original_get_year
            
            
            # Map to format compatible with UI
            pred_res = {
                'career': detailed_res['career'],
                'wealth': detailed_res['wealth'],
                'relationship': detailed_res['relationship'],
                'desc': ctx.narrative_prompt, # Use the rich prompt
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
            gt = selected_case.get('ground_truth')
            if gt:
                st.markdown("### 🧬 核心算法拟合度 (Algorithm Fit)")
                
                # Computed Strength
                # ws variable comes from try-catch block above (ensure it is accessible)
                comp_ws_raw = ws if 'ws' in locals() else "Unknown"
                
                # Match Logic
                # gt['strength'] e.g. "Strong", "Weak"
                is_match = False
                if gt['strength'] != "Unknown":
                    # Loose matching
                    is_match = (gt['strength'] in comp_ws_raw) or (comp_ws_raw in gt['strength'])
                    
                    # Special handling for "Follower"
                    if "Follower" in gt['strength'] and "Follower" in comp_ws_raw: is_match = True
                
                c_ver, c_det = st.columns([1, 3])
                with c_ver:
                    if is_match:
                        st.success(f"MATCH ✅\n{comp_ws_raw}")
                    else:
                        st.error(f"MISMATCH ❌\nGot: {comp_ws_raw}")
                        
                with c_det:
                    st.caption(f"Target: **{gt.get('strength', '?')}** | Note: {gt.get('note', '')}")
                    if 'favorable' in gt:
                        # Extract Computed Fav
                        # detailed_res doesn't explicitly return fav elements list easily here 
                        # but engine.calculate_chart does. 
                        # Here we called calculate_energy directly.
                        # However, we can access favorable from profile? No, profile is simple object.
                        # But wait, create_profile_from_case doesn't store favorable.
                        # We can re-run simple element check or assume fit based on strength.
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
            st.markdown("#### 结果分析")
            c_res, c_real, c_chart = st.columns([1, 1, 2])
            
            with c_res:
                st.info(f"AI 判词: {pred_res['desc']}")
                st.write(f"💼 事业: **{pred_res['career']:.1f}**")
                st.write(f"💰 财富: **{pred_res['wealth']:.1f}**")
                st.write(f"❤️ 感情: **{pred_res['relationship']:.1f}**")

            target_v_real = selected_case.get("truth_scores", {}) or selected_case.get("v_real", {})
            expert_note = ""
            preset_match = next((p for p in presets if p['year'] == user_year), None)
            if preset_match:
                target_v_real = preset_match['v_real_dynamic']
                expert_note = preset_match.get('note', '')

            with c_real:
                st.success("专家真值" + (f" ({expert_note})" if expert_note else ""))
                st.write(f"Career: {target_v_real.get('career', '?')}")
                st.write(f"Wealth: {target_v_real.get('wealth', '?')}")
                st.write(f"Rel: {target_v_real.get('relationship', '?')}")

            with c_chart:
                cats = ["事业", "财富", "感情"]
                try:
                    y_r = [float(target_v_real.get('career', 0)), float(target_v_real.get('wealth', 0)), float(target_v_real.get('relationship', 0))]
                except: y_r = [0,0,0]
                y_p = [pred_res['career'], pred_res['wealth'], pred_res['relationship']]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=cats, y=y_r, name='Real', line=dict(color='#00FF00', width=3)))
                fig.add_trace(go.Scatter(x=cats, y=y_p, name='AI', line=dict(color='#00BFFF', dash='dash', width=3)))
                fig.update_layout(height=250, margin=dict(t=10,b=10))
                st.plotly_chart(fig, width='stretch')

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
                # Simulation Engine needs same patching
                sim_engine = QuantumEngine()
                if 'full_algo_config' in st.session_state:
                     sim_engine.update_full_config(st.session_state['full_algo_config'])
                
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
                    
                    # Estimate Wang Shuai for simulation
                    try:
                        ws_sim, _ = sim_engine._evaluate_wang_shuai(profile.day_master, bazi_list)
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
                    
                    # Call Physics Engine (V6.0 Low Level)
                    det_res = sim_engine.calculate_energy(case_data_sim, dyn_ctx_sim)

                    sim_data.append({
                        "year": y,
                        "career": det_res['career'],
                        "wealth": det_res['wealth'],
                        "rel": det_res['relationship'],
                        "desc": det_res['desc']
                    })
                
                sdf = pd.DataFrame(sim_data)
                fig_t = go.Figure()
                fig_t.add_trace(go.Scatter(x=sdf['year'], y=sdf['career'], name='Career'))
                fig_t.add_trace(go.Scatter(x=sdf['year'], y=sdf['wealth'], name='Wealth'))
                fig_t.add_trace(go.Scatter(x=sdf['year'], y=sdf['rel'], name='Rel'))
                fig_t.update_layout(height=300, title="未来趋势")
                st.plotly_chart(fig_t, width='stretch')

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
                        
                        # Plot comparison chart
                        st.markdown("#### 📈 能量轨迹对比图")
                        
                        fig_geo = go.Figure()
                        
                        # Baseline trajectories
                        if 'baseline_career' in comparison_df.columns:
                            fig_geo.add_trace(go.Scatter(
                                x=comparison_df['year'],
                                y=comparison_df['baseline_career'],
                                name='Baseline Career',
                                line=dict(color='#00BFFF', width=2, dash='dash')
                            ))
                            fig_geo.add_trace(go.Scatter(
                                x=comparison_df['year'],
                                y=comparison_df['baseline_wealth'],
                                name='Baseline Wealth',
                                line=dict(color='#00BFFF', width=2, dash='dash')
                            ))
                            fig_geo.add_trace(go.Scatter(
                                x=comparison_df['year'],
                                y=comparison_df['baseline_relationship'],
                                name='Baseline Relationship',
                                line=dict(color='#00BFFF', width=2, dash='dash')
                            ))
                        
                        # GEO-corrected trajectories
                        if 'geo_career' in comparison_df.columns:
                            fig_geo.add_trace(go.Scatter(
                                x=comparison_df['year'],
                                y=comparison_df['geo_career'],
                                name=f'{comparison_city} Career',
                                line=dict(color='#FF6B6B', width=3)
                            ))
                            fig_geo.add_trace(go.Scatter(
                                x=comparison_df['year'],
                                y=comparison_df['geo_wealth'],
                                name=f'{comparison_city} Wealth',
                                line=dict(color='#FF6B6B', width=3)
                            ))
                            fig_geo.add_trace(go.Scatter(
                                x=comparison_df['year'],
                                y=comparison_df['geo_relationship'],
                                name=f'{comparison_city} Relationship',
                                line=dict(color='#FF6B6B', width=3)
                            ))
                        
                        fig_geo.update_layout(
                            height=400,
                            title=f"GEO-Corrected Trajectory in {comparison_city}",
                            xaxis_title="Year",
                            yaxis_title="Energy Score",
                            hovermode='x unified',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig_geo, width='stretch')
                        
                        # Display data table
                        with st.expander("📋 详细数据表 (Detailed Data Table)"):
                            st.dataframe(comparison_df, width='stretch')
                        
                        st.success("✅ GEO 能量轨迹对比图已生成。")
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
