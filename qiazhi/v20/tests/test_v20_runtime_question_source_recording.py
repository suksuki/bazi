from __future__ import annotations

from v20.api import runtime


def test_v20_runtime_records_question_source_report_without_breaking_measurement(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_record_question_source_ranking_report(**payload: object) -> dict[str, object]:
        calls.append(dict(payload))
        return {"version": "test.recorded", "runtime_mutation": True}

    monkeypatch.setattr(runtime, "record_question_source_ranking_report", fake_record_question_source_ranking_report)

    result = runtime.run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="runtime.question_source.recording",
        source_role="user",
        record_question_source_report=True,
    )

    assert result["version"] == "v20.runtime_result.v1"
    assert result["input_id"] == "runtime.question_source.recording"
    assert calls
    assert calls[0]["input_id"] == "runtime.question_source.recording"
    assert calls[0]["source_role"] == "user"
    assert calls[0]["question_source_ranking_report"]["version"] == "v20.question_source_ranking_report.v1"
