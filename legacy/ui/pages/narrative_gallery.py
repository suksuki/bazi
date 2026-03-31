import streamlit as st
import time
import json
import random

# Page Config
st.set_page_config(
    page_title="V2.9 Narrative Gallery",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS: Quantum Glassmorphism & Animations ---
st.markdown("""
<style>
/* 1. Global Gradient Background (Deep Space) */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    color: #e2e8f0;
}

/* 2. Glassmorphism Card Container */
.narrative-card {
    position: relative;
    padding: 24px;
    border-radius: 16px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    transition: all 0.3s ease;
    margin-bottom: 20px;
}
.narrative-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    border-color: rgba(255, 255, 255, 0.2);
}

/* 3. Card Types / Themes */

/* Mountain Alliance (Earth/Gold) */
.card-mountain {
    background: linear-gradient(135deg, rgba(120, 53, 15, 0.15) 0%, rgba(251, 191, 36, 0.1) 100%);
    border-top: 2px solid rgba(251, 191, 36, 0.4);
}
.icon-mountain {
    font-size: 32px;
    background: linear-gradient(to bottom, #fbbf24, #b45309);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.5));
}

/* Penalty Cap (Shield/Blue) */
.card-shield {
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(56, 189, 248, 0.1) 100%);
    border-top: 2px solid rgba(56, 189, 248, 0.4);
}
.icon-shield {
    font-size: 32px;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
}

/* Mediation Flow (Water/Green) */
.card-flow {
    background: linear-gradient(135deg, rgba(6, 78, 59, 0.2) 0%, rgba(52, 211, 153, 0.1) 100%);
    border-top: 2px solid rgba(52, 211, 153, 0.4);
}
.icon-flow {
    font-size: 32px;
    color: #34d399;
    filter: drop-shadow(0 0 5px rgba(52, 211, 153, 0.6));
}

/* Danger / Pressure (Red) */
.card-danger {
    background: linear-gradient(135deg, rgba(127, 29, 29, 0.2) 0%, rgba(248, 113, 113, 0.1) 100%);
    border-top: 2px solid rgba(248, 113, 113, 0.4);
}

/* 4. Animations */

@keyframes pulse-gold {
    0% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(251, 191, 36, 0); }
    100% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0); }
}

@keyframes ripple-blue {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.anim-pulse-gold {
    animation: pulse-gold 2s infinite;
}

/* 5. Typography */
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
    background: rgba(0,0,0,0.3);
    display: inline-block;
}

</style>
""", unsafe_allow_html=True)

# --- Component: Narrative Card Renderer ---
def render_narrative_card(event):
    """
    Renders a single narrative card based on the event payload.
    """
    ctype = event.get('card_type', 'default')
    
    # Map types to CSS classes and icons
    config = {
        "mountain_alliance": {"css": "card-mountain", "icon": "⛰️", "icon_css": "icon-mountain"},
        "penalty_cap": {"css": "card-shield", "icon": "🛡️", "icon_css": "icon-shield"},
        "mediation": {"css": "card-flow", "icon": "🌊", "icon_css": "icon-flow"},
        "pressure": {"css": "card-danger", "icon": "⚠️", "icon_css": ""},
        "default": {"css": "", "icon": "📜", "icon_css": ""}
    }
    
    cfg = config.get(ctype, config['default'])
    
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
        <!-- Visualization Placeholder for Three.js/Lottie later -->
        <div style="position: absolute; right: 10px; top: 10px; opacity: 0.1;">
            <span style="font-size: 60px;">{cfg['icon']}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- Main Application ---

st.title("Quantum Narrative Gallery")
st.markdown("**V2.9 Compassionate Physics - Visual Prototype**")
st.caption("Visualizing the 'Humanity' in the Equations. Powered by Quantum Engine V2.9.")
st.divider()

# Tab Structure
tab1, tab2 = st.tabs(["🏛️ Hall of Fame (Prototypes)", "🔬 Live Engine Test"])

with tab1:
    st.header("The Golden Master Collection")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Case 25: The Mountain")
        render_narrative_card({
            "card_type": "mountain_alliance",
            "title": "积土成山 (Mountain Alliance)",
            "desc": "土旺身强，比劫化为合伙人。",
            "score_delta": "+5.0 Wealth (Exempt)",
            "animation_trigger": "earth_assemble"
        })
        st.info("Triggered when Earth Day Master + Strong Self + Rob Wealth. Standard Robbery penalty is waived.")

    with col2:
        st.subheader("Case 21: The Shield")
        render_narrative_card({
             "card_type": "penalty_cap",
             "title": "饱和防御 (Damage Cap)",
             "desc": "结构性破坏已达物理阈值，护盾激活。",
             "score_delta": "Penalty Capped at -6.0",
             "animation_trigger": "shield_ripple"
        })
        st.info("Triggered when cumulative Structural Clash/Harm penalty exceeds 6.0.")

    with col3:
        st.subheader("Case 1: The Flow")
        render_narrative_card({
            "card_type": "mediation",
            "title": "食伤通关 (Mediation Flow)",
            "desc": "转危为机，源远流长。",
            "score_delta": "Clash Converted to Wealth",
            "animation_trigger": "prism_flow"
        })
        st.info("Triggered when Output (Food God) is strong enough to bridge Self and Wealth.")

with tab2:
    st.header("Live Engine Verification")
    
    # Inject logic to run real engine
    import sys
    import os
    sys.path.append(os.getcwd())
    from core.unified_engine import UnifiedEngine as QuantumEngine  # V9.1 Unified Engine
    
    # Load Golden Parameters
    try:
        with open('data/golden_parameters.json', 'r') as f:
            params = json.load(f)
            st.success("Loaded V2.9 Golden Parameters")
    except:
        st.error("Could not load golden_parameters.json")
        params = {}

    # Load Cases
    try:
        with open('data/calibration_cases.json', 'r') as f:
            cases = json.load(f)
            case_options = {f"Case {c['id']}: {c.get('desc','')}": c for c in cases}
    except:
        cases = []
        case_options = {}

    selected_case_name = st.selectbox("Select Benchmark Case", list(case_options.keys()))
    
    if selected_case_name:
        case_data = case_options[selected_case_name]
        
        if st.button("Run Quantum Engine V2.9"):
            engine = QuantumEngine(params)
            result = engine.calculate_energy(case_data)
            
            # Display Result
            st.write(f"### Verdict for {selected_case_name}")
            cols = st.columns(3)
            cols[0].metric("Career", result['career'])
            cols[1].metric("Wealth", result['wealth'])
            cols[2].metric("Relationship", result['relationship'])
            
            st.write("### Generated Narrative Cards")
            events = result.get('narrative_events', [])
            
            if not events:
                st.write("No special narrative events triggered.")
            else:
                for event in events:
                    render_narrative_card(event)
            
            with st.expander("Full JSON Output"):
                st.json(result)

