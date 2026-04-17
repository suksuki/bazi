from __future__ import annotations

from app.plugins.blind_school.op_work_logic import apply_work_intensity_and_meta_audit
from app.skills.blind_work_evaluator import evaluate_blind_work


def test_work_audit_v1_and_work_score_from_status():
    metadata = {"conflict_matrix": {"points": [{"detail": "辰戌冲"}]}}
    physics_tensor: dict = {
        "deity_energy_axes": {
            "比肩": {"absolute_energy": 5.0},
            "劫财": {"absolute_energy": 1.0},
            "正印": {"absolute_energy": 1.0},
            "偏印": {"absolute_energy": 1.0},
            "食神": {"absolute_energy": 2.0},
            "伤官": {"absolute_energy": 1.0},
            "正财": {"absolute_energy": 3.0},
            "偏财": {"absolute_energy": 1.0},
            "正官": {"absolute_energy": 2.0},
            "七杀": {"absolute_energy": 1.0},
        },
        "meta": {
            "l1_status_v1": {
                "per_deity": {
                    "正财": {"stages": ["戊:月墓/日死"], "work_efficiency": 0.72},
                    "比肩": {"stages": ["甲:月长生/日帝旺"], "work_efficiency": 1.2},
                }
            },
            "runtime_physics_config": {},
        },
    }
    wv = evaluate_blind_work(metadata, physics_tensor)
    apply_work_intensity_and_meta_audit(work_vector=wv, physics_tensor=physics_tensor)
    meta = physics_tensor["meta"]
    assert "work_audit_v1" in meta
    vec = wv["work_vectors"][0]
    assert "work_score" in vec
    assert vec["controlled_deity"] in {"正财", "比肩", "劫财", "正印", "偏印", "食神", "伤官", "偏财", "正官", "七杀"}
    assert float(vec.get("work_intensity") or 0) > 0
