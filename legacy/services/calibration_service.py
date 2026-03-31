"""
services/calibration_service.py
-------------------------------
V12.0 Calibration Service:
- Run data health checks
- Produce automatic recommendations (ERA/particle weights) for calibration
"""

from typing import Dict, Any

from utils.constants_manager import get_constants


class CalibrationService:
    def __init__(self, flux_engine):
        self.flux_engine = flux_engine
        self.consts = get_constants()

    def run_health_check(self, bazi_data: Dict) -> Dict[str, Any]:
        """
        Run archive data health check to detect imbalances or anomalies.
        Returns a dict with:
            - is_healthy (bool)
            - warnings (list of str)
        """
        warnings = []
        is_healthy = True

        five_elements = {}
        try:
            if hasattr(self.flux_engine, "get_five_element_energies"):
                five_elements = self.flux_engine.get_five_element_energies(bazi_data) or {}
        except Exception:
            five_elements = {}

        # Basic imbalance check: if any element is zero or ratio > 5x
        if five_elements:
            vals = [five_elements.get(elem, 0.0) for elem in self.consts.FIVE_ELEMENTS]
            mn = min(vals) if vals else 0.0
            mx = max(vals) if vals else 0.0

            # Missing element warning
            for elem in self.consts.FIVE_ELEMENTS:
                if five_elements.get(elem, 0.0) <= 0.0001:
                    warnings.append(f"🚨 五行能量 [{elem}] 缺失或接近零，建议校准。")
                    is_healthy = False

            # Imbalance ratio check
            if vals and mn >= 0.0:
                if mn <= 0.0001 or (mx > 0 and mx / max(mn, 1e-6) > 5):
                    warnings.append("🚨 档案五行能量存在严重失衡，建议校准。")
                    is_healthy = False

        # Placeholder for more checks
        # TODO: add ten-god ratio checks, missing data checks, etc.

        return {"is_healthy": is_healthy, "warnings": warnings}

    def get_auto_recommendations(self, health_report: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Based on health report, compute ERA and particle weight recommendations.
        Returns dict with keys:
            - era_factor: dict
            - particle_weights: dict
        """
        recommendations = {
            "era_factor": {elem: 0.0 for elem in self.consts.FIVE_ELEMENTS},
            "particle_weights": self.consts.DEFAULT_PARTICLE_WEIGHTS.copy()
        }

        if not health_report.get("is_healthy", True):
            # Simple heuristic: if imbalance detected, boost resource stars as an example
            if len(self.consts.TEN_GODS) >= 2:
                recommendations["particle_weights"][self.consts.TEN_GODS[0]] = 1.10  # ZhengYin
                recommendations["particle_weights"][self.consts.TEN_GODS[1]] = 1.10  # PianYin

        return recommendations

