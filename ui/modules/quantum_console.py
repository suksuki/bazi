
import streamlit as st
from core.flux import FluxEngine

def render_quantum_console(chart, dy_stem, dy_branch, ln_stem, ln_branch):
    """
    Step 7 UI: The "Atomic Work Console" (Quantum Switchboard).
    Allows interactive toggling of physics rules to see real-time energy changes.
    """
    st.markdown("### 🎛️ 原子化做功控制台 (Quantum Switchboard)")
    
    # 1. First Pass: Run Full Simulation to Discover Rules
    try:
        discovery_engine = FluxEngine(chart)
        # We run it once blindly to see what happens
        full_result = discovery_engine.calculate_flux(dy_stem, dy_branch, ln_stem, ln_branch)
        detected_rules = full_result.get('detected_rules', [])
    except Exception as e:
        st.error(f"Flux Engine Error: {e}")
        return

    # 2. UI State Management (Disabled Rules)
    if "disabled_flux_rules" not in st.session_state:
        st.session_state["disabled_flux_rules"] = set()
        
    # Layout
    c_left, c_right = st.columns([0.6, 0.4])
    
    with c_right:
        st.caption("⚡ 物理相互作用 (Interaction Layer)")
        
        # Checkbox Logic
        # If checked -> Rule Active (Not in disabled set)
        # If unchecked -> Rule Disabled (In disabled set)
        
        active_rules = []
        if not detected_rules:
            st.info("无明显的物理相互作用 (No major interactions detected)")
        
        for rule_key in detected_rules:
            is_enabled = rule_key not in st.session_state["disabled_flux_rules"]
            
            # Label beautification
            label = rule_key.replace("SanHe:", "三合 (SanHe):") \
                            .replace("LiuChong:", "冲克 (Clash):") \
                            .replace("TongGuan:", "通关 (Bridge):") \
                            .replace("Activation:", "应期 (Activate):")
            
            checked = st.checkbox(label, value=is_enabled, key=f"chk_{rule_key}")
            
            if checked:
                # Remove from disabled list if present
                if rule_key in st.session_state["disabled_flux_rules"]:
                    st.session_state["disabled_flux_rules"].remove(rule_key)
            else:
                # Add to disabled list
                st.session_state["disabled_flux_rules"].add(rule_key)

    # 3. Second Pass: Run with Selected Rules
    final_engine = FluxEngine(chart)
    final_result = final_engine.calculate_flux(
        dy_stem, dy_branch, ln_stem, ln_branch, 
        disabled_rules=st.session_state["disabled_flux_rules"]
    )
    
    # 4. Render Energy Bars (Left Side)
    with c_left:
        st.caption("🔋 粒子能级 (Particle Energy Levels)")
        
        # We display the 8 Natal Particles + DY/LN if active
        p_states = final_result.get('particle_states', [])
        
        # Filter identifying info
        natal_ps = [p for p in p_states if "dy_" not in p['id'] and "ln_" not in p['id']]
        
        # Sort by Pillar Order: Y, M, D, H
        order_map = {"year": 0, "month": 1, "day": 2, "hour": 3}
        natal_ps.sort(key=lambda x: order_map.get(x['id'].split('_')[0], 99))
        
        for p in natal_ps:
            # Build label
            pillar_name = p['id'].split('_')[0].capitalize()
            type_label = "Stem" if "stem" in p['id'] else "Branch"
            label = f"{pillar_name} {type_label}: {p['char']}"
            
            # Energy Value
            val = p['amp']
            
            # Determine color based on threshold (15.0 is base survival)
            color = "green"
            if val < 15.0: color = "red"
            elif val > 80.0: color = "orange" # High energy / Burn
            
            st.markdown(f"**{label}**")
            st.progress(min(val / 150.0, 1.0)) # Scale to max 150
            
            # Delta logic?
            # To show Delta, we'd need to compare against "Full Rules Disabled" or "All Rules Enabled".
            # For now, dynamic jump is visible when user toggles checkbox.
            st.caption(f"Energy: {val:.1f} | Status: {', '.join(p['status'])}")
            
        # Show Meaning Interpretation
        from core.meaning import MeaningEngine
        me = MeaningEngine(chart, final_result)
        report = me.analyze()
        
        st.divider()
        st.subheader("💡 宏观定义 (Macro Definition)")
        
        if report['work_modes']:
            for mode in report['work_modes']:
                st.info(f"🛠️ {mode['type']}: {mode['desc']}")
        else:
            st.caption("无特殊做功模式 (No special work mode)")
            
        w = report['wealth_potential']
        st.metric("Unified Wealth Score", f"{w['score']}", delta=w['rating'])
        
    return final_result
