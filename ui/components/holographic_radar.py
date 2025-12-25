
import plotly.graph_objects as go
import streamlit as st

def render_holographic_radar(resonance, unified_metrics, remedy, verdict):
    """
    Renders the 5-Axis Holographic Decision Radar (Quintary Tension Radar).
    Axes: Stability, Dynamic, Defense, Sensitivity, Geo-Response.
    """
    
    # --- 1. Calculate Scores (0-100) ---
    scores = {}
    
    # (1) Stability (稳态)
    # Base: Sync State (0-1). Modifier: Frag Index (lower is better), Brittleness (lower is better).
    sync = resonance.sync_state
    frag = resonance.fragmentation_index
    brit = resonance.brittleness
    
    # Formula: Sync * (1 - Frag/2) * (1 - Brittleness/2) * 100
    # Higher Sync is good. High Frag/Brit reduces score.
    s_score = sync * (1.0 - min(frag, 1.0)*0.3) * (1.0 - min(brit, 1.0)*0.3) * 100
    scores['Stability'] = min(max(s_score, 0), 100)
    
    # (2) Dynamic (动能)
    # Base: Flow Efficiency. Modifier: Capture Efficiency (if active).
    flow = resonance.flow_efficiency # Usually 0-2.0
    capture_eff = 0.0
    if unified_metrics and 'capture' in unified_metrics:
        capture_eff = unified_metrics['capture'].get('efficiency', 0.0)
    
    # If Capture is active and high, it boosts Dynamic score massiveley.
    # Flow usually around 1.0. Capture max 1.0.
    # Formula: (Flow + Capture*1.5) / 3 * 100
    d_score = (flow + capture_eff * 1.5) / 2.5 * 100
    scores['Dynamic'] = min(max(d_score, 0), 100)
    
    # (3) Defense (防御)
    # Base: 50 (Neutral). Modifier: Shielding (adds), Cutting (subtracts).
    base_def = 50.0
    cut_depth = 0.0
    shielding = 0.0 # Not directly exposed as metric yet, inferred from Remedy or low Cut Depth?
    # Actually, we can infer shielding if Cut Depth is low despite Cutting interaction.
    # But let's use the explicit metrics we have.
    
    if unified_metrics and 'cutting' in unified_metrics:
        cut_depth = unified_metrics['cutting'].get('depth', 0.0)
    
    # If remedy prescribes shield, add points.
    if remedy and "[CRITICAL SHIELD]" in remedy.get('description', ''):
        shielding = 0.8 # High shielding active/prescribed
    
    # Formula: (1 - Cut_Depth) * 100. Bonus for Shielding.
    def_score = (1.0 - cut_depth) * 100
    if shielding > 0: def_score = max(def_score, 80) # Shield boosts min defense
    scores['Defense'] = min(max(def_score, 0), 100)
    
    # (4) Sensitivity (灵敏/抗扰)
    # Inverse of Contamination/Pollution.
    poll = 0.0
    if unified_metrics and 'contamination' in unified_metrics:
        poll = unified_metrics['contamination'].get('index', 0.0)
    
    # Score: (1 - Pollution) * 100
    sens_score = (1.0 - poll) * 100
    scores['Sensitivity'] = min(max(sens_score, 0), 100)
    
    # (5) Geo-Response (空间)
    # Based on Improvement Delta from Remedy.
    imp = 0.0
    if remedy:
        imp = remedy.get('improvement', 0.0)
    
    # Improvement usu 0.0 - 0.5. Map 0.3 to 100.
    g_score = (imp / 0.3) * 100
    scores['Geo-Response'] = min(max(g_score, 0), 100)
    
    # --- 2. Render Plotly Radar ---
    categories = ['稳态 (Stability)', '动能 (Dynamic)', '防御 (Defense)', '灵敏 (Sensitivity)', '空间 (Geo-Response)']
    values = [
        scores['Stability'], 
        scores['Dynamic'], 
        scores['Defense'], 
        scores['Sensitivity'], 
        scores['Geo-Response']
    ]
    # Close the loop
    values += [values[0]]
    categories += [categories[0]]
    
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line_color='#00f2ff', # Neon Cyan
        fillcolor='rgba(0, 242, 255, 0.2)',
        name='命运张力 (Fate Tension)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False,
                linecolor='rgba(255,255,255,0.1)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#a0aec0'),
                gridcolor='rgba(255,255,255,0.1)',
                linecolor='rgba(255,255,255,0.1)'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=20),
        showlegend=False,
        height=300
    )
    
    st.markdown("##### 📡 全息决策雷达 (Holographic Decision Radar)")
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    
    
    # Optional: Display Radar Metrics below
    cols = st.columns(5)
    labels_map = {
        'Stability': '稳态 (S)', 
        'Dynamic': '动能 (D)', 
        'Defense': '防御 (Def)', 
        'Sensitivity': '抗扰 (Sen)', 
        'Geo-Response': '空间 (G)'
    }
    for i, (k, v) in enumerate(scores.items()):
        cols[i].metric(labels_map.get(k, k), f"{v:.0f}")

