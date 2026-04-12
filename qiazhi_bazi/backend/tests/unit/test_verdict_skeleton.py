from app.semantic_translator.verdict_skeleton import build_verdict_skeleton


def test_build_verdict_skeleton_empty_vf():
    md = build_verdict_skeleton([])
    assert "### 核心气象 (物理预判)" in md
    assert "### 风险预警 (意志对垒)" in md
    assert "结构：" in md
    assert "暂无 VF 结构标签" in md


def test_build_verdict_skeleton_with_risk_lines():
    md = build_verdict_skeleton(
        ["VF:日主无根"],
        risk_lines=["意志与盲派 risk 并置"],
        temporal_warnings=["换运提示"],
    )
    assert "### 风险预警 (意志对垒)" in md
    assert "意志与盲派" in md
    assert "换运" in md


def test_build_verdict_skeleton_buckets():
    vf = [
        "芯片·冲突点·[clash] 寅申冲",
        "四柱快照=甲子 / 丙寅",
        "VF:日主无根·虚浮",
        "VF:止损优先·个人能量补丁已采纳",
    ]
    md = build_verdict_skeleton(vf)
    assert "### 核心气象 (物理预判)" in md
    assert "### 风险预警 (意志对垒)" in md
    assert "结构：" in md
    assert "状态：" in md
    assert "意志：" in md
    assert "寅申冲" in md or "芯片" in md
