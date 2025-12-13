import streamlit as st
import datetime
import json
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go # Fix: Import globally

# Core Imports
from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.quantum_engine import QuantumEngine # V2.9 Quantum Physics Engine
from learning.db import LearningDB
from core.interactions import get_stem_interaction, get_branch_interaction
from core.bazi_profile import BaziProfile

# --- Component: Narrative Card Renderer (V2.9) ---
def render_narrative_card(event):
    """
    Renders a single narrative card based on the event payload.
    Uses Quantum Glassmorphism styles.
    """
    ctype = event.get('card_type', 'default')
    
    # Map types to CSS classes and icons
    config = {
        "mountain_alliance": {"css": "card-mountain", "icon": "⛰️", "icon_css": "icon-mountain"},
        "penalty_cap": {"css": "card-shield", "icon": "🛡️", "icon_css": "icon-shield"},
        "mediation": {"css": "card-flow", "icon": "🌊", "icon_css": "icon-flow"},
        "pressure": {"css": "card-danger", "icon": "⚠️", "icon_css": ""},
        "control": {"css": "card-flow", "icon": "⚡", "icon_css": "icon-flow"}, # Re-use flow for control
        "default": {"css": "", "icon": "📜", "icon_css": ""}
    }
    
    cfg = config.get(ctype, config.get(event.get('type'), config['default'])) # Fallback to 'type' key if 'card_type' missing
    
    # Generate HTML
    html = f"""
    <div class="narrative-card {cfg['css']}">
        <div style="display: flex; align-items: start; gap: 16px;">
            <div class="{cfg['icon_css']}">{cfg['icon']}</div>
            <div style="flex-grow: 1;">
                <div class="card-title">{event.get('title', 'Unknown Event')}</div>
                <div class="card-subtitle">{event.get('desc', '')}</div>
                <div class="card-impact">{event.get('score_delta', '')}</div>
            </div>
        </div>
        <!-- Visualization Placeholder -->
        <div style="position: absolute; right: 10px; top: 10px; opacity: 0.1;">
            <span style="font-size: 60px;">{cfg['icon']}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_prediction_dashboard():
    """
    Renders the V2.4 Pure Prediction Dashboard.
    Focuses solely on Quantum Physics Logic.
    """
    # 0. Inputs (Session State)
    name = st.session_state.get('input_name', '某人')
    gender = st.session_state.get('input_gender', '男')
    d = st.session_state.get('input_date', datetime.date(1990, 1, 1))
    t = st.session_state.get('input_time', 12)
    
    # 1. Basic Calculation (The Chart)
    enable_solar = st.session_state.get('input_enable_solar_time', True)
    longitude = st.session_state.get('input_longitude', 116.46) if enable_solar else 120.0
    
    calc = BaziCalculator(d.year, d.month, d.day, t, 0, longitude=longitude)
    chart = calc.get_chart()
    details = calc.get_details()
    
    # Luck Cycles
    gender_idx = 1 if "男" in gender else 0
    luck_cycles = calc.get_luck_cycles(gender_idx)
    
    # 2. UI: Header & Chart
    st.title(f"🔮 {name} 的量子命盘 (V5.3 Skull)")
    
    # --- V2.9 Glassmorphism CSS (Dark Mode) ---
    st.markdown("""
    <style>
    /* 1. Reset Global Background to Default */
    /* No .stApp override - let Streamlit use default or user preference, but we force containers to dark */

    /* 2. Card Container (Deep Space Dark) */
    .narrative-card {
        position: relative;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        background: #1e293b;
    }
    .narrative-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.5);
        border-color: #475569;
    }

    /* 3. Card Types / Themes (Dark Mode Adapted) */
    /* Mountain Alliance */
    .card-mountain {
        background: linear-gradient(to bottom right, #451a03, #1e293b);
        border-top: 3px solid #f59e0b;
    }
    .icon-mountain {
        font-size: 32px;
        color: #f59e0b;
    }

    /* Penalty Cap */
    .card-shield {
        background: linear-gradient(to bottom right, #0c4a6e, #1e293b);
        border-top: 3px solid #38bdf8;
    }
    .icon-shield {
        font-size: 32px;
        color: #38bdf8;
    }

    /* Mediation Flow */
    .card-flow {
        background: linear-gradient(to bottom right, #064e3b, #1e293b);
        border-top: 3px solid #34d399;
    }
    .icon-flow {
        font-size: 32px;
        color: #34d399;
    }

    /* Danger / Pressure */
    .card-danger {
        background: linear-gradient(to bottom right, #7f1d1d, #1e293b);
        border-top: 3px solid #f87171;
    }

    /* 4. Typography (Light Text) */
    .card-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 4px;
        color: #f1f5f9;
    }
    .card-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #94a3b8;
        margin-bottom: 12px;
    }
    .card-impact {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        padding: 4px 8px;
        border-radius: 4px;
        background: #334155;
        display: inline-block;
        color: #e2e8f0;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    
    # Helper: Quantum Theme System (Constitution V1.0)
    # Mapping "Forms" to Visuals (Icons + Animations + Gradients)
    
    QUANTUM_THEME = {
        # --- Wood (Growth / Networking) ---
        "甲": {"color": "#4ade80", "icon": "🌲", "anim": "pulse-grow", "grad": "linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d)"}, # Green 400
        "乙": {"color": "#86efac", "icon": "🌿", "anim": "sway", "grad": "linear-gradient(to top, #0ba360 0%, #3cba92 100%)"},
        "寅": {"color": "#22c55e", "icon": "🐅", "anim": "pulse-fast", "grad": "linear-gradient(to top, #09203f 0%, #537895 100%)"}, # Green 500
        "卯": {"color": "#a3e635", "icon": "🐇", "anim": "bounce", "grad": "linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%)"},

        # --- Fire (Radiation / Focus) ---
        "丙": {"color": "#fb923c", "icon": "☀️", "anim": "spin-slow", "grad": "radial-gradient(circle, #ff9966, #ff5e62)"}, # Orange 400
        "丁": {"color": "#f472b6", "icon": "🕯️", "anim": "flicker", "grad": "linear-gradient(to top, #f43b47 0%, #453a94 100%)"}, # Pink 400
        "巳": {"color": "#fdba74", "icon": "🐍", "anim": "slither", "grad": "linear-gradient(to right, #f83600 0%, #f9d423 100%)"},
        "午": {"color": "#f87171", "icon": "🐎", "anim": "gallop", "grad": "linear-gradient(to right, #ff8177 0%, #ff867a 0%, #ff8c7f 21%, #f99185 52%, #cf556c 78%, #b12a5b 100%)"}, # Red 400

        # --- Earth (Mass / Matrix) ---
        "戊": {"color": "#a8a29e", "icon": "🏔️", "anim": "stable", "grad": "linear-gradient(to top, #c79081 0%, #dfa579 100%)"}, # Stone 400
        "己": {"color": "#e7e5e4", "icon": "🧱", "anim": "stable", "grad": "linear-gradient(to top, #e6b980 0%, #eacda3 100%)"},
        "辰": {"color": "#84cc16", "icon": "🐲", "anim": "float", "grad": "linear-gradient(to top, #9be15d 0%, #00e3ae 100%)"}, 
        "戌": {"color": "#fda4af", "icon": "🌋", "anim": "rumble", "grad": "linear-gradient(to right, #434343 0%, black 100%)"}, 
        "丑": {"color": "#fde047", "icon": "🐂", "anim": "stable", "grad": "linear-gradient(to top, #50cc7f 0%, #f5d100 100%)"}, # Yellow 300
        "未": {"color": "#fdba74", "icon": "🐑", "anim": "stable", "grad": "linear-gradient(120deg, #f6d365 0%, #fda085 100%)"}, 

        # --- Metal (Impact / Order) ---
        "庚": {"color": "#cbd5e1", "icon": "⚔️", "anim": "flash", "grad": "linear-gradient(to top, #cfd9df 0%, #e2ebf0 100%)"}, # Slate 300
        "辛": {"color": "#fde047", "icon": "💎", "anim": "sparkle", "grad": "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)"}, # Gold
        "申": {"color": "#94a3b8", "icon": "🐵", "anim": "swing", "grad": "linear-gradient(to top, #30cfd0 0%, #330867 100%)"}, # Slate 400
        "酉": {"color": "#e2e8f0", "icon": "🐓", "anim": "strut", "grad": "linear-gradient(to top, #cd9cf2 0%, #f6f3ff 100%)"}, # Slate 200

        # --- Water (Flow / Permeability) ---
        "壬": {"color": "#38bdf8", "icon": "🌊", "anim": "wave", "grad": "linear-gradient(to top, #3b41c5 0%, #a981bb 49%, #ffc8a9 100%)"}, # Sky 400
        "癸": {"color": "#7dd3fc", "icon": "☁️", "anim": "drift", "grad": "linear-gradient(to top, #a18cd1 0%, #fbc2eb 100%)"}, # Sky 300
        "子": {"color": "#60a5fa", "icon": "🐀", "anim": "scurry", "grad": "linear-gradient(15deg, #13547a 0%, #80d0c7 100%)"}, # Blue 400
        "亥": {"color": "#818cf8", "icon": "🐖", "anim": "float", "grad": "linear-gradient(to top, #4fb576 0%, #44a08d 24%, #2b88aa 52%, #0f5f87 76%, #0d2f4a 100%)"}, # Indigo 400
    }

    def get_theme(char):
        return QUANTUM_THEME.get(char, {"color": "#FFF", "icon": "❓", "anim": "none", "grad": "none"})
    
    # Re-expose color for other functions
    def get_nature_color(char):
        return get_theme(char)["color"]

    # Prepare Data
    dm = chart.get('day', {}).get('stem')
    
    pillars = ['year', 'month', 'day', 'hour']
    labels = ["年柱 (Year)", "月柱 (Month)", "日柱 (Day)", "时柱 (Hour)"]
    
    # --- INJECT ADVANCED CSS ANIMATIONS ---
    st.markdown(f"""
    <style>
        /* --- Animations --- */
        @keyframes sway {{ 0% {{ transform: rotate(0deg); }} 25% {{ transform: rotate(5deg); }} 75% {{ transform: rotate(-5deg); }} 100% {{ transform: rotate(0deg); }} }}
        @keyframes pulse-grow {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} 100% {{ transform: scale(1); }} }}
        @keyframes flicker {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.8; transform: scale(0.98); }} 100% {{ opacity: 1; }} }}
        @keyframes spin-slow {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        @keyframes wave {{ 0% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} 100% {{ transform: translateY(0); }} }}
        @keyframes drift {{ 0% {{ transform: translateX(0); opacity: 0.8;}} 50% {{ transform: translateX(5px); opacity: 1;}} 100% {{ transform: translateX(0); opacity: 0.8;}} }}
        @keyframes sparkle {{ 0% {{ filter: brightness(100%); }} 50% {{ filter: brightness(130%); }} 100% {{ filter: brightness(100%); }} }}
        @keyframes flash {{ 0% {{ text-shadow: 0 0 5px #FFF; }} 50% {{ text-shadow: 0 0 20px #FFF; }} 100% {{ text-shadow: 0 0 5px #FFF; }} }}
        
        /* --- Card Styles --- */
        .pillar-card {{
            background: #1e293b;
            border-radius: 15px;
            padding: 10px;
            text-align: center;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }}
        .pillar-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0,0,0,0.5);
            border-color: #475569;
        }}
        .pillar-title {{
            font-size: 0.75em;
            color: #94a3b8;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        /* --- Quantum Token (The Character) --- */
        .quantum-token {{
            display: inline-block;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            margin: 5px auto;
            position: relative;
            
            /* Center Content */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5), 0 0 10px rgba(0,0,0,0.5);
            border: 2px solid rgba(255,255,255,0.1);
        }}
        
        .token-char {{
            font-size: 1.8em;
            font-weight: bold;
            color: #FFF;
            text-shadow: 0 2px 4px rgba(0,0,0,0.8);
            line-height: 1;
            z-index: 2;
        }}
        
        .token-icon {{
            font-size: 0.8em;
            position: absolute;
            top: 5px;
            right: 5px;
            filter: drop-shadow(0 0 2px rgba(0,0,0,0.8));
            z-index: 3;
        }}
        
        .hidden-stems {{
            font-size: 0.7em;
            color: #666;
            margin-top: 8px;
            font-family: monospace;
        }}
        
        .hidden-container {{
            display: flex;
            justify-content: center;
            gap: 6px; /* Space between quark particles */
            margin-top: 12px;
        }}
        
        .hidden-token {{
            width: 28px;
            height: 28px;
            border-radius: 50%; /* Perfect circle */
            font-size: 0.9em;
            font-weight: bold;
            color: #FFF;
            
            /* Centering */
            display: flex;
            align-items: center;
            justify-content: center;
            
            /* Quantum styling */
            box-shadow: 0 2px 4px rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.3);
            text-shadow: 0 1px 2px rgba(0,0,0,0.8);
            
            cursor: help;
            transition: transform 0.2s;
        }}
        
        .hidden-token:hover {{
            transform: scale(1.2) rotate(15deg);
            z-index: 10;
        }}
        
        .dm-glow {{
            box-shadow: 0 0 15px #FF4500, inset 0 0 10px #FF4500 !important;
            border: 2px solid #FF4500 !important;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Grid for True Four Pillars (4 Columns)
    cols = st.columns(4)
    
    for i, p_key in enumerate(pillars):
        p_data = chart.get(p_key, {})
        stem = p_data.get('stem', '?')
        branch = p_data.get('branch', '?')
        hidden = " ".join(p_data.get('hidden_stems', []))
        
        # Get Theme Data
        t_stem = get_theme(stem)
        t_branch = get_theme(branch)
        
        # Day Master Special Style
        dm_class = "dm-glow" if (p_key == 'day') else ""
        
        with cols[i]:
            # Render Stem Token
            
            # 1. Build Hidden Stems HTML (Core Particles)
            hidden_list = p_data.get('hidden_stems', [])
            hidden_html = '<div class="hidden-container">'
            for h_char in hidden_list:
                h_theme = get_theme(h_char)
                hidden_html += f'<div class="hidden-token" style="background: {h_theme["grad"]};" title="{h_char}">{h_char}</div>'
            hidden_html += '</div>'

            # 2. Render Card
            st.markdown(f"""<div class="pillar-card">
    <div class="pillar-title">{labels[i]}</div>
    <!-- Stem -->
    <div class="quantum-token {dm_class if i == 2 else ''}" style="background: {t_stem['grad']}; animation: {t_stem['anim']} 3s infinite alternate;">
        <div class="token-icon">{t_stem['icon']}</div>
        <div class="token-char">{stem}</div>
    </div>
    <!-- Branch -->
    <div class="quantum-token" style="background: {t_branch['grad']}; animation: {t_branch['anim']} 4s infinite alternate; margin-top: 10px;">
         <div class="token-icon">{t_branch['icon']}</div>
        <div class="token-char">{branch}</div>
    </div>
    <!-- Hidden Stems (Core Particles) -->
    {hidden_html}
</div>""", unsafe_allow_html=True)
            
    st.markdown("---")
    
    # 3. Time Machine (Dynamic Context)
    st.subheader("⏳ 时空控制台 (Time Machine)")
    
    current_year = datetime.datetime.now().year
    
    # Da Yun Selector
    c1, c2 = st.columns([2, 1])
    selected_yun = None
    current_gan_zhi = None # The active interaction pillar
    
    if luck_cycles:
        with c1:
            yun_options = [f"{c['start_year']}~{c['end_year']} ({c['start_age']}岁): {c['gan_zhi']}" for c in luck_cycles]
            default_idx = 0
            for i, c in enumerate(luck_cycles):
                if c['start_year'] <= current_year <= c['end_year']:
                    default_idx = i
                    break
            selected_yun_str = st.selectbox("当前大运 (Da Yun)", yun_options, index=default_idx)
            selected_yun = luck_cycles[yun_options.index(selected_yun_str)]
            
    # Liu Nian Selector
    with c2:
        sim_year = st.number_input("模拟流年 (Year)", min_value=1900, max_value=2100, value=current_year)
        # Calculate Liu Nian GanZhi
        base_year = 1924 # Jia Zi
        offset = sim_year - base_year
        gd = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        zhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        ln_gan = gd[offset % 10]
        ln_zhi = zhi[offset % 12]
        ln_gan_zhi = f"{ln_gan}{ln_zhi}"
        st.metric("流年", f"{sim_year} {ln_gan_zhi}")
        
    current_gan_zhi = ln_gan_zhi # Focus on Liu Nian for Physics
    
    # 4. Engine Execution (Flux -> Quantum V2.4)
    
    # A. FluxEngine (Sensor Layer)
    flux_engine = FluxEngine(chart)
    
    # Prepare Environment
    dy_dict = None
    if selected_yun:
        gz = selected_yun['gan_zhi']
        if len(gz) >= 2: dy_dict = {'stem': gz[0], 'branch': gz[1]}
        
    ln_dict = None
    if current_gan_zhi and len(current_gan_zhi) >= 2:
        ln_dict = {'stem': current_gan_zhi[0], 'branch': current_gan_zhi[1]}
        
    flux_engine.set_environment(dy_dict, ln_dict)
    
    # Run Calculation
    flux_data = flux_engine.compute_energy_state()
    dynamic_gods_map = flux_data
    
    # DEBUG: Inspect Flux Data
    with st.expander("🔍 DEBUG: Flux Data Output", expanded=False):
        st.write("Keys:", list(flux_data.keys()))
        if 'ZhengGuan' in flux_data:
            st.write("ZhengGuan Score:", flux_data['ZhengGuan'])
        elif 'ten_gods' in flux_data:
            st.write("Ten Gods found in sub-key 'ten_gods'")
            st.json(flux_data['ten_gods'])
        else:
            st.error("Ten Gods Keys MISSING from root!")
            st.json(flux_data)
    
    # -------------------------------------------------------------------------
    # UNIT: Quantum Engine Integration & Visualization (Aligns with Quantum Lab)
    # -------------------------------------------------------------------------
    
    # 1. Load Parameters (Golden Master V2.9)
    try:
        import os
        params_path = os.path.join(os.path.dirname(__file__), '../../data/golden_parameters.json')
        with open(params_path, 'r') as f:
            gp = json.load(f)
        
        # Pass the full configuration directly to QuantumEngine.
        # The engine's _flatten_params method will handle the nested structure 
        # (k_factors, logic_switches, weights, etc.) automatically.
        params = gp
        
    except Exception as e:
        st.error(f"Config Load Error: {e}")
        params = {} # Fallback to engine defaults

    # 2. Extract Data from Flux (Sensor) to feed Quantum Engine

    # 2. Extract Data from Flux (Sensor) to feed Quantum Engine
    scale = 0.08 
    dg = flux_data # Use Flux Data
    
    s_self = dg.get('BiJian', 0) + dg.get('JieCai', 0)
    s_output = dg.get('ShiShen', 0) + dg.get('ShangGuan', 0)
    s_wealth = dg.get('ZhengCai', 0) + dg.get('PianCai', 0)
    s_officer = dg.get('ZhengGuan', 0) + dg.get('QiSha', 0)
    s_resource = dg.get('ZhengYin', 0) + dg.get('PianYin', 0)
    
    est_self = s_self * scale
    
    final_self = est_self
    wang_shuai_str = "身中和"
    if est_self < 1.0:
        wang_shuai_str = "假从/极弱"
        final_self = est_self - 8.0 
    elif est_self < 3.5:
        wang_shuai_str = "身弱"
        final_self = est_self - 6.0 
    else:
        wang_shuai_str = "身旺"

    # Capture Pillar Energies
    pe_list = []
    p_order = ["year_stem", "year_branch", "month_stem", "month_branch", "day_stem", "day_branch", "hour_stem", "hour_branch"]
    for pid in p_order:
        val = 0.0
        for p in flux_engine.particles:
            if p.id == pid:
                val = p.wave.amplitude * scale # Apply Scaling to match Physics/TenGods magnitude
                break
        pe_list.append(round(val, 1))

    physics_sources = {
        'self': {'stem_support': final_self},
        'output': {'base': s_output * scale},
        'wealth': {'base': s_wealth * scale},
        'officer': {'base': s_officer * scale},
        'resource': {'base': s_resource * scale},
        'pillar_energies': pe_list # Inject Scaled Real Energies
    }
    
    # Construct Bazi List for Structural Clash Logic
    bazi_list = [
        f"{chart.get('year',{}).get('stem','')}{chart.get('year',{}).get('branch','')}",
        f"{chart.get('month',{}).get('stem','')}{chart.get('month',{}).get('branch','')}",
        f"{chart.get('day',{}).get('stem','')}{chart.get('day',{}).get('branch','')}",
        f"{chart.get('hour',{}).get('stem','')}{chart.get('hour',{}).get('branch','')}"
    ]

    case_data = {
        'id': 8888, 
        'gender': gender,
        'day_master': chart.get('day',{}).get('stem','?'),
        'wang_shuai': wang_shuai_str, 
        'physics_sources': physics_sources,
        'bazi': bazi_list, # Required for Structural/Harm Matrix
        # Sprint 5.4: 注入出生信息以支持动态大运
        'birth_info': {
            'year': d.year,
            'month': d.month,
            'day': d.day,
            'hour': t,
            'gender': 1 if "男" in gender else 0
        }
    }
    
    # 3. Execute Quantum Engine
    engine = QuantumEngine(params)
    dynamic_context = {'year': current_gan_zhi, 'dayun': selected_yun['gan_zhi'] if selected_yun else ''}
    results = engine.calculate_energy(case_data, dynamic_context)
    
    # 4. Render Interface (Quantum Lab Style)
    st.markdown("### 🏛️ 四柱能量 (Four Pillars Energy - Interaction Matrix)")
    pe = results.get('pillar_energies', [0]*8)
    
    y_s = chart.get('year',{}).get('stem','?')
    y_b = chart.get('year',{}).get('branch','?')
    m_s = chart.get('month',{}).get('stem','?')
    m_b = chart.get('month',{}).get('branch','?')
    d_s = chart.get('day',{}).get('stem','?')
    d_b = chart.get('day',{}).get('branch','?')
    h_s = chart.get('hour',{}).get('stem','?')
    h_b = chart.get('hour',{}).get('branch','?')
    
    l_s = selected_yun['gan_zhi'][0] if selected_yun else '?'
    l_b = selected_yun['gan_zhi'][1] if selected_yun else '?'
    
    n_s = current_gan_zhi[0] if current_gan_zhi else '?'
    n_b = current_gan_zhi[1] if current_gan_zhi else '?'
    
    # helper for interaction badges
    def fmt_int(txt):
        if not txt: return ""
        color = "#AAA"
        icon = "🔗"
        if "冲" in txt: 
            color = "#FF4500" # Red/Orange for Clash
            icon = "💥"
        elif "刑" in txt: 
            color = "#FFD700" # Gold for Punishment
            icon = "⚡"
        elif "害" in txt: 
            color = "#FF69B4" # Pink for Harm
            icon = "💔"
        elif "合" in txt: 
            color = "#00FF00" # Green for Combine
            icon = "🤝"
            
        return f"<div style='color:{color}; font-size:0.45em; border:1px solid {color}; border-radius:4px; padding:1px; margin-top:2px; display:inline-block;'>{icon} {txt}</div>"

    # Interactions relative to Day Pillar (Day Master / Day Branch)
    # Stems vs Day Stem
    i_y_s = fmt_int(get_stem_interaction(y_s, d_s))
    i_m_s = fmt_int(get_stem_interaction(m_s, d_s))
    i_h_s = fmt_int(get_stem_interaction(h_s, d_s))
    i_l_s = fmt_int(get_stem_interaction(l_s, d_s))
    i_n_s = fmt_int(get_stem_interaction(n_s, d_s))
    
    # Branches vs Day Branch
    i_y_b = fmt_int(get_branch_interaction(y_b, d_b))
    i_m_b = fmt_int(get_branch_interaction(m_b, d_b))
    i_h_b = fmt_int(get_branch_interaction(h_b, d_b))
    i_l_b = fmt_int(get_branch_interaction(l_b, d_b))
    i_n_b = fmt_int(get_branch_interaction(n_b, d_b))
    
    st.markdown(f"""
    <style>
        .bazi-box {{
            background-color: #1e293b;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #334155;
        }}
        .bazi-table {{
            width: 100%;
            table-layout: fixed;
            border-collapse: separate;
            border-spacing: 5px 0;
        }}
        .bazi-header {{
            font-size: 0.85em;
            color: #94a3b8;
            margin-bottom: 8px;
            display: inline-block;
            white-space: nowrap;
        }}
        /* Title Animations */
        .h-anim-year {{ animation: wave 3s ease-in-out infinite; color: #4ade80; }}
        .h-anim-month {{ animation: drift 5s ease-in-out infinite; color: #38bdf8; }}
        .h-anim-day {{ animation: pulse-grow 2.5s ease-in-out infinite; color: #fbbf24; font-weight: bold; }}
        .h-anim-hour {{ animation: sway 4s ease-in-out infinite; color: #c084fc; }}
        .h-anim-dayun {{ animation: wave 6s ease-in-out infinite alternate; color: #22d3ee; opacity: 0.9; }}
        .h-anim-liunian {{ animation: flash 3s ease-in-out infinite; color: #f472b6; }}
        /* Column Highlight for Day Master */
        .col-day {{
            background: #334155;
            border-radius: 8px;
        }}
        
        .stem {{
            font-size: 1.8em;
            font-weight: bold;
            color: #f1f5f9;
            line-height: 1.1;
        }}
        .branch {{
            font-size: 1.8em;
            font-weight: bold;
            color: #e2e8f0;
            line-height: 1.1;
        }}
        .day-master {{
            text-decoration: underline;
            text-decoration-color: #f97316;
            text-decoration-thickness: 3px;
        }}
        .energy-val {{
            font-size: 0.75em;
            color: #15803d; /* Safe Dark Green */
            font-family: 'Verdana', sans-serif;
            font-weight: 900;
            margin-top: -2px;
            margin-bottom: 2px;
        }}
        .energy-val-low {{
             font-size: 0.75em;
             color: #cbd5e1; /* Silver */
             font-family: 'Verdana', sans-serif;
             font-weight: bold;
             margin-top: -2px;
             margin-bottom: 2px;
        }}
        .int-container {{
            min-height: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        /* Dynamic Columns distinct style */
        .dynamic-col {{
            background: #0f172a;
            border-radius: 8px;
        }}
    </style>
    
    <div class="bazi-box">
        <table class="bazi-table">
            <tr>
                <td><div class="bazi-header h-anim-year">🌲 年柱 (Year)</div></td>
                <td><div class="bazi-header h-anim-month">🌤️ 月柱 (Month)</div></td>
                <td class="col-day"><div class="bazi-header h-anim-day">👑 日柱 (Day)</div></td>
                <td><div class="bazi-header h-anim-hour">🏹 时柱 (Hour)</div></td>
                <td style="width: 10px;"></td> <!-- Spacer -->
                <td class="dynamic-col"><div class="bazi-header h-anim-dayun">🛣️ 大运 (Dyn)</div></td>
                <td class="dynamic-col"><div class="bazi-header h-anim-liunian">🌊 流年 (Year)</div></td>
            </tr>
            <tr>
                <!-- Stems -->
                <td class="stem" style="color: {get_nature_color(y_s)}">
                    {y_s}
                    <div class="{ 'energy-val' if pe[0]>2 else 'energy-val-low'}">{pe[0]}</div>
                    <div class="int-container">{i_y_s}</div>
                </td>
                <td class="stem" style="color: {get_nature_color(m_s)}">
                    {m_s}
                    <div class="{ 'energy-val' if pe[2]>2 else 'energy-val-low'}">{pe[2]}</div>
                    <div class="int-container">{i_m_s}</div>
                </td>
                <td class="stem day-master col-day" style="color: {get_nature_color(d_s)}">
                    {d_s}
                    <div class="{ 'energy-val' if pe[4]>2 else 'energy-val-low'}">{pe[4]}</div>
                    <div class="int-container"><span style="font-size:0.4em; color:#666;">命主</span></div>
                </td>
                <td class="stem" style="color: {get_nature_color(h_s)}">
                    {h_s}
                    <div class="{ 'energy-val' if pe[6]>2 else 'energy-val-low'}">{pe[6]}</div>
                    <div class="int-container">{i_h_s}</div>
                </td>
                <td></td>
                <td class="stem dynamic-col" style="color: {get_nature_color(l_s)}">
                    {l_s}
                    <div style="font-size:0.5em; color:#888;">&nbsp;</div>
                    <div class="int-container">{i_l_s}</div>
                </td>
                <td class="stem dynamic-col" style="color: {get_nature_color(n_s)}">
                    {n_s}
                    <div style="font-size:0.5em; color:#888;">&nbsp;</div>
                    <div class="int-container">{i_n_s}</div>
                </td>
            </tr>
            <tr>
                <!-- Branches -->
                <td class="branch" style="color: {get_nature_color(y_b)}">
                    {y_b}
                    <div class="{ 'energy-val' if pe[1]>2 else 'energy-val-low'}">{pe[1]}</div>
                    <div class="int-container">{i_y_b}</div>
                </td>
                <td class="branch" style="color: {get_nature_color(m_b)}">
                    {m_b}
                    <div class="{ 'energy-val' if pe[3]>2 else 'energy-val-low'}">{pe[3]}</div>
                    <div class="int-container">{i_m_b}</div>
                </td>
                <td class="branch day-master col-day" style="color: {get_nature_color(d_b)}">
                    {d_b}
                    <div class="{ 'energy-val' if pe[5]>2 else 'energy-val-low'}">{pe[5]}</div>
                    <div class="int-container"><span style="font-size:0.4em; color:#666;">（坐）</span></div>
                </td>
                <td class="branch" style="color: {get_nature_color(h_b)}">
                    {h_b}
                    <div class="{ 'energy-val' if pe[7]>2 else 'energy-val-low'}">{pe[7]}</div>
                    <div class="int-container">{i_h_b}</div>
                </td>
                <td></td>
                <td class="branch dynamic-col" style="color: {get_nature_color(l_b)}">
                    {l_b}
                    <div style="font-size:0.5em; color:#888;">&nbsp;</div>
                    <div class="int-container">{i_l_b}</div>
                </td>
                <td class="branch dynamic-col" style="color: {get_nature_color(n_b)}">
                    {n_b}
                    <div style="font-size:0.5em; color:#888;">&nbsp;</div>
                    <div class="int-container">{i_n_b}</div>
                </td>
            </tr>
        </table>
        <div style="margin-top: 10px; font-size: 0.9em; color: #AAA;">
            旺衰判定: <span style="color: #FFF; font-weight: bold;">{wang_shuai_str}</span>
            <br>
            <span style="font-size: 0.8em; color: #666;">提示：🔗合 💥冲 ⚡刑 💔害 (相对于日柱)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 5. Ten Gods Stats (Using Flux Data directly for Display Consistency)
    st.subheader("1.5. 十神能量分布 (Ten Gods Stats)")
    
    # Use Flux Data Scaled (Real Quantity) instead of Engine Logic (Physics Polarity)
    # This prevents '0' values for Weak Self and keeps scale consistent with Pillars
    
    # Metadata for Lively Descriptions
    ten_gods_meta = {
        "BiJian":    {"name": "比肩", "icon": "🤝", "desc": "坚定的盟友", "tag": "意志"},
        "JieCai":    {"name": "劫财", "icon": "🐺", "desc": "敏锐的猎手", "tag": "竞争"},
        "ShiShen":   {"name": "食神", "icon": "🎨", "desc": "优雅艺术家", "tag": "才华"},
        "ShangGuan": {"name": "伤官", "icon": "🎤", "desc": "叛逆演说家", "tag": "创新"},
        "PianCai":   {"name": "偏财", "icon": "💸", "desc": "慷慨冒险家", "tag": "机遇"},
        "ZhengCai":  {"name": "正财", "icon": "🏰", "desc": "勤勉建设者", "tag": "积累"},
        "QiSha":     {"name": "七杀", "icon": "⚔️", "desc": "无畏的将军", "tag": "魄力"},
        "ZhengGuan": {"name": "正官", "icon": "⚖️", "desc": "公正的法官", "tag": "秩序"},
        "PianYin":   {"name": "偏印", "icon": "🦉", "desc": "孤独的智者", "tag": "洞察"},
        "ZhengYin":  {"name": "正印", "icon": "🛡️", "desc": "仁慈守护者", "tag": "庇护"},
    }

    # Grid Layout
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
    
    def style_metric(col, key, val):
        meta = ten_gods_meta.get(key, {"name": key, "icon": "?", "desc": "", "tag": ""})
        val_f = float(val)
        
        # Color Logic: Silver -> Neon Green -> Red
        # Thresholds:
        # < 3.0: Silver (Weak/Latent)
        # 3.0 - 6.0: Neon Green (Healthy/Active)
        # > 6.0: Red (Dominant/Excessive)
        
        color = "#B0B0B0" # Silver / Grey
        box_shadow = "0 2px 4px rgba(0,0,0,0.3)"
        
        if val_f > 6: 
            color = "#FF4500" # High Energy Red
            box_shadow = "0 0 8px rgba(255, 69, 0, 0.4)"
        elif val_f > 3: 
            color = "#00E676" # Neon Green
            box_shadow = "0 0 5px rgba(0, 230, 118, 0.3)"
        else:
            # Silver/Weak state
            color = "#C0C0C0" 
        
        # Bar chart BG style (Gradient fill from bottom)
        # Cap at 100% for fill
        pct = min(val_f * 10, 100) # Slightly more sensitive (scale 0-10)
        
        # Background gradient: Fills up with a subtle glass effect
        bg_gradient = f"linear-gradient(to top, rgba(255,255,255,0.1) {pct}%, rgba(30,30,30,0.5) {pct}%)"
        
        # NOTE: Indentation removed to prevent Markdown from interpreting this as a code block
        col.markdown(f"""<div style="text-align: center; border: 1px solid #444; background: {bg_gradient}; padding: 8px 4px; border-radius: 8px; margin-bottom: 8px; box-shadow: {box_shadow}; position: relative; transition: transform 0.2s;">
    <!-- Tag Badge -->
    <div style="position: absolute; top: 4px; right: 4px; font-size: 0.5em; background: #222; color: #888; padding: 1px 4px; border-radius: 4px; opacity: 0.8; border: 1px solid #444;">
        {meta['tag']}
    </div>
    <!-- Icon & Name -->
    <div style="font-size: 0.9em; color: #CCC; margin-bottom: 4px; margin-top: 4px; display: flex; align-items: center; justify-content: center; gap: 4px;">
        <span style="font-size: 1.2em;">{meta['icon']}</span> {meta['name']}
    </div>
    <!-- Value -->
    <div style="font-size: 1.5em; font-weight: 900; color: {color}; margin: -2px 0 2px 0; text-shadow: 0 1px 2px rgba(0,0,0,0.5);">
        {val_f:.1f}
    </div>
    <!-- Description -->
    <div style="font-size: 0.65em; color: #999; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 2px;">
        {meta['desc']}
    </div>
</div>""", unsafe_allow_html=True)

    # Column 1: Self
    style_metric(r1c1, "BiJian", dg.get('BiJian', 0) * scale)
    style_metric(r2c1, "JieCai", dg.get('JieCai', 0) * scale)
    
    # Column 2: Output
    style_metric(r1c2, "ShiShen", dg.get('ShiShen', 0) * scale)
    style_metric(r2c2, "ShangGuan", dg.get('ShangGuan', 0) * scale)
    
    # Column 3: Wealth
    style_metric(r1c3, "PianCai", dg.get('PianCai', 0) * scale)
    style_metric(r2c3, "ZhengCai", dg.get('ZhengCai', 0) * scale)
    
    # Column 4: Officer
    style_metric(r1c4, "QiSha", dg.get('QiSha', 0) * scale)
    style_metric(r2c4, "ZhengGuan", dg.get('ZhengGuan', 0) * scale)
    
    # Column 5: Resource
    style_metric(r1c5, "PianYin", dg.get('PianYin', 0) * scale)
    style_metric(r2c5, "ZhengYin", dg.get('ZhengYin', 0) * scale)

    st.markdown("---")
    

    # 5. Result Visualization (Section 4 & 5 Requirement)
    st.markdown("### ⚛️ 量子断语 (Quantum Verdicts)")
    
    def get_verdict_text(score):
        if score > 6: return "大吉 / 爆发"
        elif score > 2: return "吉 / 上升"
        elif score < -6: return "大凶 / 崩塌"
        elif score < -2: return "凶 / 阻力"
        return "平稳"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("⚔️ 事业 (Career)", f"{results['career']}", delta=get_verdict_text(results['career']))
    with c2:
        st.metric("💰 财富 (Wealth)", f"{results['wealth']}", delta=get_verdict_text(results['wealth']))
    with c3:
        st.metric("❤️ 感情 (Rel)", f"{results['relationship']}", delta=get_verdict_text(results['relationship']))
        
    # B. Narrative Box
    # B. Narrative Box (V2.9: Narrative Cards)
    st.markdown("### 📜 核心叙事 (Narrative Events)")
    
    narrative_events = results.get('narrative_events', [])
    
    if narrative_events:
        nc1, nc2 = st.columns(2)
        for i, event in enumerate(narrative_events):
            with nc1 if i % 2 == 0 else nc2:
                render_narrative_card(event)
    else:
        # Fallback to description if no special events
        desc = results.get('desc', '能量流转平稳')
        st.info(f"**V2.3 Narrative:**\n\n{desc}")

    st.markdown("---")
    # --- New Section: Quantum Destiny Trajectory (Charts) ---
    # --- New Section: Dynamic Timeline (Quantum Lab Logic) ---
    st.markdown("### 🌊 动态流年模拟 (Dynamic Timeline)")
    st.caption(f"未来 12 年 ({sim_year} - {sim_year+11}) 能量趋势模拟")
    
    # Sprint 5.4: Adaptive Disclaimer
    birth_info_check = case_data.get('birth_info')
    is_dynamic_ready = birth_info_check and birth_info_check.get('year')
    
    if is_dynamic_ready:
        st.info("""
✅ **动态大运已激活**: 系统正在根据您的出生日期实时计算大运切换。
如果图表中出现 🔄 虚线，表示该年运势进入新阶段。
        """.strip())
    else:
        st.warning("""
ℹ️ **静态大运模式**: 由于未检测到具体出生日期（仅有四柱干支），系统将使用当前大运进行推演。
若需查看精确的换运时间，请使用日期方式重新排盘。
        """.strip())
    
    years = range(sim_year, sim_year + 12)
    traj_data = []
    handover_years = []  # Sprint 5.4: 记录换运年份
    prev_luck = None  # 跟踪上一年的大运
    
    # Helper for GanZhi
    gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    base_year = 1924 # Jia Zi
    
    # === V6.0: BaziProfile Initialization ===
    # Convert input date/time to full datetime
    birth_dt = datetime.datetime.combine(d, datetime.time(t, 0))
    profile = BaziProfile(birth_dt, gender)
    
    # Optional: Update profile with specific analysis if needed (e.g. wang_shuai from previous steps if we trust it more?)
    # For now, let BaziProfile calculate its own strength to be the Single Source of Truth.
    
    for y in years:
        offset = y - base_year
        l_gan = gan_chars[offset % 10]
        l_zhi = zhi_chars[offset % 12]
        l_gz = f"{l_gan}{l_zhi}"
        
        # 1. Get Luck from Profile (O(1))
        active_luck = profile.get_luck_pillar_at(y)
        
        # 2. Call QuantumEngine V6.0 Interface
        ctx = engine.calculate_year_context(profile, y)
        
        # Extract data from DestinyContext (clean and simple!)
        final_career = ctx.career
        final_wealth = ctx.wealth
        final_rel = ctx.relationship
        full_desc = ctx.description
        
        # Trinity data for visualization
        is_treasury_open = ctx.is_treasury_open
        treasury_icon_type = ctx.icon
        treasury_risk = ctx.risk_level
        treasury_tags = ctx.tags
        
        # Sprint 5.4: 检测换运点
        if prev_luck and prev_luck != active_luck:
            handover_years.append({
                'year': y,
                'from': prev_luck,
                'to': active_luck
            })
        prev_luck = active_luck

        # 0. 确保数据类型绝对安全
        safe_year = int(y)
        safe_career = float(final_career) if final_career is not None else 0.0
        safe_wealth = float(final_wealth) if final_wealth is not None else 0.0
        safe_rel = float(final_rel) if final_rel is not None else 0.0

        traj_data.append({
            "year": safe_year,
            "label": f"{safe_year}\n{l_gz}",
            "career": round(safe_career, 2),
            "wealth": round(safe_wealth, 2),
            "relationship": round(safe_rel, 2),
            "desc": full_desc,
            # V3.5 Metadata (simplified)
            "is_treasury_open": is_treasury_open,
            "treasury_icon": treasury_icon_type,
            "treasury_risk": treasury_risk
        })
        
    # Sprint 5.4 Debug: 显示大运变化信息
    if handover_years:
        st.success(f"🔄 检测到 {len(handover_years)} 个换运点：")
        for h in handover_years:
            st.write(f"  • {h['year']}年: {h['from']} → {h['to']}")
    else:
        st.error("⚠️ **Bug警告**: 12年内未检测到换运点！")
        st.error("📐 数学事实: 一步大运=10年，模拟周期=12年，12>10 → 必然有换运！")
        st.error("🔍 请查看下方调试面板获取详细信息")
        if prev_luck:
            st.caption(f"可疑: 全程使用同一大运 `{prev_luck}` (可能是fallback)")
    
    # Render Chart
    df_traj = pd.DataFrame(traj_data)
    
    # 🔍 终极调试：打印前三年数据，看看为什么没画出来
    st.write("🔍 **前三年数据检查 (Raw Data)**:")
    st.write(df_traj.head(3)[['year', 'label', 'career', 'wealth', 'relationship']])
    
    # Safety check: Only render chart if data exists
    if not df_traj.empty and 'label' in df_traj.columns:
        # V3.5 Sprint 5: Extract Treasury Points with icon and color
        treasury_points_labels = []
        treasury_points_career = []
        treasury_points_wealth = []
        treasury_points_rel = []
        treasury_icons = []
        treasury_colors = []  # Color differentiation
        
        for d in traj_data:
            if d.get('is_treasury_open'):
                treasury_points_labels.append(d['label'])
                treasury_points_career.append(d['career'])
                treasury_points_wealth.append(d['wealth'])
                treasury_points_rel.append(d['relationship'])
                
                # Use backend-provided icon directly
                icon = d.get('treasury_icon', '🗝️')
                treasury_icons.append(icon)
                
                # Color mapping based on risk level
                risk = d.get('treasury_risk', 'opportunity')
                if risk == 'warning':
                    treasury_colors.append('#FF6B35')  # Orange for warning
                else:
                    treasury_colors.append('#FFD700')  # Gold for opportunity
        
        fig = go.Figure()
        
        # Base trajectory lines
        fig.add_trace(go.Scatter(
            x=df_traj['year'], 
            y=df_traj['career'], 
            mode='lines+markers', 
            name='事业 (Career)',
            line=dict(color='#00E5FF', width=3),
            connectgaps=True, # 强制连线
            hovertext=df_traj['desc']
        ))
        fig.add_trace(go.Scatter(
            x=df_traj['year'], 
            y=df_traj['wealth'], 
            mode='lines+markers', 
            name='财富 (Wealth)',
            line=dict(color='#FFD700', width=3),
            connectgaps=True, # 强制连线
            hovertext=df_traj['desc']
        ))
        fig.add_trace(go.Scatter(
            x=df_traj['year'], 
            y=df_traj['relationship'], 
            mode='lines+markers', 
            name='感情 (Rel)',
            line=dict(color='#F50057', width=3),
            connectgaps=True, # 强制连线
            hovertext=df_traj['desc']
        ))
        
        # V3.5 Treasury Icon Overlay with Color Differentiation
        if treasury_points_labels:
            # Use the maximum value among the three dimensions for icon placement
            treasury_points_y = [max(c, w, r) for c, w, r in zip(
                treasury_points_career, treasury_points_wealth, treasury_points_rel
            )]
            
            fig.add_trace(go.Scatter(
                x=treasury_points_labels,
                y=treasury_points_y,
                mode='text',
                text=treasury_icons,
                textposition="top center",
                textfont=dict(size=36),  # Larger for visibility
                marker=dict(color=treasury_colors),
                name='💰 库门事件',
                hoverinfo='skip',
                showlegend=False
            ))
        
        # Sprint 5.4: 添加换运分界线
        for handover in handover_years:
            fig.add_vline(
                x=handover['year'],
                line_width=2,
                line_dash="dash",
                line_color="rgba(255,255,255,0.6)",
                annotation_text=f"🔄 换运\\n{handover['to']}",
                annotation_position="top",
                annotation=dict(
                    font=dict(size=10, color="white"),
                    bgcolor="rgba(100,100,255,0.3)",
                    bordercolor="rgba(255,255,255,0.5)",
                    borderwidth=1
                )
            )
        
        fig.update_layout(
            title="🏛️ Antigravity V5.3: 命运全息图 (Destiny Wavefunction)",
            yaxis=dict(title="能量级 (Energy Score)", range=[-10, 12]),
            xaxis=dict(
                title="年份 (Year)",
                range=[sim_year - 0.5, sim_year + 11.5], # 强制锁定范围
                tickmode='linear',
                dtick=1
            ),
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=80),  # More space for legend
            height=500,  # Taller chart
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,  # Below chart
                xanchor="center",
                x=0.5,
                font=dict(size=12),
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.3)",
                borderwidth=1
            ),
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # V3.0 DEBUG: Treasury Detection Status
        with st.expander("🐛 财库检测调试 (Treasury Debug)", expanded=False):
            st.write(f"**总年数**: {len(traj_data)} 年")
            st.write(f"**检测到财库开启**: {len(treasury_points_labels)} 次")
            
            if treasury_points_labels:
                st.success(f"✅ 找到 {len(treasury_points_labels)} 个财库事件！")
                for i, label in enumerate(treasury_points_labels):
                    icon = treasury_icons[i]
                    st.write(f"- {label}: {icon} (Y坐标: {treasury_points_y[i]})")
            else:
                st.warning("⚠️ 未检测到任何财库开启事件")
                st.write("**检查以下内容**:")
                
                # Show sample data
                st.write("**前3年数据样本**:")
                for i, d in enumerate(traj_data[:3]):
                    st.json({
                        'year': d['year'],
                        'label': d['label'],
                        'is_treasury_open': d.get('is_treasury_open'),
                        'is_wealth_treasury': d.get('is_wealth_treasury'),
                        'treasury_element': d.get('treasury_element'),
                        'v2_details': d.get('desc', '').split('|')[-1] if '|' in d.get('desc', '') else 'none'
                    })
        
        # Sprint 5.4 DEBUG: Dynamic Luck Progression
        with st.expander("🔄 大运动态检测 (Luck Progression Debug)", expanded=True):  # 默认展开！
            st.write(f"**模拟年份**: {sim_year} - {sim_year + 11}")
            st.write(f"**检测到换运点**: {len(handover_years)} 个")
            
            # === 关键调试：显示完整大运时间表 ===
            st.markdown("### 📋 完整大运时间表 (Timeline)")
            try:
                # 尝试获取timeline
                birth_info = case_data.get('birth_info', {})
                birth_year = birth_info.get('year', 1990)
                birth_month = birth_info.get('month', 1)
                birth_day = birth_info.get('day', 1)
                birth_hour = birth_info.get('hour', 12)
                gender = birth_info.get('gender', 1)
                
                # Debug: 显示使用的出生信息
                st.caption(f"计算基准: {birth_year}年{birth_month}月{birth_day}日 {birth_hour}时 (性别:{gender})")
                
                timeline = engine.get_luck_timeline(
                    birth_year, birth_month, birth_day, birth_hour, gender, num_steps=10
                )
                
                if timeline:
                    st.success("✅ 成功生成大运时间表：")
                    st.json(timeline) # 直接显示完整JSON以便检查
                else:
                    st.error("❌ Timeline为空！")
            except Exception as e:
                st.error(f"❌ Timeline获取失败: {e}")
            
            st.markdown("### 📊 逐年大运追踪")
            # 显示每年实际使用的大运
            if traj_data:
                year_luck_tracking = []
                # 重新计算每年的大运（用于调试）
                for y in range(sim_year, sim_year + 12):
                    try:
                        luck = engine.get_dynamic_luck_pillar(
                            birth_year, birth_month, birth_day, birth_hour, gender, y
                        )
                        year_luck_tracking.append(f"{y}: `{luck}`")
                    except:
                        year_luck_tracking.append(f"{y}: ❌ 计算失败")
                
                # 按列显示
                col1, col2, col3 = st.columns(3)
                for i, track in enumerate(year_luck_tracking):
                    if i % 3 == 0:
                        col1.write(track)
                    elif i % 3 == 1:
                        col2.write(track)
                    else:
                        col3.write(track)
            
            if handover_years:
                st.success("✅ 发现大运切换：")
                for h in handover_years:
                    st.write(f"  📍 {h['year']}年: `{h['from']}` → `{h['to']}`")
            else:
                st.error("⚠️ **BUG警告**: 12年内未检测到换运！")
                st.error("数学上12 > 10，必然有换运点！请检查算法！")
                if prev_luck:
                    st.write(f"**全程大运**: `{prev_luck}` (可能是静态fallback)")
            
            st.caption("💡 如果Timeline显示有多个大运，但未检测到换运，说明代码有Bug！")
        
        # DEBUG: Show data summary
        with st.expander("🔍 数据诊断 (Data Debug)", expanded=False):
            st.write("**样本数据点 (前3年)**:")
            for i, d in enumerate(traj_data[:3]):
                st.write(f"Year {d['year']}: Career={d['career']}, Wealth={d['wealth']}, Rel={d['relationship']}")
            
            # Check for identical values (which would cause lines to overlap)
            careers = [d['career'] for d in traj_data]
            wealths = [d['wealth'] for d in traj_data]
            rels = [d['relationship'] for d in traj_data]
            
            st.write(f"\n**数值范围**:")
            st.write(f"- 事业: [{min(careers):.1f}, {max(careers):.1f}]")
            st.write(f"- 财富: [{min(wealths):.1f}, {max(wealths):.1f}]")
            st.write(f"- 感情: [{min(rels):.1f}, {max(rels):.1f}]")
            
            # Check if all lines are identical
            if careers == wealths == rels:
                st.warning("⚠️ 警告：三条曲线数值完全相同！这会导致线条重叠。")
        
        # V3.0 Explainer: Treasury Events Log
        treasury_events = [d for d in traj_data if d.get('is_treasury_open')]
        if treasury_events:
            st.markdown("### 🔓 墓库开启事件 (Treasury Opening Events)")
            cols = st.columns(min(len(treasury_events), 4))
            for i, event in enumerate(treasury_events):
                with cols[i % 4]:
                    icon = "🏆" if event.get('is_wealth_treasury') else "🗝️"
                    treasury_type = "财库 (Wealth)" if event.get('is_wealth_treasury') else f"杂气库 ({event.get('treasury_element')})"
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 15px; border-radius: 10px; text-align: center; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                        <div style="font-size: 2.5em;">{icon}</div>
                        <div style="font-size: 1.2em; font-weight: bold; color: #FFD700; margin-top: 5px;">
                            {event['year']} {event['label'].split()[1] if len(event['label'].split()) > 1 else ''}
                        </div>
                        <div style="font-size: 0.9em; color: #EEE; margin-top: 5px;">
                            {treasury_type}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No trajectory data available for visualization.")


    # C. Physics Debug (Optional)
    with st.expander("🔬 查看物理参数 (Physics Debug)"):
        st.json(physics_sources)
        st.write(f"Wang/Shuai: {case_data['wang_shuai']}")
        
    # D. Calculation Audit (Transparency)
    with st.expander("📊 数值计算审计 (Calculation Audit)", expanded=True):
        st.markdown("### 1. 核心映射逻辑 (Core Mapping)")
        st.markdown("**原理**: 智能排盘 (Flux Engine) 生成的原始能量场 (0-100+) 通过缩放系数映射到 量子物理引擎 (Quantum Layer) 的标准输入 (0-10)。")
        st.latex(r"E_{quantum} = E_{flux} \times 0.08")
        
        st.markdown("### 2. 详细转换追踪 (Trace)")
        audit_data = []
        for p in flux_engine.particles:
            if "dy_" in p.id or "ln_" in p.id: continue
            raw = p.wave.amplitude
            scaled = raw * scale
            audit_data.append({
                "Particle": f"{p.char} ({p.id})",
                "Raw Flux (E_f)": f"{raw:.1f}",
                "Scale Factor": f"{scale}",
                "Quantum Input (E_q)": f"{scaled:.1f}"
            })
        st.dataframe(pd.DataFrame(audit_data))
        
        st.markdown("### 3. 被激活的黄金参数 (Active Golden Params)")
        st.caption("以下参数来自 `golden_parameters.json`，确保了与量子验证实验室的一致性。")
        st.json(params)

