from __future__ import annotations

import base64
import json
import wave
from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace

import pytest
from abu_v60.api.public_experience import public_home_projection
from abu_v60.db import engine
from abu_v60.media.focused_speech import (
    FocusedPassSpeechConflict,
    FocusedPassSpeechNotFound,
    FocusedPassSpeechService,
    _speech_segments,
)
from abu_v60.media.tts import validate_wav
from abu_v60.settings import settings


def _wav() -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(b"\x00\x00" * 240)
    return output.getvalue()


class _StageStore:
    def __init__(self, projection: object) -> None:
        self.projection = projection
        self.calls: list[dict[str, object]] = []

    def project(self, **arguments: object) -> object:
        self.calls.append(arguments)
        return self.projection


class _PassStore:
    def __init__(self, record: object | None) -> None:
        self.record = record
        self.calls: list[tuple[str, str]] = []

    def owned_record(
        self,
        *,
        requester_account_ref: str,
        record_ref: str,
    ) -> object | None:
        self.calls.append((requester_account_ref, record_ref))
        return self.record


class _Provider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, *, text: str, speaker: str):
        self.calls.append((text, speaker))
        return validate_wav(_wav(), max_audio_bytes=1024 * 1024)


def _stage() -> SimpleNamespace:
    return SimpleNamespace(
        projection_ref="stage:public",
        projection_hash="a" * 64,
        case_ref="case:public",
        reading_ref="reading:public",
        reading_hash="b" * 64,
    )


def _record() -> SimpleNamespace:
    return SimpleNamespace(
        record_ref="record:public",
        record_hash="c" * 64,
        case_ref="case:public",
        reading_ref="reading:public",
        reading_hash="b" * 64,
        pass_result=SimpleNamespace(
            normalized_text="## 总纲\n- 先看整盘。\n\n真正重要的是主线，不由单一符号定论。"
        ),
    )


def test_public_home_projection_does_not_leak_internal_world_or_lab_state() -> None:
    case = {
        "case_ref": "case:1",
        "profile_ref": "profile:1",
        "display_name": "测试",
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "1990-01-01",
        "birth_time": "12:00:00",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
        "lunar_leap_month": False,
        "status": "ACTIVE",
        "pillars": {"year": "庚午", "month": "丁丑", "day": "甲子", "hour": "庚午"},
        "active": True,
        "stage_subject_id": "subject:1",
        "subject_kind": "HUMAN_OWNER",
        "identity_badge": "私密真实档案",
        "birth_location_status": "RECORDED",
        "internal_trace": {"secret": True},
    }
    payload = public_home_projection(
        {
            "profile": {"display_name": "测试"},
            "case": {"case_ref": "case:1"},
            "case_options": [
                case,
                {
                    **case,
                    "case_ref": "case:reference",
                    "display_name": "内部参考档案",
                    "subject_kind": "HUMAN_REFERENCE",
                    "active": False,
                },
                {
                    **case,
                    "case_ref": "case:synthetic",
                    "display_name": "内部合成档案",
                    "subject_kind": "SYNTHETIC_EXPERIMENT",
                    "active": False,
                },
            ],
            "chart": {"pillars": case["pillars"]},
            "life_case": {
                "life_case_revision_ref": "life-case:1",
                "revision": 1,
                "status": "ACTIVE",
                "revision_hash": "a" * 64,
                "internal_trace": {"secret": True},
            },
            "tree": {
                "tree_ref": "tree:1",
                "projection_version": 1,
                "scene_ref": "scene:1",
                "phenotype": {"semantic_status": "VISUAL_METAPHOR_ONLY"},
                "read_only": True,
                "source_kind": "CANONICAL_SCENE_PROJECTION",
                "internal_trace": {"secret": True},
            },
            "lab": {"private": True},
            "units": ["unit-mingli", "unit-lab"],
            "lineage": {"private": True},
        }
    )

    assert set(payload) == {
        "scope",
        "profile",
        "case",
        "case_options",
        "chart",
        "life_case",
        "tree",
        "privacy",
    }
    assert payload["scope"] == "MINGLI_HOME"
    assert payload["privacy"] == {"private_to_account": True}
    assert len(payload["case_options"]) == 2
    assert [item["case_ref"] for item in payload["case_options"]] == [
        "case:1",
        "case:reference",
    ]
    assert all("internal_trace" not in item for item in payload["case_options"])
    assert "internal_trace" not in payload["life_case"]
    assert "internal_trace" not in payload["tree"]
    assert "lab" not in payload
    assert "units" not in payload
    assert "lineage" not in payload


def test_focused_speech_reuses_owned_persisted_pass_and_audio_cache() -> None:
    stage = _stage()
    stages = _StageStore(stage)
    record = _record()
    passes = _PassStore(record)
    provider = _Provider()
    service = FocusedPassSpeechService(
        engine,
        runtime_settings=replace(
            settings,
            tts_enabled=True,
            tts_max_audio_bytes=1024 * 1024,
        ),
        stages=stages,  # type: ignore[arg-type]
        passes=passes,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
    )

    arguments = {
        "account_ref": "account:owner",
        "subject_id": "subject:1",
        "expected_stage_projection_ref": stage.projection_ref,
        "expected_stage_projection_hash": stage.projection_hash,
        "record_ref": record.record_ref,
        "expected_record_hash": record.record_hash,
    }
    first = service.prepare(**arguments)
    second = service.prepare(**arguments)

    assert first.audio.audio_bytes == second.audio.audio_bytes
    assert len(provider.calls) == len(first.cues) == 2
    assert passes.calls == [
        ("account:owner", "record:public"),
        ("account:owner", "record:public"),
    ]
    assert all(call[1] == settings.tts_abu_voice for call in provider.calls)
    assert all("##" not in call[0] and "- " not in call[0] for call in provider.calls)
    assert [(cue.start_ms, cue.end_ms) for cue in first.cues] == [(0, 10), (10, 20)]
    timeline_header = first.timeline_header_value()
    padded_header = timeline_header + "=" * (-len(timeline_header) % 4)
    timeline = json.loads(base64.urlsafe_b64decode(padded_header))
    assert timeline["duration_ms"] == 20
    assert [cue["text"] for cue in timeline["cues"]] == [call[0] for call in provider.calls]
    assert stages.calls[0]["stage_mode"] == "NATAL_4"
    assert stages.calls[0]["selected_year"] is None


def test_focused_speech_can_lock_to_the_current_six_pillar_projection() -> None:
    stage = _stage()
    stages = _StageStore(stage)
    service = FocusedPassSpeechService(
        engine,
        stages=stages,  # type: ignore[arg-type]
        passes=_PassStore(_record()),  # type: ignore[arg-type]
        provider=_Provider(),  # type: ignore[arg-type]
    )

    service.prepare(
        account_ref="account:owner",
        subject_id="subject:1",
        stage_mode="NATAL_DAYUN_YEAR_6",  # type: ignore[arg-type]
        selected_year=2026,
        expected_stage_projection_ref=stage.projection_ref,
        expected_stage_projection_hash=stage.projection_hash,
        record_ref="record:public",
        expected_record_hash="c" * 64,
    )

    assert stages.calls[0]["stage_mode"] == "NATAL_DAYUN_YEAR_6"
    assert stages.calls[0]["selected_year"] == 2026


def test_focused_speech_fails_closed_on_stale_or_unowned_lineage() -> None:
    stage = _stage()
    service = FocusedPassSpeechService(
        engine,
        stages=_StageStore(stage),  # type: ignore[arg-type]
        passes=_PassStore(None),  # type: ignore[arg-type]
        provider=_Provider(),  # type: ignore[arg-type]
    )

    common = {
        "account_ref": "account:owner",
        "subject_id": "subject:1",
        "expected_stage_projection_ref": stage.projection_ref,
        "expected_stage_projection_hash": stage.projection_hash,
        "record_ref": "record:other",
        "expected_record_hash": "c" * 64,
    }
    with pytest.raises(FocusedPassSpeechNotFound):
        service.prepare(**common)
    with pytest.raises(FocusedPassSpeechConflict, match="stage_stale"):
        service.prepare(
            **{
                **common,
                "expected_stage_projection_hash": "d" * 64,
            }
        )


def test_speech_normalizer_splits_long_text_into_provider_safe_segments() -> None:
    segments = _speech_segments("# 标题\n- " + ("甲" * 430) + "。结尾。")

    assert segments
    assert all(0 < len(item) <= 64 for item in segments)
    assert all("#" not in item and "- " not in item for item in segments)
    assert "".join(segments) == "标题 " + ("甲" * 430) + "。结尾。"


def test_speech_normalizer_keeps_a_short_quoted_tail_with_its_lead_in() -> None:
    segments = _speech_segments(
        "日主乙木生于巳月，火旺泄气极重，虽月干、时干两透比肩帮身，"
        "但地支无强根支撑，仅靠虚浮之木抗衡烈火与燥土，"
        "呈现“身弱用印比，实则力不从心”的承载状态。"
    )

    assert len(segments) == 2
    assert segments[1].startswith("呈现“")
    assert segments[1].count("“") == segments[1].count("”") == 1
