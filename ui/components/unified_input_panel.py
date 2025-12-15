import streamlit as st
import json
import os
import datetime
from typing import Dict, List, Optional, Tuple, Any


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


def render_and_collect_input(controller,
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
    with st.sidebar:
        st.header("⚙️ 核心数据与修正")

        # --- 档案选择 ---
        if cases is None:
            cases = _load_cases()

        selected_case = None
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
        raw_cities = _load_geo_cities()
        if "Beijing" in raw_cities:
            raw_cities.remove("Beijing")
        cities = ["None", "Beijing"] + raw_cities

        archive_city = selected_case.get("city") if isinstance(selected_case, dict) else None
        default_city = archive_city if archive_city in cities else "None"
        default_idx = cities.index(default_city) if default_city in cities else 0
        selected_city = st.selectbox("🌍 GEO 修正城市", cities, index=default_idx, key="unified_geo_city")
        city_for_controller = "Unknown" if selected_city == "None" else selected_city

        # --- ERA 因子 ---
        era_factor: Dict[str, float] = {}
        if is_quantum_lab:
            st.subheader("🌐 ERA 时代修正 (可调)")
            cols = st.columns(5)
            era_factor["Wood"] = cols[0].slider("木 (ERA %)", -10, 10, 0, key="era_wood") / 100
            era_factor["Fire"] = cols[1].slider("火 (ERA %)", -10, 10, 0, key="era_fire") / 100
            era_factor["Earth"] = cols[2].slider("土 (ERA %)", -10, 10, 0, key="era_earth") / 100
            era_factor["Metal"] = cols[3].slider("金 (ERA %)", -10, 10, 0, key="era_metal") / 100
            era_factor["Water"] = cols[4].slider("水 (ERA %)", -10, 10, 0, key="era_water") / 100
        else:
            st.subheader("🌐 ERA 时代修正 (当前生效)")
            current_era = controller.get_current_era_factor()
            if current_era and any(current_era.values()):
                cols = st.columns(3)
                elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
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

        # --- 构造用户输入并刷新 Controller ---
        # 因档案未必带有出生日期，这里使用默认日期/时辰，主要用于实验/展示
        try:
            name = selected_case.get("description", "User")
            gender = "男" if selected_case.get("gender", "男") in ["男", "M", 1] else "女"
        except Exception:
            name, gender = "User", "男"

        demo_date = datetime.date(1990, 1, 1)
        demo_hour = 12

        try:
            controller.set_user_input(
                name=name,
                gender=gender,
                date_obj=demo_date,
                time_int=demo_hour,
                city=city_for_controller,
                enable_solar=True,
                longitude=116.46,
                era_factor=era_factor if era_factor else None,
            )
            st.success("数据与修正因子已同步到 Controller。")
        except Exception as e:
            st.warning(f"无法刷新 Controller 输入: {e}")

    return selected_case, era_factor, city_for_controller

