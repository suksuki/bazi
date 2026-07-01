from __future__ import annotations

from v40.contracts.base import EngineKey
from v40.contracts.context import EngineCapability, MingliTermDictionary, MingliTermEntry


def build_horizontal_runtime_context_status() -> dict[str, object]:
    return {
        "version": "v40.horizontal_runtime_context_status.v1",
        "phase": "V40-RC2: Horizontal Runtime Context",
        "statement": "V40 is a multi-locale, multi-role, multi-client, multi-engine trainable mingli runtime.",
        "contexts": [
            {
                "key": "locale",
                "contract": "LocaleContext",
                "status": "contract_ready",
                "principle": "not frontend translation; drives ProductProjection and LLMExpression",
                "supported": ["zh-CN", "en-US", "ko-KR"],
            },
            {
                "key": "role",
                "contract": "RoleContext",
                "status": "contract_ready",
                "principle": "not UI button hiding; drives RoleProjection permissions and training weight",
                "supported": ["guest", "user", "practitioner", "admin"],
            },
            {
                "key": "client",
                "contract": "ClientContext",
                "status": "contract_ready",
                "principle": "not CSS-only responsiveness; changes density/layout, never verdict",
                "supported": ["desktop", "tablet", "mobile"],
            },
            {
                "key": "engine",
                "contract": "EngineContext + EngineCapability",
                "status": "contract_ready",
                "principle": "not adapter pile; declares capability and schedules through EnginePlan",
                "supported": ["bazi", "ziwei", "reality_probe", "conversation"],
            },
        ],
        "engine_capabilities": [capability.model_dump(mode="json") for capability in _engine_capabilities()],
        "term_dictionary": _term_dictionary().model_dump(mode="json"),
        "training_dimensions": ["locale", "role", "client", "engine_source"],
        "evaluation_dimensions": [
            "locale overclaim rate",
            "terminology consistency",
            "role leakage rate",
            "mobile readability",
            "mobile probe completion",
            "desktop practitioner calibration success",
            "engine-aware attribution coverage",
        ],
        "hard_gates": [
            "Locale is handled by LocaleContext + ProductProjection + LLMExpression, not frontend-only translation",
            "Role is enforced by RoleContext + RoleProjection, not UI-only hiding",
            "ClientContext changes information density and layout only, never mingli verdict",
            "EngineCapability.can_directly_generate_verdict must remain false",
            "Ziwei remains Domain Lens and sidecar in V40-RC2",
            "Admin remains independent control plane on its own service and port",
        ],
        "boundary": "horizontal_runtime_contexts_are_system_dimensions_not_ui_afterthoughts",
    }


def _engine_capabilities() -> list[EngineCapability]:
    return [
        EngineCapability(
            engine=EngineKey.BAZI,
            can_emit_facts=True,
            can_emit_signals=True,
            can_emit_probe_candidates=True,
            supported_domains=[],
            required_inputs=["bazi_chart_facts"],
            default_weight=1.0,
            max_weight=1.0,
        ),
        EngineCapability(
            engine=EngineKey.ZIWEI,
            can_emit_facts=True,
            can_emit_signals=True,
            can_emit_probe_candidates=True,
            supported_domains=[],
            required_inputs=["complete_birth_input_or_ziwei_chart_facts"],
            default_weight=0.0,
            max_weight=0.15,
        ),
        EngineCapability(
            engine=EngineKey.REALITY_PROBE,
            can_emit_signals=True,
            can_emit_probe_candidates=True,
            can_emit_training_labels=True,
            supported_domains=[],
            required_inputs=["mixed_branch_or_advice_gap"],
            default_weight=0.35,
            max_weight=0.9,
        ),
        EngineCapability(
            engine=EngineKey.CONVERSATION,
            can_emit_probe_candidates=True,
            can_emit_training_labels=True,
            supported_domains=[],
            required_inputs=["user_initiated_question_after_report"],
            default_weight=0.0,
            max_weight=0.0,
        ),
    ]


def _term_dictionary() -> MingliTermDictionary:
    return MingliTermDictionary(
        entries=[
            MingliTermEntry(canonical_key="shi_shang", zh_cn="食伤", en_us="Output Star / Talent Output", ko_kr="식상"),
            MingliTermEntry(canonical_key="bi_jie", zh_cn="比劫", en_us="Peer / Competitor Star", ko_kr="비겁"),
            MingliTermEntry(canonical_key="cai_xing", zh_cn="财星", en_us="Wealth Star", ko_kr="재성"),
            MingliTermEntry(canonical_key="guan_sha", zh_cn="官杀", en_us="Authority / Pressure Star", ko_kr="관살"),
            MingliTermEntry(canonical_key="yin_xing", zh_cn="印星", en_us="Resource / Support Star", ko_kr="인성"),
        ]
    )
