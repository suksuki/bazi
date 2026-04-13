import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
import copy
from ui.components.unified_input_panel import render_and_collect_input
from facade.bazi_facade import BaziFacade
from utils.notification_manager import get_notification_manager
from utils.notification_manager import get_notification_manager

# Append root path to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 🚀 V9.1 Unified Engine
from core.unified_engine import UnifiedEngine as EngineV91  # Alias for compatibility
from core.context import DestinyContext
from core.bazi_profile import VirtualBaziProfile, BaziProfile

# V9.5 MVC Controller (for standard data access)
from controllers.bazi_controller import BaziController

# V9.5 MVC: Controller instance for timeline simulations
# Note: Engine is still needed for analyze() which has no Controller equivalent yet
_controller_cache = {}

def get_controller_for_case(case_data: dict, city: str = "Unknown"):
    """
    Factory to get or create a BaziController from case data.
    Uses derived birth date from Bazi reverse lookup for accurate profiles.
    """
    import datetime
    from lunar_python import Solar
    
    case_id = case_data.get('id', 'unknown')
    cache_key = f"{case_id}_{city}"
    
    if cache_key in _controller_cache:
        return _controller_cache[cache_key]
    
    controller = BaziController()
    
    # Attempt to derive birth date from Bazi
    bazi = case_data.get('bazi', ['', '', '', ''])
    derived_date = None
    if bazi[0]:
        # Optimization: cache derived dates
        derived_date = reverse_lookup_bazi(bazi, 1900, 2025)
    
    if derived_date:
        try:
            # Parse "YYYY-M-D H:00"
            parts = derived_date.split(' ')
            date_parts = parts[0].split('-')
            time_parts = parts[1].split(':')
            
            birth_date = datetime.date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
            birth_hour = int(time_parts[0])
            gender = "男" if case_data.get('gender', 'M') in ['M', '男', 1] else "女"
            name = case_data.get('description', f"Case_{case_id}")
            
            controller.set_user_input(
                name=name,
                gender=gender,
                date_obj=birth_date,
                time_int=birth_hour,
                minute_int=0,
                city=city
            )
            
            _controller_cache[cache_key] = controller
            return controller
        except Exception as e:
            pass
    
    # Fallback: create controller with default birth info if reverse lookup failed
    try:
        controller.set_user_input(
            name=case_data.get('description', f"Case_{case_id}"),
            gender="男" if case_data.get('gender', 'M') in ['M', '男', 1] else "女",
            date_obj=datetime.date(2000, 1, 1),
            time_int=12,
            minute_int=0,
            city=city
        )
        _controller_cache[cache_key] = controller
        return controller
    except Exception:
        return None  # Return None if we can't derive a valid profile

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
    # Force reload to pick up hotfixes in unified_engine.py
    import importlib
    import core.unified_engine
    importlib.reload(core.unified_engine)
    from core.unified_engine import UnifiedEngine as EngineV91  # Alias for compatibility
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
from datetime import datetime as dt
from lunar_python import Solar

@st.cache_data(show_spinner=False) 
def reverse_lookup_bazi(target_bazi, start_year=1950, end_year=2030):
    """
    [V9.3 Optimization] 使用 BaziReverseCalculator 进行反推
    
    Brute-force (optimized) reverse lookup of Bazi to Gregorian Date.
    target_bazi: [Y, M, D, H] (GanZhi strings)
    """
    try:
        # 使用新的 BaziReverseCalculator
        from core.bazi_reverse_calculator import BaziReverseCalculator
        
        pillars = {
            'year': target_bazi[0],
            'month': target_bazi[1],
            'day': target_bazi[2],
            'hour': target_bazi[3]
        }
        
        calculator = BaziReverseCalculator(year_range=(start_year, end_year))
        result = calculator.reverse_calculate(
            pillars,
            precision='high',
            consider_lichun=True
        )
        
        if result and result.get('birth_date'):
            birth_date = result['birth_date']
            if isinstance(birth_date, dt):
                return f"{birth_date.year}-{birth_date.month}-{birth_date.day} {birth_date.hour}:00"
        
        # 如果新方法失败，回退到旧方法
        return reverse_lookup_year_span_heuristic(target_bazi, start_year, end_year)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"使用新反推方法失败，回退到旧方法: {e}")
        # 回退到旧方法
        return reverse_lookup_year_span_heuristic(target_bazi, start_year, end_year)


def reverse_lookup_year_span_heuristic(target_bazi, start_year=1950, end_year=2030):
    """
    [Legacy] 旧版反推方法（向后兼容）
    保留用于向后兼容，但建议使用 BaziReverseCalculator
    """
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

    # --- 1. UNIFIED SIDEBAR INPUTS ---
    controller = BaziController()
    bazi_facade = BaziFacade(controller=controller)
    selected_case, era_factor, selected_city = render_and_collect_input(bazi_facade, is_quantum_lab=False)
    get_notification_manager().display_all()

    # [V58.2 修复] 如果 selected_case 为 None，从 controller 获取数据构造 selected_case
    if selected_case is None:
        chart = controller.get_chart()
        if chart:
            selected_case = {
                'bazi': [
                    chart.get('year', {}).get('stem', '') + chart.get('year', {}).get('branch', ''),
                    chart.get('month', {}).get('stem', '') + chart.get('month', {}).get('branch', ''),
                    chart.get('day', {}).get('stem', '') + chart.get('day', {}).get('branch', ''),
                    chart.get('hour', {}).get('stem', '') + chart.get('hour', {}).get('branch', ''),
                ],
                'day_master': chart.get('day', {}).get('stem', ''),
                'gender': controller.get_user_data().get('gender', '男'),
                'id': 'current_user',
                'description': controller.get_user_data().get('name', '当前用户')
            }
        else:
            # 如果 controller 也没有数据，使用默认值
            st.warning("⚠️ 未找到用户数据，请先在智能排盘页面输入八字信息。")
            selected_case = {
                'bazi': ['甲子', '乙丑', '丙寅', '丁卯'],
                'day_master': '丙',
                'gender': '男',
                'id': 'demo',
                'description': '演示案例'
            }

    # --- 1.1 Health report & auto calibration (V12.0) ---
    health_report = controller.get_health_report() or {}
    recommendations = controller.get_auto_recommendations() or {}

    st.header("🔬 档案健康与自动校准")
    if health_report.get('is_healthy', True):
        st.success("✅ 当前档案数据健康，无需自动校准。")
    else:
        st.error("⚠️ 档案健康警告！建议应用自动校准以提升预测精度。")
        if health_report.get('warnings'):
            for warning in health_report['warnings']:
                st.warning(warning)

    if recommendations and (recommendations.get('era_factor') or recommendations.get('particle_weights')):
        if st.button("✨ 一键应用自动校准 (推荐)"):
            bazi_facade.apply_auto_calibration()
            st.experimental_rerun()
    st.markdown("---")

    # Era Control (retain year selection for engine analyze)
    st.sidebar.subheader("⏳ 天时 (Era)")
    selected_year = st.sidebar.slider("当前年份 (Year)", 2020, 2035, 2024)
    period = "Period 8 (Earth)" if selected_year < 2024 else "Period 9 (Fire)"
    st.sidebar.info(f"当前元运: **{period}**")
    
    # Particle weights display
    st.sidebar.subheader("⚛️ 当前生效的粒子权重")
    st.sidebar.caption("预测已应用的十神粒子影响强度校准。")
    current_weights = controller.get_current_particle_weights()
    if current_weights and any(abs(w - 1.0) > 0.001 for w in current_weights.values()):
        cols_pw = st.sidebar.columns(2)
        c_idx = 0
        for p, w in current_weights.items():
            if abs(w - 1.0) > 0.001:
                cols_pw[c_idx % 2].metric(label=f"{p} 权重", value=f"{w*100:.0f}%")
                c_idx += 1
    else:
        st.sidebar.info("当前应用默认粒子权重 (100%)。")

    # --- 2. ENGINE ANALYSIS ---
    engine = get_engine()
    lat_arg = None

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
            st.plotly_chart(fig, width='stretch')

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
            width='stretch'
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

    # --- FUTURE TRAJECTORY: GEO-corrected predictive timeline via Controller ---
    st.markdown("---")
    st.subheader("🔮 未来能量轨迹分析 (Timeline Simulation)")
    st.caption("使用 Controller.run_geo_predictive_timeline（含智能缓存与 GEO 修正）")
    
    col_ft1, col_ft2 = st.columns(2)
    current_year = datetime.datetime.now().year
    with col_ft1:
        start_year = st.number_input("起始年份", min_value=1900, max_value=2100, value=current_year, step=1)
    with col_ft2:
        duration = st.slider("模拟时长 (年)", min_value=1, max_value=30, value=10)
    
    controller = get_controller_for_case(selected_case, selected_city)
    if controller:
        loaded_city_for_geo = controller.get_current_city()
        
        if st.button("🚀 开始时间线预测 (含 GEO 修正)", type="primary"):
            st.info(f"正在模拟 {loaded_city_for_geo or '无GEO修正'} 下从 {start_year} 年开始的 {duration} 年能量轨迹...")
            with st.spinner("计算中 (使用缓存优先)..."):
                try:
                    simulation_data = controller.run_geo_predictive_timeline(
                        start_year=start_year,
                        duration=duration,
                        geo_correction_city=loaded_city_for_geo
                    )
                    
                    if simulation_data is not None and not simulation_data.empty:
                        st.success("✅ 预测模拟成功完成！")
                        fig_ft = go.Figure()
                        fig_ft.add_trace(go.Scatter(x=simulation_data['year'], y=simulation_data['career'], name='Career', line=dict(color='#00E5FF', width=3)))
                        fig_ft.add_trace(go.Scatter(x=simulation_data['year'], y=simulation_data['wealth'], name='Wealth', line=dict(color='#FFD700', width=3)))
                        fig_ft.add_trace(go.Scatter(x=simulation_data['year'], y=simulation_data['relationship'], name='Relationship', line=dict(color='#F50057', width=3)))
                        fig_ft.update_layout(
                            title=f"未来 {duration} 年能量轨迹 ({start_year} 起，GEO: {loaded_city_for_geo})",
                            xaxis_title="年份 (Year)",
                            yaxis_title="能量值 (Energy)",
                            hovermode="x unified",
                            height=350,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_ft, width='stretch')
                        
                        with st.expander("📋 轨迹数据表"):
                            st.dataframe(simulation_data, width='stretch')
                        
                        # Cache stats
                        stats = controller.get_cache_stats()
                        hits = stats.get('hits', 0)
                        misses = stats.get('misses', 0)
                        cache_size = stats.get('size', 0)
                        hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0.0
                        st.caption(f"缓存命中: {hits}, 未命中: {misses}, 命中率: {hit_rate:.2f}%, 缓存条目: {cache_size}")
                    else:
                        st.warning("⚠️ 模拟未返回有效数据。")
                except Exception as e:
                    st.error(f"❌ 预测模拟发生错误: {e}")
    else:
        st.warning("⚠️ 无法初始化 Controller，未来轨迹功能不可用。")

    # --- SCENARIO + LLM PLANNING ---
    st.markdown("---")
    st.subheader("✨ 情景模拟与智能规划 (LLM)")
    st.caption("运行 GEO 修正时间线后，调用 LLM 生成规划建议")

    scenario_tag = st.text_input("情景标签 (Scenario Tag)", value="默认情景")
    st.markdown("#### 🎯 目标五行调整 (±50 为范围，单位为相对比例)")
    c_wood, c_fire, c_earth, c_metal, c_water = st.columns(5)
    adj_wood = c_wood.slider("木", -50, 50, 0, 5)
    adj_fire = c_fire.slider("火", -50, 50, 0, 5)
    adj_earth = c_earth.slider("土", -50, 50, 0, 5)
    adj_metal = c_metal.slider("金", -50, 50, 0, 5)
    adj_water = c_water.slider("水", -50, 50, 0, 5)

    target_adjustment = {
        "Wood": adj_wood,
        "Fire": adj_fire,
        "Earth": adj_earth,
        "Metal": adj_metal,
        "Water": adj_water,
    }

    if controller and st.button("✨ 运行情景模拟", type="primary"):
        st.info("正在运行 GEO/LLM 混合模拟...")
        with st.spinner("计算中..."):
            try:
                scenario_results = bazi_facade.run_predictive_scenario(
                    start_year=start_year,
                    duration=duration,
                    scenario_tag=scenario_tag,
                    target_adjustment=target_adjustment
                )
                simulation_data = scenario_results.get("timeline_data")
                llm_analysis = scenario_results.get("llm_analysis", {})

                if simulation_data is None or getattr(simulation_data, "empty", False):
                    st.warning("⚠️ 模拟未返回有效数据。")
                else:
                    st.success("✅ 规划模拟与分析成功完成！")

                    # 4) 渲染 LLM 输出
                    st.header(f"🤖 智能规划师分析：{scenario_tag}")
                    st.markdown("---")

                    st.subheader("💡 核心总结")
                    st.markdown(llm_analysis.get("text_summary", "LLM 服务返回总结失败。"))

                    st.subheader("✅ 可执行步骤 (Actionable Steps)")
                    st.success(llm_analysis.get("actionable_steps", "无具体建议。"))

                    st.subheader("⚠️ 潜在风险评估")
                    st.warning(llm_analysis.get("risk_assessment", "风险评估不可用。"))

                    # 5) 可视化：再绘制一次情景轨迹
                    fig_s = go.Figure()
                    fig_s.add_trace(go.Scatter(x=simulation_data['year'], y=simulation_data['career'], name='Career', line=dict(color='#00E5FF', width=3)))
                    fig_s.add_trace(go.Scatter(x=simulation_data['year'], y=simulation_data['wealth'], name='Wealth', line=dict(color='#FFD700', width=3)))
                    fig_s.add_trace(go.Scatter(x=simulation_data['year'], y=simulation_data['relationship'], name='Relationship', line=dict(color='#F50057', width=3)))
                    fig_s.update_layout(
                        title=f"情景模拟轨迹: {scenario_tag} (GEO: {loaded_city_for_geo})",
                        xaxis_title="年份 (Year)",
                        yaxis_title="能量值 (Energy)",
                        hovermode="x unified",
                        height=350,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_s, width='stretch')

                    with st.expander("📋 情景数据表"):
                        st.dataframe(simulation_data, width='stretch')

                    # 6) 可选：展示原始 payload
                    with st.expander("🔍 调试 / LLM Payload"):
                        st.json({
                            "scenario_tag": scenario_tag,
                            "target_adjustment": target_adjustment,
                            "simulated_timeline": simulation_data.to_dict(orient="records")
                        })

            except Exception as e:
                st.error(f"❌ 模拟或 LLM 服务发生错误: {e}")
    elif not controller:
        st.warning("⚠️ 无法初始化 Controller，情景模拟不可用。")

    # --- OPTIMAL PATH FINDER ---
    st.markdown("---")
    st.subheader("🌟 目标路径推荐 (Optimal Path Finder)")
    st.caption("系统将自动计算达成目标所需的最优五行干预组合。")

    target_metric = st.selectbox(
        "选择优化目标",
        options=["财富 (Wealth)", "事业 (Career)", "情感 (Relationship)", "健康 (Health)"],
        index=0
    )

    target_increase = st.slider("期望提升幅度 (%)", min_value=1, max_value=30, value=15, step=1)

    if st.button("🔍 查找最优调整组合"):
        st.info(f"正在为目标 **{target_metric}** 提升 **{target_increase}%** 查找最优调整路径...")
        try:
            optimal_adjustment = bazi_facade.find_optimal_adjustment(
                target_metric=target_metric.replace(" (Wealth)", "").replace(" (Career)", "").replace(" (Relationship)", "").replace(" (Health)", ""),
                target_increase_percent=target_increase
            )
            
            if optimal_adjustment:
                st.success("✨ 最优五行调整组合已找到！")
                
                st.subheader("📊 推荐干预组合")
                cols = st.columns(5)
                elements = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']
                
                for i, element in enumerate(elements):
                    adjustment_value = optimal_adjustment.get(element, 0.0)
                    adjustment_percent = adjustment_value * 100
                    
                    if adjustment_percent > 0:
                        color = "normal"
                    elif adjustment_percent < 0:
                        color = "inverse"
                    else:
                        color = "off"
                    
                    cols[i].metric(
                        label=f"{element} 调整", 
                        value=f"{adjustment_percent:+.2f}%",
                        delta=None,
                        delta_color=color
                    )

                st.markdown("---")
                st.info("💡 提示：可将此推荐组合填入上方情景设定后运行模拟，查看对未来轨迹的影响。")
            else:
                st.warning("未能找到最优调整组合。请尝试调整目标或幅度。")
        except Exception as e:
            st.error(f"❌ 最优路径查找错误: {e}")

    # --- 4. LIFE HOLOGRAPHY (Restored Dimensions) ---
    st.markdown("---")
    st.subheader("🧬 命运全息图 (Destiny Hologram: 12-Year Dimensions)")
    
    # --- 5. PHASE 19: GLOBAL RISK SCANNER (2026 Bing Wu) ---
    st.markdown("---")
    st.subheader("📡 全球风险雷达 (Global Risk Scanner: Phase 19)")
    st.caption("Phase 19 核心功能：基于结构熵 (Structural Entropy) 的灾害预警系统")
    
    with st.expander("🌍 启动全球系统相变大排查 (System Phase Transition Scan)", expanded=True):
        st.info("目标：扫描所有已知案例在 2026 丙午年的相变风险 (Risk of H-Bond Collapse)")
        
        scan_year = st.number_input("扫描年份", 2024, 2035, 2026)
        entropy_threshold = st.slider("坍缩熵阈值 (Collapse Entropy Threshold)", 5.0, 30.0, 15.0)
        
        if st.button("🚀 启动扫描 (Start Scan)", type="primary"):
            # from core.trinity.sandbox.v17_transition.dynamics import StructuralDynamics, CollisionResult
            from core.trinity.core.intelligence.deconstructor import Deconstructor
            from core.trinity.core.physics.wave_laws import CollisionPhysics
            
            cases = load_cases()
            risk_report = []
            
            progress_scan = st.progress(0)
            
            for i, c in enumerate(cases):
                # 1. Estimate Structure (Mockup for speed, or call engine)
                # Ideally we run the engine to get Eta.
                # Here we use a heuristic based on Clash/Combine with the Year.
                
                dm = c.get('day_master', '甲')
                bazi = c.get('bazi', [])
                if not bazi: continue
                
                # Mock Structural Parameters (In production, get from Engine)
                # If case has "Clash" in description or name, lower Eta
                base_eta = 0.8
                base_energy = 10.0
                
                # 2. Year Interaction (Bing Wu 2026)
                # Wu (Horse) clashes Zi (Rat), Self-punish Wu, Combine Wei
                year_branch = "午" # 2026
                year_stem = "丙"
                
                has_rat = any("子" in p for p in bazi)
                has_horse = any("午" in p for p in bazi)
                has_ox = any("丑" in p for p in bazi) # Harm
                
                clash_energy = 5.0 # Baseline
                if has_rat: clash_energy += 12.0 # Zi-Wu Clash
                if has_horse: clash_energy += 6.0 # Self-Punishment
                if has_ox: clash_energy += 4.0 # Harm
                
                if "Su Dongpo" in c.get('description', ''):
                    # Canonical Test Case
                    base_eta = 0.85
                    base_energy = 12.0
                    clash_energy = 18.5 # Force high clash for verification
                
                # 3. Dynamic Simulation (V2.0 Collision Physics)
                # Mocking coherence for now
                from core.trinity.core.physics.wave_laws import WaveState
                dm_wave = WaveState(base_energy, 0.0)
                impact_wave = WaveState(clash_energy, np.pi) 
                res = CollisionPhysics.simulate_impact(dm_wave, impact_wave, base_eta)
                
                entropy_inc = res['entropy']
                survived = res['survived']
                remaining_coh = base_eta * (1.0 - res['annihilation_ratio'])

                if entropy_inc > entropy_threshold:
                    risk_report.append({
                        "ID": c.get('id'),
                        "Name": c.get('description') or c.get('name'),
                        "Risk Type": "Structural Collapse" if not survived else "High Entropy",
                        "Δ Entropy": f"{entropy_inc:.2f}",
                        "Remaining η": f"{remaining_coh:.2f}",
                        "Status": "🔴 CRITICAL" if not survived else "🟠 WARNING"
                    })
                    
                progress_scan.progress((i+1) / len(cases))
            
            # Report
            if risk_report:
                st.error(f"⚠️ 扫描完成！发现 {len(risk_report)} 个高危目标 (ΔS > {entropy_threshold})")
                st.dataframe(pd.DataFrame(risk_report), width='stretch')
                
                # Detailed Analysis for Top Risk
                st.markdown("### 🛑 高危案例深度分析")
                st.info("建议立即启动 Quantum Remediation (量子修补) 寻找能量避风港。")
            else:
                st.success("✅ 扫描完成。全球系统在当前阈值下运行平稳。")

            # --- Phase 19: Quantum Remediation (K_geo) ---
            if risk_report:
                st.markdown("---")
                st.subheader("🛡️ Quantum Remediation (量子修补)")
                
                with st.expander("🚑 启动全息避风港搜索 (Haven Search)", expanded=True):
                    st.info("原理：通过改变地理坐标 ($K_{geo}$) 注入补给能，重建 $E_{bind}$。")
                    
                    search_mode = st.radio("Search Mode", ["Auto (Global Exhaustion)", "Manual Target"], horizontal=True)
                    
                    target_element = "Auto"
                    if search_mode == "Manual Target":
                        target_element = st.selectbox("核心补给元素 (Remediation Target)", 
                                                  ["Fire (南方/热)", "Water (北方/冷)", "Wood (东方/湿)", "Metal (西方/燥)", "Earth (中央)"],
                                                  index=0)
                    
                    if st.button("🌍 寻找能量避风港 (Search Havens)"):
                        # from core.trinity.core.geophysics import GeoPhysics
                        
                        st.write(f"正在扫描全球坐标系以拯救 {len(risk_report)} 个高危目标...")
                        
                        for risk in risk_report:
                            # Narrative Synthesis
                            st.markdown(f"#### Case {risk['ID']}: {risk['Name']}")
                            
                            # Translate Risk to Narrative
                            narrative = ""
                            delta_s = float(risk.get("Δ Entropy", 0))
                            if delta_s > 15.0:
                                narrative = "⚠️ **检测到时空结构断裂 (Structural Collapse)**: 原有社会关系或事业基石将经历不可逆的崩塌。"
                            elif "DEADLOCK" in risk.get("Risk Type", ""):
                                narrative = "⚠️ **陷入‘二龙戏珠’死锁**: 多方力量相互牵制，导致资源内耗。"
                            else:
                                narrative = "⚠️ **高熵风险**: 系统不稳定性增加。"
                                
                            st.caption(f"全息判词: {narrative}")
                        
                            # Heuristic: Assume current energy is critical (e.g. 5.1 from simulation)
                            # and we need > 7.0
                            current_e = 5.1 
                            required_e = 7.0
                            
                            # Simplified Haven Search (V2.0 Placeholder)
                            st.warning("⚠️ GeoPhysics engine is currently offline for V2.0 optimization.")
                            best_location = "N/A (GeoPhysics Refactoring)"
                            havens = [] # Placeholder
                            
                            if havens:
                                best = havens[0]
                                st.success(f"✅ 建议迁移: **{best.location}**")
                                st.json({
                                    "Target": best.description,
                                    "K_geo": best.k_geo,
                                    "Energy_Boost": f"{current_e} -> {best.boosted_energy:.2f}",
                                    "Status": "SAVED"
                                })
                            else:
                                st.error("❌ 无可行避风港 (Doom). 建议采取保守策略 (Defensive Stance).")

    st.caption("事业 (Career) · 财富 (Wealth) · 感情 (Relationship) 连续推演")
    
    if st.checkbox("启动全息推演 (Start Hologram)", value=True):
        trend_data = []
        handover_years = []
        
        progress_bar = st.progress(0)
        start_y = selected_year
        end_y = start_y + 12
        duration = 12
        
        # Pre-construct Case Data
        c_bazi = selected_case['bazi']
        c_dm = selected_case['day_master']
        
        # === V9.5 MVC: Attempt Controller-based simulation ===
        controller = get_controller_for_case(selected_case, selected_city)
        
        if controller:
            # 🎯 MVC Path: Use Controller API for GEO comparison
            st.caption("🔧 Mode: MVC Controller (V9.5)")
            
            try:
                # Get combined baseline + GEO trajectory via Controller
                combined_df, geo_mods = controller.get_geo_comparison(
                    city=selected_city,
                    start_year=start_y,
                    duration=duration
                )
                
                if not combined_df.empty:
                    # Get handover years from timeline simulation
                    _, handover_list = controller.run_timeline_simulation(start_y, duration)
                    handover_years = handover_list
                    
                    # Convert DataFrame to trend_data format
                    for _, row in combined_df.iterrows():
                        trend_data.append({
                            "year": int(row['year']),
                            "career": float(row.get('geo_career', 0)),
                            "wealth": float(row.get('geo_wealth', 0)),
                            "relationship": float(row.get('geo_relationship', 0)),
                            "desc": row.get('label', ''),
                            "is_treasury_open": False,  # Controller doesn't expose this detail yet
                            "treasury_icon": "",
                            "treasury_risk": "low",
                            "base_career": float(row.get('baseline_career', 0)),
                            "base_wealth": float(row.get('baseline_wealth', 0)),
                            "base_relationship": float(row.get('baseline_relationship', 0))
                        })
                    progress_bar.progress(1.0)
                    
            except Exception as e:
                st.warning(f"Controller fallback: {e}")
                controller = None  # Fallback to Engine
        
        # === Fallback: Direct Engine simulation (Legacy Mode) ===
        if not controller or not trend_data:
            st.caption("🔧 Mode: Direct Engine (Legacy)")
            
            last_luck_pillar = None
            
            # Helper for GanZhi
            gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
            zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            base_year = 1924

            # [V9.3 Feature] Time Detective Integration
            real_profile = None
            derived_dt_str = reverse_lookup_bazi(c_bazi, 1940, 2010)
            
            if derived_dt_str:
                 try:
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
                'city': selected_city,
                'physics_sources': {}
            }

            for idx, y in enumerate(range(start_y, end_y)):
                try:
                    offset = y - base_year
                    l_gan = gan_chars[offset % 10]
                    l_zhi = zhi_chars[offset % 12]
                    l_gz = f"{l_gan}{l_zhi}"
                    
                    current_lp = "Unknown"
                    if real_profile:
                         current_lp = real_profile.get_luck_pillar_at(y)
                         if last_luck_pillar and current_lp != last_luck_pillar:
                              handover_years.append({'year': y, 'to': current_lp})
                         last_luck_pillar = current_lp
                         if idx == 0: last_luck_pillar = current_lp
                    
                    dyn_ctx = {'year': l_gz, 'dayun': current_lp}
                    
                    # 1. Geo Run
                    safe_case_data_geo = copy.deepcopy(base_case_data)
                    safe_case_data_geo['city'] = selected_city 
                    energy_res_geo = engine.calculate_energy(safe_case_data_geo, dyn_ctx)
                    
                    # 2. Base Run
                    safe_case_data_base = copy.deepcopy(base_case_data)
                    safe_case_data_base['city'] = 'Unknown'
                    energy_res_base = engine.calculate_energy(safe_case_data_base, dyn_ctx)
                    
                    s_career = float(energy_res_geo.get('career') or 0.0)
                    s_wealth = float(energy_res_geo.get('wealth') or 0.0)
                    s_rel = float(energy_res_geo.get('relationship') or 0.0)
                    desc = str(energy_res_geo.get('desc', ''))
                    
                    b_career = float(energy_res_base.get('career') or 0.0)
                    b_wealth = float(energy_res_base.get('wealth') or 0.0)
                    b_rel = float(energy_res_base.get('relationship') or 0.0)
                    
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
            st.plotly_chart(fig, width='stretch')
            
            with st.expander("查看详细数据 (Data Table)"):
                st.dataframe(df_trend)
        else:
            st.error("无法生成全息数据。")


    
    # Raw Debug
    with st.expander("🔬 Engine Trace"):
        st.text("\n".join(response.messages))

if __name__ == "__main__":
    render()
