import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys

# Append root path to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Migration
from core.context import DestinyContext
from core.bazi_profile import VirtualBaziProfile

# Load Golden Parameters
GOLDEN_PARAMS_PATH = os.path.join(os.path.dirname(__file__), '../../data/golden_parameters.json')
CALIBRATION_CASES_PATH = os.path.join(os.path.dirname(__file__), '../../data/calibration_cases.json')

try:
    with open(GOLDEN_PARAMS_PATH, 'r') as f:
        GOLDEN_CONFIG = json.load(f)
except Exception as e:
    GOLDEN_CONFIG = {}

def load_cases():
    try:
        with open(CALIBRATION_CASES_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load cases: {e}")
        return []

def generate_narrative_from_context(ctx: DestinyContext) -> str:
    """
    V4.0 Trinity: Generate LLM-constrained narrative
    LLM must follow the narrative_prompt as gospel truth
    """
    # System Prompt: The Director's Script
    system_prompt = f"""你是一位精通命理与人性的剧作家。
请根据以下【核心设定】创作一段年度运势独白。

【核心设定】(必须严格遵守，这是算法的绝对真理):
{ctx.narrative_prompt}

【风格要求】:
- 如果包含"Risk/风险/大凶/危机"，语气需深沉、警示，引用《周易》或《麦克白》中的危机感。
- 如果包含"Opportunity/机遇/大吉"，语气需激昂、振奋，如同《华尔街之狼》或英雄史诗。
- 如果包含"身弱不胜财"，务必警告虚不受补、量力而行。
- 如果包含"身强胜财"，可积极鼓舞大展拳脚。
- 严禁违背核心设定（例如：设定为凶，绝不可写成吉）。

【输出要求】:
- 150-200字
- 第一人称或第二人称
- 文学化表达，但不失严谨性
"""
    
    # For now, return a simulated response (in production, call actual LLM)
    # This demonstrates the constraint mechanism
    
    # Simulate LLM with rule-based generation for demo
    if "警示" in ctx.narrative_prompt or "风险" in ctx.narrative_prompt or ctx.risk_level == "warning":
        # Dangerous scenario
        narrative = f"""
【{ctx.year}年 {ctx.pillar}】

{ctx.narrative_prompt.split('。')[0]}。

此刻如同《推背图》所言："阴盛阳衰，虚火上炎。" 虽见宝藏在前，却是镜花水月。
若强行攫取，恐招破耗之祸。宜守不宜攻，量力而为，方可避过劫数。

【核心警示】: {', '.join(ctx.tags[:3])}
【综合评分】: {ctx.score:.1f} (高风险区)
"""
    elif "积极" in ctx.narrative_prompt or "机遇" in ctx.narrative_prompt or ctx.risk_level == "opportunity":
        # Opportunistic scenario
        narrative = f"""
【{ctx.year}年 {ctx.pillar}】

{ctx.narrative_prompt.split('。')[0]}。

如《易经》所云："飞龙在天，利见大人。" 天时地利人和，三者齐聚。
此时不搏，更待何时？当如《华尔街之狼》般放手一搏，成就辉煌！

【关键机遇】: {', '.join(ctx.tags[:3])}
【综合评分】: {ctx.score:.1f} (黄金时机)
"""
    else:
        # Neutral scenario
        narrative = f"""
【{ctx.year}年 {ctx.pillar}】

{ctx.narrative_prompt.split('。')[0]}。

运势平稳如水，波澜不惊。宜按部就班，稳扎稳打。

【综合评分】: {ctx.score:.1f}
"""
    
    return narrative.strip()


def render():
    st.set_page_config(page_title="Zeitgeist Cinema V4.0", page_icon="🎬", layout="wide")
    
    st.title("🎬 命运波函数影院 V4.0 (Trinity Edition)")
    st.caption("Powered by Trinity Architecture | LLM Narratives Constrained by QuantumEngine")
    st.caption(f"🔧 Engine Version: `{QuantumEngine.VERSION}` (Modular)")
    
    # Sidebar: Case Selector
    cases = load_cases()
    if not cases:
        st.error("No cases loaded")
        return
    
    case_options = {f"No.{c['id']} {c['bazi'][2]}日主 ({c.get('description', 'Unknown')})": c for c in cases}
    selected_label = st.sidebar.selectbox("选择主演 (Subject)", list(case_options.keys()))
    selected_case = case_options[selected_label]
    
    # ---------------------------
    # 1. 12-Year Trinity Simulation
    # ---------------------------
    st.subheader(f"1. 命运全息图 (Destiny Hologram): 2024-2035")
    
    years = range(2024, 2036)
    contexts = []  # Store DestinyContext objects
    
    engine = QuantumEngine()
    
    # Prepare birth chart
    bazi = selected_case['bazi']
    birth_chart = {
        'year_pillar': bazi[0],
        'month_pillar': bazi[1],
        'day_pillar': bazi[2],
        'hour_pillar': bazi[3],
        'day_master': selected_case['day_master'],
        'energy_self': 3.0  # Simplified, can enhance based on wang_shuai
    }
    
    # Determine favorable/unfavorable (simplified)
    dm_elem = engine._get_element(selected_case['day_master'])
    all_elems = ['wood', 'fire', 'earth', 'metal', 'water']
    relation_map = {e: engine._get_relation(dm_elem, e) for e in all_elems}
    
    wang_shuai = selected_case.get('wang_shuai', '身中和')
    if "旺" in wang_shuai or "强" in wang_shuai:
        fav_types = ['output', 'wealth', 'officer']
    else:
        fav_types = ['resource', 'self']
    
    favorable = []
    unfavorable = []
    for e, r in relation_map.items():
        if r in fav_types:
            favorable.append(e.capitalize())
        else:
            unfavorable.append(e.capitalize())
    
    
    gender_map = {"男": 1, "女": 0}
    gender_val = gender_map.get(selected_case.get('gender', '男'), 1)
    
    # Construct pillars dict
    bazi_list = selected_case['bazi']
    pillars_dict = {
        'year': bazi_list[0],
        'month': bazi_list[1],
        'day': bazi_list[2],
        'hour': bazi_list[3]
    }
    
    profile = VirtualBaziProfile(
        pillars=pillars_dict,
        static_luck="未知",
        day_master=selected_case['day_master'],
        gender=gender_val
    )

    # === Trinity Calculation Loop ===
    for y in years:
        # Call Trinity Interface
        ctx = engine.calculate_year_context(profile, y)
        
        contexts.append(ctx)
    
    # Build DataFrame from contexts
    df_sim = pd.DataFrame([{
        'year': ctx.year,
        'ganzhi': ctx.pillar,
        'career': ctx.career,
        'wealth': ctx.wealth,
        'relationship': ctx.relationship,
        'score': ctx.score,
        'icon': ctx.icon,
        'energy_level': ctx.energy_level,
        'tags': ', '.join(ctx.tags[:3])
    } for ctx in contexts])
    
    # Plotly Chart with Trinity Icons
    fig = go.Figure()
    
    # Traces
    fig.add_trace(go.Scatter(
        x=df_sim['year'], y=df_sim['career'], 
        mode='lines+markers', name='事业 (Career)', 
        line=dict(color='#00CED1', width=3),
        hovertext=[f"{row['ganzhi']}: {row['tags']}" for _, row in df_sim.iterrows()]
    ))
    fig.add_trace(go.Scatter(
        x=df_sim['year'], y=df_sim['wealth'], 
        mode='lines+markers', name='财富 (Wealth)', 
        line=dict(color='#FFD700', width=3),
        hovertext=[f"{row['ganzhi']}: {row['tags']}" for _, row in df_sim.iterrows()]
    ))
    fig.add_trace(go.Scatter(
        x=df_sim['year'], y=df_sim['relationship'], 
        mode='lines+markers', name='感情 (Rel)', 
        line=dict(color='#FF1493', width=3),
        hovertext=[f"{row['ganzhi']}: {row['tags']}" for _, row in df_sim.iterrows()]
    ))
    
    # Add Trinity Icons
    treasury_years = [ctx.year for ctx in contexts if ctx.icon]
    treasury_icons = [ctx.icon for ctx in contexts if ctx.icon]
    treasury_y = [max(ctx.career, ctx.wealth, ctx.relationship) for ctx in contexts if ctx.icon]
    
    if treasury_years:
        fig.add_trace(go.Scatter(
            x=treasury_years,
            y=treasury_y,
            mode='text',
            text=treasury_icons,
            textposition="top center",
            textfont=dict(size=36),
            showlegend=False,
            hoverinfo='skip'
        ))

    fig.update_layout(
        title=f"Trinity 12年运势全息图 ({selected_case['bazi'][2]}日主)",
        xaxis_title="流年 (Year)",
        yaxis_title="能量级别 (Energy Level)",
        hovermode="x unified",
        template="plotly_dark",
        height=450
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # ---------------------------
    # 2. Time Slider & Trinity Narrative
    # ---------------------------
    st.markdown("---")
    st.subheader("2. 时光穿梭机 + AI剧本解说 (Time Shuttle & Narrative)")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        selected_year = st.select_slider("拖动时间轴穿越命运", options=list(years), value=2024)
        
        # Get context for selected year
        current_ctx = next(c for c in contexts if c.year == selected_year)
        
        st.markdown(f"### {current_ctx.year} {current_ctx.pillar}")
        
        # Display metrics
        st.metric("综合评分", f"{current_ctx.score:.1f}", 
                 delta=current_ctx.energy_level)
        
        # Tags
        if current_ctx.tags:
            st.markdown(f"**特征标签**: {', '.join(current_ctx.tags)}")
        
        # Icon
        if current_ctx.icon:
            st.markdown(f"## {current_ctx.icon}")
            st.caption(f"风险等级: {current_ctx.risk_level}")
    
    with c2:
        st.markdown("#### 🎭 AI 剧作家解说")
        st.caption("基于 Trinity Architecture 的受约束叙事生成")
        
        # Generate Narrative
        narrative = generate_narrative_from_context(current_ctx)
        
        # Display with styling based on risk level
        if current_ctx.risk_level == 'warning':
            st.error(narrative)
        elif current_ctx.risk_level == 'opportunity':
            st.success(narrative)
        else:
            st.info(narrative)
        
        # Show the constraint (expandable debug)
        with st.expander("🔍 查看 LLM 约束指令 (Trinity Constraint)"):
            st.code(current_ctx.narrative_prompt, language='text')
            st.caption("LLM 必须严格遵守此指令，不得自由发挥")
    
    # ---------------------------
    # 3. Dimension Breakdown
    # ---------------------------
    st.markdown("---")
    st.subheader("3. 三维能量分解 (Dimension Breakdown)")
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("事业 Career", f"{current_ctx.career:.1f}")
    with cols[1]:
        st.metric("财富 Wealth", f"{current_ctx.wealth:.1f}")
    with cols[2]:
        st.metric("感情 Relationship", f"{current_ctx.relationship:.1f}")

if __name__ == "__main__":
    render()
