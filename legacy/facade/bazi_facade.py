"""
facade/bazi_facade.py
---------------------
V13.0 BaziFacade:
- 统一封装 UI 输入/输出，降低页面与 Controller 的耦合
- 提供简洁的 API 给 View 层调用
"""

from typing import Dict, Any, Optional

from controllers.bazi_controller import BaziController
from utils.constants_manager import get_constants


class BaziFacade:
    """
    作为 UI 与 BaziController 的轻量级外观层，提供统一入口。
    """

    def __init__(self, controller: Optional[BaziController] = None):
        self._controller = controller or BaziController()
        self.consts = get_constants()

    def process_and_set_inputs(
        self,
        user_data: Dict[str, Any],
        geo_city: Optional[str] = None,
        era_factor: Optional[Dict[str, float]] = None,
        particle_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        统一处理来自 UI 的输入并刷新 Controller 状态。
        `user_data` 预期字段：name, gender, date, time, city, enable_solar, longitude
        """
        if not user_data:
            return

        self._controller.set_user_input(
            name=user_data.get("name"),
            gender=user_data.get("gender"),
            date_obj=user_data.get("date"),
            time_int=user_data.get("time"),
            city=geo_city or user_data.get("city"),
            enable_solar=user_data.get("enable_solar", True),
            longitude=user_data.get("longitude", 116.46),
            era_factor=era_factor if era_factor is not None else user_data.get("era_factor"),
            particle_weights=particle_weights if particle_weights is not None else user_data.get("particle_weights"),
        )

    def get_core_analysis(self) -> Dict[str, Any]:
        """
        返回 P1/P3 需要的核心分析摘要，封装 Controller 的底层接口。
        """
        # 确保有基础能量数据
        flux_data = self._controller.get_flux_data()
        element_energies = self._controller.get_five_element_energies(flux_data)
        wang_shuai = self._controller.get_wang_shuai_str(flux_data)

        return {
            "five_elements_names": self.consts.FIVE_ELEMENTS,
            "ten_gods_names": self.consts.TEN_GODS,
            "chart": self._controller.get_chart(),
            "details": self._controller.get_details(),
            "luck_cycles": self._controller.get_luck_cycles(),
            "element_energies": element_energies,
            "wang_shuai": wang_shuai,
            "geo_city": self._controller.get_current_city(),
            "era_factor": self._controller.get_current_era_factor(),
            "particle_weights": self._controller.get_current_particle_weights(),
            "health_report": self._controller.get_health_report(),
            "auto_recommendations": self._controller.get_auto_recommendations(),
        }

    # 可按需扩展更多统一方法（如时间线、LLM、GEO 对比等）

    def run_predictive_scenario(
        self,
        start_year: int,
        duration: int,
        scenario_tag: str,
        target_adjustment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        运行情景模拟，封装时间线 + LLM 分析。
        """
        timeline_df = self._controller.run_geo_predictive_timeline(
            start_year=start_year,
            duration=duration,
            target_adjustment=target_adjustment
        )

        scenario_payload = {
            "base_chart_data": self._controller.get_chart(),
            "simulated_timeline": timeline_df.to_dict(orient="records") if hasattr(timeline_df, "to_dict") else {},
            "target_adjustment": target_adjustment or {},
            "scenario_tag": scenario_tag,
        }
        llm_analysis = self._controller.get_llm_scenario_analysis(scenario_payload)

        return {
            "timeline_data": timeline_df,
            "llm_analysis": llm_analysis,
        }

    def find_optimal_adjustment(self, target_metric: str, target_increase_percent: float) -> Dict[str, float]:
        """
        封装最优路径查找逻辑。
        """
        return self._controller.find_optimal_adjustment_path(target_metric, target_increase_percent)

    def apply_auto_calibration(self) -> None:
        """
        封装一键应用自动校准逻辑。
        """
        recommendations = self._controller.get_auto_recommendations() or {}
        self._controller.apply_temporary_corrections(
            era_factor=recommendations.get("era_factor"),
            particle_weights=recommendations.get("particle_weights")
        )

