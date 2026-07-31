from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from abu_v60.mingli.stage_contracts import MingliStageMode, MingliStageProjection
from abu_v60.provenance import content_hash, stable_ref


@dataclass(frozen=True, slots=True)
class NarrationScriptSegment:
    cue_id: str
    text: str
    semantic_action: str


@dataclass(frozen=True, slots=True)
class NarrationScript:
    script_ref: str
    script_hash: str
    segments: tuple[NarrationScriptSegment, ...]


@dataclass(frozen=True, slots=True)
class NarrationVoiceProfile:
    voice_profile_ref: str
    voice_profile_hash: str
    actor_ref: str
    speaker: str
    model: str
    status: str


VOICE_PROFILES: Final = {
    "ABU_NARRATOR_V1": {
        "voice_profile_ref": "v60.voice-profile.abu-dylan-owner-selected.001",
        "actor_ref": "ABU_NARRATOR_V1",
        "speaker": "Dylan",
        "model": "Qwen3-TTS",
        "status": "OWNER_SELECTED",
        "design_intent": "cartoon boy; youthful Beijing tone, warm and restrained",
    },
    "DUODUO_NARRATOR_V1": {
        "voice_profile_ref": "v60.voice-profile.duoduo-vivian-audition.001",
        "actor_ref": "DUODUO_NARRATOR_V1",
        "speaker": "Vivian",
        "model": "Qwen3-TTS",
        "status": "AUDITION_CANDIDATE",
        "design_intent": "cartoon girl; bright, clear, restrained",
    },
}


def voice_profile(
    actor_ref: str,
    *,
    speaker: str | None = None,
    model: str | None = None,
) -> NarrationVoiceProfile:
    base = VOICE_PROFILES.get(actor_ref)
    if base is None:
        raise ValueError("mingli_narration_actor_not_admitted")
    payload = {
        **base,
        "speaker": speaker or base["speaker"],
        "model": model or base["model"],
    }
    if payload["speaker"] != base["speaker"] or payload["model"] != base["model"]:
        payload["voice_profile_ref"] = stable_ref(
            "v60-voice-profile-audition",
            {
                "actor_ref": actor_ref,
                "speaker": payload["speaker"],
                "model": payload["model"],
            },
        )
        payload["status"] = "AUDITION_CANDIDATE"
    profile_hash = content_hash(payload)
    return NarrationVoiceProfile(
        voice_profile_ref=str(payload["voice_profile_ref"]),
        voice_profile_hash=profile_hash,
        actor_ref=str(payload["actor_ref"]),
        speaker=str(payload["speaker"]),
        model=str(payload["model"]),
        status=str(payload["status"]),
    )


def script_for_projection(projection: MingliStageProjection) -> NarrationScript:
    pillar_line = "、".join(f"{column.label}{column.pillar}" for column in projection.columns[:4])
    relation_counts = {
        "six_clash_membership": sum(
            relation.relation_type == "six_clash_membership"
            for relation in projection.relations
        ),
        "six_harmony_membership": sum(
            relation.relation_type == "six_harmony_membership"
            for relation in projection.relations
        ),
    }
    if sum(relation_counts.values()):
        relation_line = (
            f"舞台识别到六冲成员关系{relation_counts['six_clash_membership']}组，"
            f"六合成员关系{relation_counts['six_harmony_membership']}组。"
            "这里确认的只是成员关系。"
        )
    else:
        relation_line = "当前舞台没有命中已准入的六冲或六合成员关系。"
    if projection.stage_mode == MingliStageMode.NATAL_DAYUN_YEAR_6:
        dayun = projection.columns[4]
        annual = projection.columns[5]
        time_line = (
            f"时间层中，当前大运是{dayun.pillar}，"
            f"你选择的{projection.selected_year}年流年是{annual.pillar}。"
            f"这步大运按起运日期从{projection.current_dayun_start_date.isoformat()}"
            f"到{projection.current_dayun_end_date.isoformat()}划界；"
            "交运当天只有日期而没有观察时刻时，系统不声明当前大运。"
        )
    else:
        time_line = (
            "现在先看本命四柱。进入时间层时，大运和所选流年会一起展开，"
            "系统不会生成孤立流年的五柱状态。"
        )
    segments = (
        NarrationScriptSegment(
            cue_id="STRUCTURE",
            text=f"这是{projection.display_name}的命理舞台。{pillar_line}。",
            semantic_action="PILLARS_PRESENT",
        ),
        NarrationScriptSegment(
            cue_id="RELATION_BOUNDARY",
            text=relation_line,
            semantic_action="RELATIONS_PRESENT",
        ),
        NarrationScriptSegment(
            cue_id="EVIDENCE_GAP",
            text=(
                "这些坐标和成员关系，不自动等于关系已经发生作用。"
                "来源是否可用、旺衰、有效做功、概率和吉凶，当前都没有被证明。"
            ),
            semantic_action="BOUNDARY_HOLD",
        ),
        NarrationScriptSegment(
            cue_id="TIME_LAYER",
            text=time_line,
            semantic_action="TIME_COORDINATES_PRESENT",
        ),
    )
    identity = {
        "cue_set_ref": "v60.mingli-stage-guide-cues.001",
        "stage_projection_ref": projection.projection_ref,
        "stage_projection_hash": projection.projection_hash,
        "segments": [
            {
                "cue_id": segment.cue_id,
                "text": segment.text,
                "semantic_action": segment.semantic_action,
            }
            for segment in segments
        ],
    }
    return NarrationScript(
        script_ref=stable_ref("v60-mingli-narration-script", identity),
        script_hash=content_hash(identity),
        segments=segments,
    )
