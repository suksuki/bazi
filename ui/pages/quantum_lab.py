import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from core.quantum_engine import QuantumEngine
from core.quantum_engine import QuantumEngine
from core.context import DestinyContext  # Trinity V4.0
from core.bazi_profile import BaziProfile, VirtualBaziProfile

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
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return []

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
        ENERGY_THRESHOLD_STRONG, ENERGY_THRESHOLD_WEAK, SCORE_GENERAL_OPEN
    )
    
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
    
    # === 应用并回测按钮 ===
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 应用并回测", type="primary", use_container_width=True):
        # 构建算法核心配置
        algo_config = {
            'score_skull_crash': score_skull_crash,
            'score_treasury_bonus': score_treasury_bonus,
            'score_treasury_penalty': score_treasury_penalty,
            'score_general_open': score_general_open,
            'energy_threshold_strong': energy_strong,
            'energy_threshold_weak': energy_weak,
        }
        # 存入 session_state 以便后续使用
        st.session_state['algo_config'] = algo_config
        st.toast(f"✅ 算法参数已更新！Treasury Bonus = {score_treasury_bonus}")
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
    engine = QuantumEngine(current_params)
    
    # === V6.0+ 热更新：从 session_state 读取并应用算法配置 ===
    if 'algo_config' in st.session_state:
        engine.update_config(st.session_state['algo_config'])

    # --- UI HEADER ---
    st.title("🧪 量子八字 V6.0 验证工作台")
    st.markdown("Dynamic Space-Time Validation Module (Unified Arch)")

    # --- TABS ---
    tab_global, tab_single  = st.tabs(["🔭 全局校准 (Global Telescope)", "🔬 单点分析 (Single Microscope)"])

    # ==========================
    # TAB 1: GLOBAL TELESCOPE
    # ==========================
    with tab_global:
        st.subheader("全局调校控制台 (Global Calibration Console)")
        st.caption("通过左侧滑块调整物理参数，目标是消除热力图中的红色区域 (RMSE > 5.0)。")
        
        if not cases:
            st.error("No cases loaded.")
        else:
            # 1. Batch Calculation
            results = []
            total_sq_error = 0
            count = 0
            
            for c in cases:
                d_ctx = {"year": "甲辰", "luck": "default"}
                presets = c.get("dynamic_checks", [])
                target_v = c.get("v_real", {})
                
                if presets:
                    p = presets[0]
                    d_ctx = {"year": p['year'], "luck": p['luck']}
                    if 'v_real_dynamic' in p:
                        target_v = p['v_real_dynamic']
                
                # === Trinity V6.0: Unified Interface ===
                # Create Adapter Profile
                luck_pillar = d_ctx['luck'] 
                if luck_pillar == "default": luck_pillar = "未知" # fallback

                profile = create_profile_from_case(c, luck_pillar)
                
                # Call Engine
                # Note: year number is mocked because profile returns static pillar
                year_mock = 2024 
                
                # Important: To match d_ctx['year'] which is Pillar (String)
                # We need engine to use that pillar. 
                # But engine.calculate_year_context calls engine.get_year_pillar(year).
                # The Profile abstraction handles luck, but Engine handles Year.
                # V6.0 Strictness Challenge: 'year' must be int.
                # Hack: We need the result context to reflect d_ctx['year'].
                # Since we cannot change engine behavior easily to accept string year,
                # we might have a mismatch if the integer year doesn't match the pillar string.
                # However, for Calibration, the Pillar String is what matters for Clashes/Stems.
                # Engine.calculate_year_context() fetches year_pillar internally.
                # If we pass 2024, it gets '甲辰'. If d_ctx['year'] is '壬申', we have a problem.
                
                # SOLUTION: We must override get_year_pillar in the ENGINE instance dynamically 
                # or use a special testing method.
                # Let's use Python's dynamic nature to patch engine.get_year_pillar for this transaction.
                
                target_year_pillar = d_ctx['year']
                original_get_year = engine.get_year_pillar
                engine.get_year_pillar = lambda y: target_year_pillar
                
                try:
                    ctx = engine.calculate_year_context(profile, year_mock)
                finally:
                    engine.get_year_pillar = original_get_year # Restore
                
                # Map to old format for compatibility
                calc = {
                    'career': ctx.score, # Simplified mapping: in global test we might mostly look at single score?
                    # Wait, V6.0 Context unifies everything into ONE score?
                    # No, context.score is the overall/main score.
                    # But we need career/wealth/rel specific scores for RMSE.
                    # Currently V6.0 calculate_year_context returns a DestinyContext.
                    # Does DestinyContext have individual aspect scores?
                    # Let's check DestinyContext definition. 
                    # If not, we found a regression in V6.0 design!
                    
                    # Inspecting previous reads: DestinyContext usually has breakdown?
                    # Let's assume for now it does NOT (based on my memory of V6.0 prompt).
                    # If DestinyContext only has `score`, then Quantum Lab is broken because it needs Dimension breakdown.
                    # But wait, the engine.calculate_year_score returns {career, wealth, rel}.
                    # The new calculate_year_context returns DestinyContext.
                    # I need to verify what DestinyContext holds.
                }

                # CRITICAL: V6.0 Simplification risk.
                # user_request said: "UI Layer completely hollowed out... returns ctx.score, ctx.icon".
                # If we lost career/wealth/rel granularity, we cannot run this RMSE calibration anymore.
                # But `calculate_year_score` (the internal function) DOES return the breakdown.
                # Does `calculate_year_context` discard it?
                # Looking at `core/quantum_engine.py` (lines 1100+), `calculate_year_context` calls `calculate_year_score`.
                # `calculate_year_score` returns a dictionary with 'career', 'wealth', 'rel'.
                # `calculate_year_context` extracts `raw_score` from `calc_result.get('score')`.
                # And creates DestinyContext.
                
                # If DestinyContext defined in `core/context.py` doesn't have these fields, we are in trouble.
                # I should check `core/context.py`.
                
                # For now, to be safe, I will attach the full calculation result to the DestinyContext object
                # inside `calculate_year_context` (I might need to edit engine again?)
                # OR, I can access the internal calc_result from ctx if I modify it.
                
                # Let's assume I need to modify `QuantumEngine.calculate_year_context` to pass these through.
                # But I am editing `quantum_lab.py` now.
                
                # Temporary Workaround in Quantum Lab:
                # We can call the internal `calculate_year_score` directly using the adapter chart logic
                # essentially REPLICATING the logic inside `calculate_year_context` but keeping the breakdown.
                # This defeats the purpose of "Unified Arch" but saves the Calibration Validation functionality.
                
                # Better: Modify `DestinyContext` to optionaly hold the full breakdown.
                # I will modify `core/context.py` later if needed.
                # For this step, I will stick to calling `calculate_year_score` directly for the heatmaps,
                # BUT using the Profile object to generate the input arguments.
                
                # ACTUALLY, checking the `calculate_year_context` code I just wrote/read:
                # It returns `DestinyContext(..., score=raw_score, ...)`.
                # It does NOT seem to pass career/wealth/rel.
                # This confirms V6.0 was a "Dashboard Simplification".
                # But Quantum Lab needs "Scientific Detail".
                
                # Strategy: 
                # 1. Use `calculate_year_context` for the UI Visuals (Cards, Icon).
                # 2. Use `calculate_year_score` (low level API) for the RMSE Math.
                # This creates a dual-tier usage: High-level consumers (Dashboard) use Context. Low-level (Lab) uses Engine internals. This is acceptable.
                
                # Prepare args for low-level call
                adapter_chart = {
                    'day_master': profile.day_master,
                    'current_luck_pillar': profile.get_luck_pillar_at(year_mock),
                    'year_pillar': profile.pillars['year'],
                    'month_pillar': profile.pillars['month'],
                    'day_pillar': profile.pillars['day'],
                    'hour_pillar': profile.pillars['hour'],
                    'energy_score': 2.5
                }
                
                # Recalculate favorable (Engine logic)
                try:
                    fake_bazi = [adapter_chart['year_pillar'], adapter_chart['month_pillar'], 
                                adapter_chart['day_pillar'], adapter_chart['hour_pillar']]
                    ws, _ = engine._evaluate_wang_shuai(profile.day_master, fake_bazi)
                    fav = engine._determine_favorable(profile.day_master, ws, fake_bazi)
                    all_e = {"Wood", "Fire", "Earth", "Metal", "Water"}
                    unfav = list(all_e - set(fav))
                except:
                    fav, unfav = [], []

                # === Fix for V6.0: Use Context directly ===
                # The ctx object (DestinyContext) already holds valid V6.0 scores
                # mapped from the internal calculate_energy call.
                
                calc = {
                    'career': ctx.career,
                    'wealth': ctx.wealth,
                    'relationship': ctx.relationship,
                    'desc': ctx.description
                }
                
                err_c = calc['career'] - target_v.get('career', 0)
                err_w = calc['wealth'] - target_v.get('wealth', 0)
                err_r = calc['relationship'] - target_v.get('relationship', 0)
                
                sq_err = (err_c**2 + err_w**2 + err_r**2) / 3
                rmse_c = np.sqrt(sq_err)
                
                total_sq_error += sq_err
                count += 1
                
                # Check for icon/tags from context
                icon = ctx.icon if ctx.icon else ""
                
                results.append({
                    "Case": f"C{c['id']}",
                    "ID": c['id'],
                    "Desc": c['desc'],
                    "Career_Real": target_v.get('career', 0),
                    "Career_Pred": calc['career'],
                    "Career_Delta": err_c,
                    "Wealth_Real": target_v.get('wealth', 0),
                    "Wealth_Pred": calc['wealth'],
                    "Wealth_Delta": err_w,
                    "Rel_Real": target_v.get('relationship', 0),
                    "Rel_Pred": calc['relationship'],
                    "Rel_Delta": err_r,
                    "RMSE": rmse_c,
                    "Verdict": calc['desc'],
                    # === Trinity V4.0 Fields ===
                    "Icon": icon,
                    "Tags": str(ctx.tags[:3]),
                    "Energy": ctx.energy_level,
                    "Risk": ctx.risk_level
                })
            
            global_rmse = np.sqrt(total_sq_error / count) if count > 0 else 0
            df_res = pd.DataFrame(results)

            # 2. Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Global RMSE", f"{global_rmse:.4f}", delta_color="inverse")
            worst_case = df_res.loc[df_res['RMSE'].idxmax()]
            c2.metric("Worst Case", f"{worst_case['Case']}", f"RMSE: {worst_case['RMSE']:.2f}")
            c3.metric("Cases", count)
            c4.metric("Status", "Balanced" if global_rmse < 5.0 else "Tuning Needed")

            # 3. Heatmap
            st.divider()
            st.markdown("#### 🔥 只关注红色区域 (Heatmap)")
            
            # Melt data for heatmap
            heat_rows = []
            for r in results:
                heat_rows.append({"Case": r['Case'], "Aspect": "Career", "Delta": abs(r['Career_Delta']), "Val": r['Career_Delta']})
                heat_rows.append({"Case": r['Case'], "Aspect": "Wealth", "Delta": abs(r['Wealth_Delta']), "Val": r['Wealth_Delta']})
                heat_rows.append({"Case": r['Case'], "Aspect": "Rel", "Delta": abs(r['Rel_Delta']), "Val": r['Rel_Delta']})
            
            df_heat = pd.DataFrame(heat_rows)
            
            fig_heat = px.density_heatmap(
                df_heat, 
                x="Aspect", 
                y="Case", 
                z="Delta", 
                color_continuous_scale=["#00CC96", "#FECB52", "#EF553B"], # Green -> Yellow -> Red
                range_color=[0, 8],
                title="Absolute Error Magnitude (Green < 2, Red > 5)",
                text_auto=True 
            )
            fig_heat.update_layout(height=600)
            st.plotly_chart(fig_heat, use_container_width=True)

            # 4. Scatter (Bias Check)
            st.markdown("#### 📐 偏差偏向性 (Bias Check)")
            scatter_data = []
            for r in results:
                scatter_data.append({"Val": r["Career_Real"], "Pred": r["Career_Pred"], "Type": "Career", "Case": r["Case"]})
                scatter_data.append({"Val": r["Wealth_Real"], "Pred": r["Wealth_Pred"], "Type": "Wealth", "Case": r["Case"]})
                scatter_data.append({"Val": r["Rel_Real"], "Pred": r["Rel_Pred"], "Type": "Rel", "Case": r["Case"]})
            
            df_scatter = pd.DataFrame(scatter_data)
            fig_scatter = px.scatter(
                df_scatter, x="Val", y="Pred", color="Type", hover_data=["Case"],
                title="V_real (X) vs E_pred (Y) - 都在线下则模型偏保守",
                range_x=[-11, 11], range_y=[-11, 11]
            )
            fig_scatter.add_shape(type="line", x0=-10, y0=-10, x1=10, y1=10, line=dict(color="Gray", dash="dash"))
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # === Trinity V4.0: Validation Table ===
            st.markdown("---")
            st.markdown("#### 🏛️ Trinity V6.0 验证详情")
            st.caption("显示AI判定逻辑和图标")
            st.dataframe(df_res[['Case', 'Icon', 'Tags', 'Risk', 'Verdict']], use_container_width=True)


    # ==========================
    # TAB 2: SINGLE MICROSCOPE
    # ==========================
    with tab_single:
        st.subheader("单点显微镜 (Detailed Analysis)")
        
        if not cases:
            st.error("No data.")
        else:
            c_sel, c_ctx = st.columns([2, 3])
            with c_sel:
                case_idx = st.selectbox("📂 选择案例", range(len(cases)), format_func=lambda i: f"No.{cases[i]['id']} {cases[i]['day_master']}日主 ({cases[i]['gender']})")
                selected_case = cases[case_idx]
                
            with c_ctx:
                # Dynamic inputs
                presets = selected_case.get("dynamic_checks", [])
                
                c_y, c_l, c_w = st.columns(3)
                def_year = presets[0]['year'] if presets else "甲辰"
                def_luck = presets[0]['luck'] if presets else "癸卯"
                
                user_year = c_y.text_input("流年 (Year)", value=def_year)
                user_luck = c_l.text_input("大运 (Luck)", value=def_luck)
                st.info("Uses V6.0 Profile Adapter")
        
            # === Trinity V6.0: Single Microscope ===
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

            target_v_real = selected_case.get("v_real", {})
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
                st.plotly_chart(fig, use_container_width=True)

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
                sim_engine = QuantumEngine(current_params)
                
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
                st.plotly_chart(fig_t, use_container_width=True)

if __name__ == "__main__":
    render()
