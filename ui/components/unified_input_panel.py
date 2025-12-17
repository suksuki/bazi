import streamlit as st
import json
import os
import datetime
from typing import Dict, List, Optional, Tuple, Any

from utils.constants_manager import get_constants

from facade.bazi_facade import BaziFacade


def _load_cases() -> List[Dict[str, Any]]:
    """
    Load prediction archives/cases from external data.
    """
    path = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _load_geo_cities() -> List[str]:
    """
    Load available GEO cities from geo_coefficients.json.
    """
    geo_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
    try:
        with open(geo_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return list(data.get("cities", {}).keys())
    except Exception:
        return ["Unknown", "Beijing", "Shanghai", "Guangzhou", "Singapore"]


def render_and_collect_input(facade: BaziFacade,
                             cases: Optional[List[Dict[str, Any]]] = None,
                             is_quantum_lab: bool = False) -> Tuple[Optional[Dict[str, Any]], Dict[str, float], str]:
    """
    渲染统一输入面板，收集档案/GEO/ERA 输入，并刷新 Controller 状态。

    Args:
        controller: BaziController 实例
        cases: 可选的档案列表；若不提供则默认从 calibration_cases.json 加载
        is_quantum_lab: 是否处于 P2 量子验证页面（允许 ERA 可调）

    Returns:
        (selected_case, era_factor_dict, selected_city)
    """
    controller = facade._controller
    consts = get_constants()

    with st.sidebar:

        # --- 档案选择（仅量子验证页面） ---
        selected_case = None
        if is_quantum_lab:
            # 量子验证页面需要档案选择
            if cases is None:
                cases = _load_cases()

            if cases:
                case_options = {f"{c.get('id', 'NA')} - {c.get('description', 'Case')}": c for c in cases}
                selected_case_name = st.selectbox("🎭 选择档案 (Archive)", list(case_options.keys()))
                selected_case = case_options[selected_case_name]
            else:
                st.warning("未找到预测档案数据，使用默认示例。")
                selected_case = {
                    "id": "DEMO",
                    "description": "Demo Case",
                    "bazi": ["甲子", "乙丑", "丙寅", "丁卯"],
                    "day_master": "丙",
                    "gender": "男",
                }

        # --- GEO 城市选择 ---
        # [V56.3] GEO 修正城市已移到 input_form.py 中（在"启用真太阳时"之后）
        # 这里从 session_state 读取已选择的城市
        selected_city = st.session_state.get("unified_geo_city", "None")
        city_for_controller = "Unknown" if selected_city == "None" else selected_city

        # --- ERA 因子 ---
        era_factor: Dict[str, float] = {}
        if is_quantum_lab:
            # 在 ERA 调节前展示档案概要（仅量子验证页面）
            if isinstance(selected_case, dict) and selected_case:
                st.subheader("档案信息")
                st.markdown(f"- 档案ID: {selected_case.get('id', 'Unknown')}")
                st.markdown(f"- 性别: {selected_case.get('gender', '未知')}")
                st.markdown(f"- 日主: {selected_case.get('day_master', '?')}")
                bazi_list = selected_case.get("bazi", [])
                bazi_str = " | ".join(bazi_list) if bazi_list else "未提供"
                st.markdown(f"- 八字: {bazi_str}")
                birth_date = selected_case.get("birth_date", "")
                birth_time = selected_case.get("birth_time", "")
                st.markdown(f"- 推断公历: {birth_date} {birth_time}".strip())
            st.subheader("🌐 ERA 时代修正 (可调)")
            cols = st.columns(len(consts.FIVE_ELEMENTS))
            prefix = st.session_state.get("era_key_prefix", "era")
            for idx, elem in enumerate(consts.FIVE_ELEMENTS):
                label_map = {
                    "Wood": "木",
                    "Fire": "火",
                    "Earth": "土",
                    "Metal": "金",
                    "Water": "水",
                }
                era_factor[elem] = cols[idx].slider(
                    f"{label_map.get(elem, elem)} (ERA %)", -10, 10, 0, key=f"{prefix}_{elem.lower()}"
                ) / 100
        else:
            st.subheader("🌐 ERA 时代修正 (当前生效)")
            current_era = controller.get_current_era_factor() if controller else {}
            if current_era and any(current_era.values()):
                cols = st.columns(3)
                elements = consts.FIVE_ELEMENTS
                c_idx = 0
                for elem in elements:
                    factor = current_era.get(elem, 0.0) * 100
                    if abs(factor) > 0.001:
                        cols[c_idx % 3].metric(label=elem, value=f"{factor:+.1f}%")
                        c_idx += 1
                era_factor = current_era
            else:
                st.info("当前未应用 ERA 因子。")
                era_factor = {}

        # --- 构造用户输入并通过 Facade 刷新 Controller ---
        controller = facade._controller
        
        # 智能排盘页面：从 session_state 读取输入表单的数据
        if not is_quantum_lab:
            # 从 session_state 读取输入表单的数据（档案管理或手动输入）
            name = st.session_state.get("input_name", "某人")
            gender = st.session_state.get("input_gender", "男")
            input_date = st.session_state.get("input_date")
            input_time = st.session_state.get("input_time", 12)
            input_longitude = st.session_state.get("input_longitude", 116.46)
            input_enable_solar = st.session_state.get("input_enable_solar_time", True)
            
            # 确保日期是 datetime.date 对象
            if isinstance(input_date, datetime.date):
                date_obj = input_date
            elif isinstance(input_date, datetime.datetime):
                date_obj = input_date.date()
            else:
                date_obj = datetime.date(1990, 1, 1)
            
            user_data = {
                "name": name,
                "gender": gender,
                "date": date_obj,
                "time": input_time,
                "city": city_for_controller,
                "enable_solar": input_enable_solar,
                "longitude": input_longitude,
                "era_factor": era_factor if era_factor else None,
            }
        else:
            # 量子验证页面：使用档案数据或默认值
            if selected_case and isinstance(selected_case, dict):
                try:
                    name = selected_case.get("description", "User")
                    gender = "男" if selected_case.get("gender", "男") in ["男", "M", 1] else "女"
                except Exception:
                    name, gender = "User", "男"
            else:
                # 从 controller 获取或使用默认值
                user_data_existing = controller.get_user_data() if controller else {}
                name = user_data_existing.get("name", "User")
                gender = user_data_existing.get("gender", "男")

            demo_date = datetime.date(1990, 1, 1)
            demo_hour = 12

            user_data = {
                "name": name,
                "gender": gender,
                "date": demo_date,
                "time": demo_hour,
                "city": city_for_controller,
                "enable_solar": True,
                "longitude": 116.46,
                "era_factor": era_factor if era_factor else None,
            }

        particle_weights = controller.get_current_particle_weights() if hasattr(controller, "get_current_particle_weights") else {}

        try:
            facade.process_and_set_inputs(
                user_data=user_data,
                geo_city=city_for_controller,
                era_factor=era_factor if era_factor else None,
                particle_weights=particle_weights if particle_weights else None
            )
            st.success("数据与修正因子已同步到 Controller。")
        except Exception as e:
            st.warning(f"无法刷新 Controller 输入: {e}")

    return selected_case, era_factor, city_for_controller

