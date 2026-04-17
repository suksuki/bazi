from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FourPillars, StemBranchPair
from app.skills.climate_inference import ClimateInferenceSkill


def _metadata(month_branch: str) -> BaziMetadata:
    return BaziMetadata(
        pillars=FourPillars(
            year=StemBranchPair(stem="庚", branch="午", energy_value=100),
            month=StemBranchPair(stem="壬", branch=month_branch, energy_value=100),
            day=StemBranchPair(stem="甲", branch="子", energy_value=100),
            hour=StemBranchPair(stem="乙", branch="酉", energy_value=100),
        ),
        conflict_matrix=ConflictMatrix(points=[]),
    )


def test_climate_inference_winter_penalizes_fire_and_boosts_water():
    out = ClimateInferenceSkill.infer(metadata=_metadata("子"), climate_intensity=1.0)
    assert out["season"] == "winter"
    assert out["factors"]["water"] >= 1.05
    assert out["factors"]["fire"] <= 0.95
