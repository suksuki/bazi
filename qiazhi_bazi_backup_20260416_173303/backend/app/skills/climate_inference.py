"""ClimateInferenceSkill: derive seasonal hard factors for five elements."""
from __future__ import annotations

from typing import Any, Dict

from app.schemas.bazi_metadata import BaziMetadata
from app.skills.physics_rules import ELEMENT_GENERATES, MONTH_BRANCH_TO_SEASON


class ClimateInferenceSkill:
    skill_id = "climate_inference_skill"
    skill_version = "0.1.0"
    rule_version = "climate_rules.v1"

    @staticmethod
    def infer(
        *,
        metadata: BaziMetadata,
        climate_intensity: float = 1.0,
    ) -> Dict[str, Any]:
        month_branch = metadata.pillars.month.branch
        season = MONTH_BRANCH_TO_SEASON.get(month_branch, "spring")
        dominant_by_season = {
            "spring": "wood",
            "summer": "fire",
            "autumn": "metal",
            "winter": "water",
        }
        dominant = dominant_by_season.get(season, "wood")
        supporting = ELEMENT_GENERATES.get(dominant, "earth")
        opposing = {
            "wood": "metal",
            "fire": "water",
            "earth": "water",
            "metal": "wood",
            "water": "fire",
        }.get(dominant, "metal")

        intensity = max(0.0, min(1.0, float(climate_intensity)))
        gain_factor = 1.05 + 0.10 * intensity
        loss_factor = 0.95 - 0.10 * intensity
        neutral_factor = 1.0

        factors = {el: neutral_factor for el in ("wood", "fire", "earth", "metal", "water")}
        factors[dominant] = round(gain_factor, 4)
        factors[supporting] = round(1.02 + 0.08 * intensity, 4)
        factors[opposing] = round(loss_factor, 4)

        return {
            "month_branch": month_branch,
            "season": season,
            "dominant_element": dominant,
            "supporting_element": supporting,
            "opposing_element": opposing,
            "intensity": round(intensity, 4),
            "factors": factors,
        }
