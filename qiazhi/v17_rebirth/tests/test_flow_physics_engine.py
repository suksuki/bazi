from __future__ import annotations
from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine

def test_flow_physics_engine_kcl() -> None:
    # 模拟壬水日主，水火对峙局，同时给其他节点少量背景电位
    engine = FlowPhysicsEngine("壬")
    
    ten_gods = {
        "比肩": 100.0, # 水
        "正财": 20.0,  # 火
        "食神": 10.0,  # 木
        "正官": 10.0,  # 土
        "正印": 10.0   # 金
    }
    ten_god_to_el = {
        "比肩": "水", "正财": "火", "食神": "木", "正官": "土", "正印": "金"
    }
    clash_stress = {"events": []} # 无应力
    
    result = engine.compute_flow(
        ten_gods_absolute=ten_gods,
        clash_stress_map=clash_stress,
        ten_god_to_el=ten_god_to_el
    )
    
    # 验证能量流转的趋势：水(100) 应该向 木(10) 生，向 火(20) 克
    deltas = result["ten_god_deltas"]
    assert deltas["比肩"] < 0 # 水流出能量
    assert abs(sum(deltas.values())) < 0.01 # 能量守恒

def test_flow_stress_modulation() -> None:
    # 模拟子午冲带来的电阻下降，导致被迫导通（水火泄压）
    engine = FlowPhysicsEngine("壬")
    # 背景电位统一，只观察水火
    ten_gods = {"比肩": 100.0, "正财": 20.0, "食神": 50.0, "正官": 50.0, "正印": 50.0}
    ten_god_to_el = {"比肩": "水", "正财": "火", "食神": "木", "正官": "土", "正印": "金"}
    
    # 情况 A：无应力 (F=0) -> R = R_base * (1 + 1/0.1) = 11 * R_base
    res_low = engine.compute_flow(
        ten_gods_absolute=ten_gods,
        clash_stress_map={"events": []},
        ten_god_to_el=ten_god_to_el
    )
    
    # 情况 B：高应力 (F=100) -> R = R_base * (1 + 1/100) = 1.01 * R_base (路径极度导通)
    res_high = engine.compute_flow(
        ten_gods_absolute=ten_gods,
        clash_stress_map={"events": [{"god_i": "比肩", "god_j": "正财", "damped_stress": 100.0}]},
        ten_god_to_el=ten_god_to_el
    )
    
    # 高应力下，水对火的克制电流更大，火的净能量变化应受到显著影响（在这个模型中，火会吸收更多来自水的“冲击”）
    # 注意：KCL 中 I = (Vi - Vj)/R。由于 V_water(100) > V_fire(20)，I 是从水流向火。
    # 即使火向土流转，高应力导致水流入火的电流 I 变大，因此火节点得到的流入量增加。
    assert res_high["ten_god_deltas"]["正财"] > res_low["ten_god_deltas"]["正财"]
