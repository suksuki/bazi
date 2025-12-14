import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
import copy

# Append root path to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 🚀 V9.2 Spacetime Engine
from core.engine_v91 import EngineV91
from core.context import DestinyContext
from core.bazi_profile import VirtualBaziProfile, BaziProfile

# Load Constants
GOLDEN_PARAMS_PATH = os.path.join(os.path.dirname(__file__), '../../data/golden_parameters.json')
CALIBRATION_CASES_PATH = os.path.join(os.path.dirname(__file__), '../../data/calibration_cases.json')
GEO_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../data/geo_coefficients.json')

def load_geo_cities():
    try:
        with open(GEO_DATA_PATH, 'r') as f:
            data = json.load(f)
            return list(data.get("cities", {}).keys())
    except:
        return ["Unknown", "Beijing", "Singapore", "Harbin"]

def load_cases():
    try:
        if os.path.exists(CALIBRATION_CASES_PATH):
            with open(CALIBRATION_CASES_PATH, 'r') as f:
                return json.load(f)
    except: pass
    return []

# Initialize Engine
# @st.cache_resource
def get_engine():
    print("🔄 Reloading Engine V9.1...")
    # Force reload to pick up hotfixes in engine_v91.py
    import importlib
    import core.engine_v91
    importlib.reload(core.engine_v91)
    from core.engine_v91 import EngineV91
    return EngineV91()

engine = get_engine()

# Helper for Narrative
def generate_narrative_from_context(ctx: DestinyContext) -> str:
    """Generate simple narrative from context"""
    try:
        if "风险" in ctx.narrative_prompt or ctx.risk_level == "warning":
            return f"⚠️ 【{ctx.year}】{ctx.narrative_prompt}\n建议：宜守不宜攻，注意风险管控。"
        elif "机遇" in ctx.narrative_prompt or "吉" in ctx.narrative_prompt:
            return f"🚀 【{ctx.year}】{ctx.narrative_prompt}\n建议：大展宏图，积极进取。"
        else:
            return f"📅 【{ctx.year}】{ctx.narrative_prompt}\n建议：稳扎稳打，步步为营。"
    except:
        return f"【{ctx.year}】运势平稳。"

# [V9.3 Feature] Time Detective: Reverse Engineer Date from Bazi
import datetime
from lunar_python import Solar

@st.cache_data(show_spinner=False) 
def reverse_lookup_bazi(target_bazi, start_year=1950, end_year=2030):
    """
    Brute-force (optimized) reverse lookup of Bazi to Gregorian Date.
    target_bazi: [Y, M, D, H] (GanZhi strings)
    """
    found_dates = []
    tg_y, tg_m, tg_d, tg_h = target_bazi[0], target_bazi[1], target_bazi[2], target_bazi[3]
    
    # Iterate roughly possible years. 60-year cycle helps but manual is safer for close range.
    for y in range(start_year, end_year + 1):
        # Optimization: Check mid-year to filter Year Pillar quickly
        # (Approximate check, precise check happens inside)
        test_solar = Solar.fromYmd(y, 6, 15)
        lunar = test_solar.getLunar()
        curr_y_gz = lunar.getYearInGanZhi()
        
        # If year pillar matches (or is adjacent due to LiChun), we scan
        # Simple heuristic: Scan year if mid-year matches OR if we are paranoid (just scan all?)
        # Scanning all 80 years * 365 = 29200 ops. Tiny.
        # Let's just scan year if match to save 59/60th of time.
        
        if curr_y_gz == tg_y:
            # Scan this year (plus margins for LiChun)
            start_d = datetime.date(y, 1, 15)
            end_d = datetime.date(y+1, 2, 15)
            
            curr = start_d
            while curr < end_d:
                try:
                    s = Solar.fromYmd(curr.year, curr.month, curr.day)
                    l = s.getLunar()
                    
                    if l.getYearInGanZhiExact() == tg_y:
                        if l.getMonthInGanZhiExact() == tg_m:
                            if l.getDayInGanZhiExact() == tg_d:
                                # Day Matched! Check Hour.
                                # Check a few key hours to find Time Pillar
                                for h in range(0, 24, 2):
                                    sh = Solar.fromYmdHms(curr.year, curr.month, curr.day, h, 0, 0)
                                    lh = sh.getLunar()
                                    if lh.getTimeInGanZhi() == tg_h:
                                        # Found a match!
                                        # Use explicit formatting to ensure Time is visible
                                        return f"{sh.getYear()}-{sh.getMonth()}-{sh.getDay()} {sh.getHour()}:00"
                except: pass
                
                curr += datetime.timedelta(days=1)
                
    return None


# Main Entry Point needed by main.py
def render():
    # st.set_page_config only works if run directly, but here it's imported.
    # We'll skip set_page_config or wrap it in try-catch if needed, 
    # but usually main.py sets config.
    
    st.title("🎬 命运影院 V9.2 (Destiny Cinema)")
    st.caption("Powered by Antigravity Engine V9.1 (Heaven & Earth)")

    # --- 1. SIDEBAR CONTROLS ---
    st.sidebar.header("🕹️ 时空控制台 (Spacetime Console)")

    # Case Selection
    cases = load_cases()
    if not cases:
        st.error("No cases loaded.")
        return

    case_options = {f"{c['id']} - {c['description']}": c for c in cases}
    selected_case_name = st.sidebar.selectbox("🎭 选择剧本 (Case)", list(case_options.keys()))
    selected_case = case_options[selected_case_name]

    # Bazi Info
    # [V9.3 UI] Enhanced Sidebar Display
    bazi_str = ' '.join(selected_case['bazi'])
    st.sidebar.subheader("📜 剧本八字 (Script)")
    st.sidebar.code(bazi_str, language="text")
    st.sidebar.markdown(f"**日主**: `{selected_case['day_master']}`")
    
    # [TIME DETECTIVE] Auto-derive Date
    # Scanning 1940-2010 (Typical range for current tycoons)
    derived_date = reverse_lookup_bazi(selected_case['bazi'], 1940, 2010)
    if derived_date:
        st.sidebar.success(f"🗓️ 推算日期: {derived_date}")
    else:
        st.sidebar.caption("🔍 未找到匹配日期 (1940-2010)")

    st.sidebar.markdown("---")

    # Geo Control
    st.sidebar.subheader("🌍 地利 (Geo)")
    
    # [V9.3 Fix] Default to None (Neutral) as requested
    raw_cities = load_geo_cities()
    # Ensure Beijing is prominent
    if "Beijing" in raw_cities: raw_cities.remove("Beijing")
    cities = ["None", "Beijing"] + raw_cities
    
    selected_city = st.sidebar.selectbox("出生/生活城市", cities, index=0)
    
    # [V9.3 Logic] Map None to Neutral
    if selected_city == "None":
        selected_city = "Unknown" # Passes to Engine as Unknown -> Neutral Fallback
    
    manual_lat = st.sidebar.number_input("或手动纬度 (Latitude)", -90.0, 90.0, 0.0, disabled=(selected_city!="Unknown")) # This disabled logic might be weird if I force Beijing, but it's fine for now (Beijing is known).

    # Era Control
    st.sidebar.subheader("⏳ 天时 (Era)")
    # Period 9 is 2024+. Allow simulation.
    selected_year = st.sidebar.slider("当前年份 (Year)", 2020, 2035, 2024)

    period = "Period 8 (Earth)" if selected_year < 2024 else "Period 9 (Fire)"
    st.sidebar.info(f"当前元运: **{period}**")

    # --- 2. ENGINE ANALYSIS ---
    lat_arg = None if selected_city != "Unknown" else (manual_lat if manual_lat != 0 else None)

    # Call Engine V9.1
    response = engine.analyze(
        bazi=selected_case['bazi'],
        day_master=selected_case['day_master'],
        city=selected_city,
        latitude=lat_arg,
        year=selected_year
    )
    
    # Guard Check: If Spacetime Engine fails (returns None), stop here.
    if response is None:
        st.error("Engine failed to generate analysis. (Calculation Returned None)")
        return

    # Extract Data
    energy = response.energy_distribution
    debug_info = response.debug.get("modifiers", {}) if response.debug else {}
    geo_mods = debug_info.get("geo_json", {})
    era_mults = debug_info.get("era_json", {})

    # --- 3. MAIN DISPLAY ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🌋 能量全息图 (Energy Hologram)")
        
        # Prepare DataFrame for Chart
        chart_data = []
        
        # Debug: Check if energy is empty
        if not energy:
            st.warning("⚠️ No energy data returned from engine.")
            st.json(response.model_dump()) 
        
        for elem, score in energy.items():
            # Get Modifiers
            e_mod = era_mults.get(elem, 1.0) if selected_year >= 2024 else 1.0 
            g_mod = geo_mods.get(elem, 1.0)
            total_mod = e_mod * g_mod
            
            base_score = score / total_mod if total_mod > 0 else score
            delta = score - base_score
            
            chart_data.append({
                "Element": elem.upper(),
                "Score": score,
                "Base": base_score,
                "Boost": delta,
                "Geo": f"x{g_mod:.2f}",
                "Era": f"x{e_mod:.2f}"
            })
            
        df_chart = pd.DataFrame(chart_data)
        
        # DEBUG: Force show data to confirm existence
        # st.caption("Debug: Chart Source Data")
        # st.dataframe(df_chart)
        
        if df_chart.empty:
             st.info("Chart data is empty.")
        else:
            # Render Bar Chart with Delta
            fig = go.Figure()
            
            # Base Layer
            fig.add_trace(go.Bar(
                x=df_chart['Element'],
                y=df_chart['Base'],
                name='Base Energy',
                marker_color='#BDC3C7'
            ))
            
            # Boost Layer
            fig.add_trace(go.Bar(
                x=df_chart['Element'],
                y=df_chart['Boost'],
                name='Spacetime Boost',
                marker_color=['#E74C3C' if v > 0 else '#3498DB' for v in df_chart['Boost']],
                text=[f"{v:+.1f}" for v in df_chart['Boost']],
                textposition='auto'
            ))
            
            fig.update_layout(barmode='stack', title="Base Energy + Spacetime Correction", height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🔍 时空因子 (Spacetime Modifiers)")
        
        # Display Verdict
        # Pydantic successfully converted dict back to object!
        verdict = response.strength.verdict
        adj_score = response.strength.adjusted_score
        
        st.metric("最终判定 (Verdict)", verdict, f"{adj_score:.1f}")
        
        st.markdown("### 🧬 Modifier Breakdown")
        
        if geo_mods.get('desc'):
            st.info(f"📍 **Geo**: {geo_mods['desc']}")
        
        if selected_year >= 2024:
            st.success(f"🔥 **Era**: Period 9 (离火运) Active")
        else:
            st.warning(f"⛰️ **Era**: Period 8 (艮土运) Active")
            
        # Table without gradient
        st.dataframe(
            df_chart[['Element', 'Geo', 'Era', 'Score']],
            hide_index=True,
            use_container_width=True
        )

    # Narrative / Interpretation
    st.markdown("---")
    st.subheader("📜 命运独白 (Narrative)")

    max_elem = max(energy, key=energy.get)
    narrative = f"在 **{selected_year}** 年的 **{selected_city}**，"
    narrative += f"天地之间 **{max_elem.upper()}** 能量最为强盛。"

    if geo_mods.get('fire', 1.0) > 1.1:
        narrative += " 此地火气炽热，助长了你的热情与行动力。"
    elif geo_mods.get('water', 1.0) > 1.1:
        narrative += " 此地寒气逼人，需注意冷静与沉淀。"

    if selected_year >= 2024 and 'fire' in energy and energy['fire'] > 15:
        narrative += " 借着九运离火的东风，正是大展宏图之时！"

    st.write(f"> {narrative}")

    # --- 4. LIFE HOLOGRAPHY (Restored Dimensions) ---
    st.markdown("---")
    st.subheader("🧬 命运全息图 (Destiny Hologram: 12-Year Dimensions)")
    st.caption("事业 (Career) · 财富 (Wealth) · 感情 (Relationship) 连续推演")
    
    if st.checkbox("启动全息推演 (Start Hologram)", value=True):
        trend_data = []
        handover_years = []
        last_luck_pillar = None
        
        progress_bar = st.progress(0)
        start_y = selected_year
        end_y = start_y + 12
        
        # Helper for GanZhi
        gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        base_year = 1924

        # Pre-construct Case Data
        # Ensure 'bazi' is list of strings
        c_bazi = selected_case['bazi']
        c_dm = selected_case['day_master']

        # [V9.3 Feature] Time Detective Integration
        # Attempt to rebuild Real Profile to get accurate Luck Cycles (Handover Lines)
        real_profile = None
        # Use cached lookup
        derived_dt_str = reverse_lookup_bazi(c_bazi, 1940, 2010)
        
        if derived_dt_str:
             try:
                 # Parse "YYYY-M-D H:00"
                 p_parts = derived_dt_str.split(' ')
                 p_date = p_parts[0].split('-')
                 p_time = p_parts[1].split(':')
                 dt_birth = datetime.datetime(int(p_date[0]), int(p_date[1]), int(p_date[2]), int(p_time[0]))
                 gender_idx = 1 if selected_case.get('gender', 'M') == 'M' else 0
                 real_profile = BaziProfile(dt_birth, gender_idx)
             except: pass

        # Construct Base Case Data
        base_case_data = {
            'id': selected_case.get('id', 0),
            'gender': 1 if selected_case.get('gender', 'M') == 'M' else 0,
            'day_master': c_dm,
            'bazi': c_bazi,
            'city': selected_city, # Forced Beijing if Unknown
            'physics_sources': {} # flux engine not active here, empty is fine for V9.1 defaults
        }

        for idx, y in enumerate(range(start_y, end_y)):
            try:
                # Calculate Year GanZhi
                offset = y - base_year
                l_gan = gan_chars[offset % 10]
                l_zhi = zhi_chars[offset % 12]
                l_gz = f"{l_gan}{l_zhi}"
                
                # [V9.3] Dynamic Luck Handover Detection
                # If we have a Real Profile (via Time Detective), use it.
                current_lp = "Unknown"
                if real_profile:
                     # Get Luck Pillar for this year
                     current_lp = real_profile.get_luck_pillar_at(y)
                     
                     # Check if changed from last year (or init)
                     if last_luck_pillar and current_lp != last_luck_pillar:
                          handover_years.append({'year': y, 'to': current_lp})
                     last_luck_pillar = current_lp
                     
                     # First year init
                     if idx == 0: last_luck_pillar = current_lp
                
                # Dynamic Context
                dyn_ctx = {'year': l_gz, 'dayun': current_lp}
                
                # 1. Geo Run (Selected City - Spacetime Enabled)
                safe_case_data_geo = copy.deepcopy(base_case_data)
                safe_case_data_geo['city'] = selected_city 
                energy_res_geo = engine.calculate_energy(safe_case_data_geo, dyn_ctx)
                
                # 2. Base Run (Neutral / Unknown - Baseline)
                safe_case_data_base = copy.deepcopy(base_case_data)
                safe_case_data_base['city'] = 'Unknown'
                energy_res_base = engine.calculate_energy(safe_case_data_base, dyn_ctx)
                
                # Extract Geo Scores (Main Lines)
                s_career = float(energy_res_geo.get('career') or 0.0)
                s_wealth = float(energy_res_geo.get('wealth') or 0.0)
                s_rel = float(energy_res_geo.get('relationship') or 0.0)
                desc = str(energy_res_geo.get('desc', ''))
                
                # Extract Base Scores (Ghost Lines)
                b_career = float(energy_res_base.get('career') or 0.0)
                b_wealth = float(energy_res_base.get('wealth') or 0.0)
                b_rel = float(energy_res_base.get('relationship') or 0.0)
                
                # Extract Domain Details for Key Events (Skull/Key) - From Geo Run
                dom_det = energy_res_geo.get('domain_details', {})
                is_tr_open = dom_det.get('is_treasury_open', False)
                tr_icon = dom_det.get('icon', '🗝️') if is_tr_open else ''
                tr_risk = dom_det.get('risk_level', 'low')
                
                row = {
                    "year": y,
                    "career": s_career,
                    "wealth": s_wealth,
                    "relationship": s_rel,
                    "desc": f"{y} {l_gz}\n{desc[:50]}...",
                    "is_treasury_open": is_tr_open,
                    "treasury_icon": tr_icon,
                    "treasury_risk": tr_risk,
                    # Base Data
                    "base_career": b_career,
                    "base_wealth": b_wealth,
                    "base_relationship": b_rel
                }
                trend_data.append(row)
                
            except Exception as e:
                st.error(f"Loop Error {y}: {e}")
                pass
            
            progress_bar.progress((idx + 1) / 12)
            
        progress_bar.empty()
        
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            
            # --- Render Rich Chart (Ported from DestinyCharts) ---
            fig = go.Figure()
            
            # Base Layer (Ghost Lines - Neutral Geo)
            # This shows what the destiny would be without Location Modifier
            fig.add_trace(go.Scatter(
                x=df_trend['year'], y=df_trend['base_career'],
                mode='lines', name='原生 (Base - No Geo)',
                line=dict(color='rgba(0, 229, 255, 0.3)', width=2, dash='dot'),
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=df_trend['year'], y=df_trend['base_wealth'],
                mode='lines', showlegend=False,
                line=dict(color='rgba(255, 215, 0, 0.3)', width=2, dash='dot'),
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=df_trend['year'], y=df_trend['base_relationship'],
                mode='lines', showlegend=False,
                line=dict(color='rgba(245, 0, 87, 0.3)', width=2, dash='dot'),
                hoverinfo='skip'
            ))
            
            # Geo Layer (Main Lines - Selected City)
            fig.add_trace(go.Scatter(x=df_trend['year'], y=df_trend['career'], mode='lines+markers', name='事业 (Career)', line=dict(color='#00E5FF', width=3), hovertext=df_trend['desc']))
            fig.add_trace(go.Scatter(x=df_trend['year'], y=df_trend['wealth'], mode='lines+markers', name='财富 (Wealth)', line=dict(color='#FFD700', width=3), hovertext=df_trend['desc']))
            fig.add_trace(go.Scatter(x=df_trend['year'], y=df_trend['relationship'], mode='lines+markers', name='感情 (Rel)', line=dict(color='#F50057', width=3), hovertext=df_trend['desc']))
            
            # Treasury Icons
            treasury_rows = df_trend[df_trend['is_treasury_open'] == True]
            if not treasury_rows.empty:
                # Y position: max of 3 lines + offset
                t_y = [max(r['career'], r['wealth'], r['relationship']) + 1.5 for _, r in treasury_rows.iterrows()]
                t_colors = ['#FF0000' if r['treasury_risk'] == 'danger' or r['treasury_risk'] == 'warning' else '#FFD700' for _, r in treasury_rows.iterrows()]
                
                fig.add_trace(go.Scatter(
                    x=treasury_rows['year'], y=t_y,
                    mode='text', text=treasury_rows['treasury_icon'],
                    textposition="top center", textfont=dict(size=24),
                    marker=dict(color=t_colors), name='库门事件', showlegend=False
                ))

            # Handover Lines
            for h in handover_years:
                fig.add_vline(x=h['year'], line_width=2, line_dash="dash", line_color="rgba(255,255,255,0.6)", annotation_text=f"🔄 换运 {h['to']}")

            fig.update_layout(
                title=f"🏛️ 命运全息图 (Destiny Hologram) - {start_y}~{end_y-1}",
                yaxis=dict(title="能量级 (Score)", range=[-15, 15]),
                xaxis=dict(title="年份 (Year)", tickmode='linear', dtick=1),
                height=500,
                legend=dict(orientation="h", y=-0.2),
                plot_bgcolor='rgba(0,0,0,0.05)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("查看详细数据 (Data Table)"):
                st.dataframe(df_trend)
        else:
            st.error("无法生成全息数据。")


    
    # Raw Debug
    with st.expander("🔬 Engine Trace"):
        st.text("\n".join(response.messages))

if __name__ == "__main__":
    render()
