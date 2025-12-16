import datetime
import unittest
from unittest.mock import MagicMock

from controllers.bazi_controller import BaziController
from facade.bazi_facade import BaziFacade


class TestControllerFacade(unittest.TestCase):
    def setUp(self):
        # 初始化真实的 Controller 与 Facade（Controller 内部会创建 FluxEngine 等）
        self.controller = BaziController()
        self.facade = BaziFacade(controller=self.controller)

        # 基础输入数据
        self.base_kwargs = dict(
            name="TestUser",
            gender="男",
            date_obj=datetime.date(1990, 1, 1),
            time_int=12,
            city="Beijing",
            enable_solar=True,
            longitude=116.46,
        )

    def test_set_input_triggers_calibration(self):
        """验证设置新输入时 CalibrationService 被调用。"""
        # 注入 mock 校准服务
        self.controller._calibration_service.run_health_check = MagicMock(return_value={"is_healthy": True, "warnings": []})
        self.controller._calibration_service.get_auto_recommendations = MagicMock(return_value={"era_factor": {}, "particle_weights": {}})

        self.controller.set_user_input(**self.base_kwargs)

        self.controller._calibration_service.run_health_check.assert_called_once()
        self.controller._calibration_service.get_auto_recommendations.assert_called_once()

    def test_particle_weight_change_invalidates_cache(self):
        """粒子权重变更应触发缓存失效逻辑。"""
        # 使用 mock 来捕捉缓存失效调用
        self.controller._invalidate_cache = MagicMock()

        # 初次设置输入
        self.controller.set_user_input(**self.base_kwargs, particle_weights=None)
        self.assertTrue(self.controller._invalidate_cache.called)  # 首次也会被调用
        self.controller._invalidate_cache.reset_mock()

        # 第二次仅修改粒子权重
        new_weights = {"ZhengYin": 1.2}
        self.controller.set_user_input(**self.base_kwargs, particle_weights=new_weights)
        self.controller._invalidate_cache.assert_called_once()

    def test_facade_core_analysis_aggregation(self):
        """Facade 应聚合并透传 Controller 的核心指标。"""
        # Mock 底层接口，避免真实计算
        self.controller.get_five_element_energies = MagicMock(return_value={"Wood": 1.0})
        self.controller.get_wang_shuai_str = MagicMock(return_value="身强")
        self.controller.get_chart = MagicMock(return_value={"day": {"stem": "甲"}})
        self.controller.get_details = MagicMock(return_value={"demo": True})
        self.controller.get_luck_cycles = MagicMock(return_value=[])

        analysis = self.facade.get_core_analysis()

        self.controller.get_five_element_energies.assert_called_once()
        self.controller.get_wang_shuai_str.assert_called_once()
        self.assertIn("five_elements_names", analysis)
        self.assertIn("ten_gods_names", analysis)
        self.assertEqual(analysis["element_energies"]["Wood"], 1.0)
        self.assertEqual(analysis["wang_shuai"], "身强")


if __name__ == "__main__":
    unittest.main()

