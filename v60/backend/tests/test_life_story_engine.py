from abu_v60.story.service import LifeStoryEngine


def test_story_plan_contains_only_committed_sources_and_question() -> None:
    plan = LifeStoryEngine().plan_committed_scene(
        world_ref="world:1",
        question_ref="question:1",
        scene_ref="scene:1",
        beat_text="水渠边留下了一道新的湿痕。",
        content_key="story.channel.question-open",
        phase="QUESTION_OPEN",
        disclosure="BASELINE_ONLY",
        evidence_refs=("evidence:1", "evidence:2"),
        world_event_ref="world-event:1",
    )
    assert plan.source_event_refs == ("evidence:1", "evidence:2")
    assert tuple(beat.source_ref for beat in plan.beats) == (
        "evidence:1",
        "evidence:2",
        "question:1",
    )
    assert plan.beats[-1].dialogue_intent == "水渠边留下了一道新的湿痕。"


def test_revealed_story_beat_is_bound_to_committed_decision() -> None:
    plan = LifeStoryEngine().plan_committed_scene(
        world_ref="world:1",
        question_ref="question:1",
        scene_ref="scene:1",
        beat_text="后来发生的事实已经展开。",
        content_key="story.channel.revealed",
        phase="REVEALED",
        disclosure="OUTCOME_REVEALED",
        evidence_refs=("evidence:baseline",),
        world_event_ref="world-event:1",
        decision_refs=("decision:1",),
    )

    assert plan.story_version == "v60.life-story-engine.011"
    assert plan.beats[-1].kind.value == "REVEAL"
    assert plan.beats[-1].source_ref == "decision:1"
