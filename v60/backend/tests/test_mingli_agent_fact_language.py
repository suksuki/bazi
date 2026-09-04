from abu_v60.mingli.agent_fact_language import resolution_ruling_conflicts


def test_resolution_support_ignores_negated_or_weak_competition_language() -> None:
    assert not resolution_ruling_conflicts(
        check_code="COMPETING_PATH_RESOLUTION",
        ruling="SUPPORTS",
        rationale="竞争路径存在，但印星仅藏，未形成更强竞争。",
    )
    assert not resolution_ruling_conflicts(
        check_code="COMPETING_PATH_RESOLUTION",
        ruling="SUPPORTS",
        rationale="竞争路径弱、不改变官印主轴。",
    )
    assert not resolution_ruling_conflicts(
        check_code="COMPETING_PATH_RESOLUTION",
        ruling="SUPPORTS",
        rationale="竞争路径被阻，已有清楚主次。",
    )


def test_resolution_support_still_rejects_active_competition_blocker() -> None:
    assert resolution_ruling_conflicts(
        check_code="COMPETING_PATH_RESOLUTION",
        ruling="SUPPORTS",
        rationale="竞争路径更闭合并压制官印主轴，形成明确阻断。",
    )
