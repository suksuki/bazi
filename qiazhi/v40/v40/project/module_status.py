from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleMigrationStatus:
    key: str
    label: str
    current_state: str
    reuse_policy: str
    v30_sources: tuple[str, ...]
    v40_target: str
    rc2_action: str


MODULES: tuple[ModuleMigrationStatus, ...] = (
    ModuleMigrationStatus(
        key="contracts_protocols",
        label="合约与协议层",
        current_state="v40_native_ready",
        reuse_policy="keep_v40_native",
        v30_sources=(),
        v40_target="contracts",
        rc2_action="保持稳定，只允许通过新合约扩展命理纵深。",
    ),
    ModuleMigrationStatus(
        key="runtime_repository",
        label="运行时仓储与隔离边界",
        current_state="v40_native_ready",
        reuse_policy="keep_v40_native",
        v30_sources=(),
        v40_target="storage/postgres",
        rc2_action="继续维持 qiazhi_v40 / v40_ 前缀，不和 V30 共库表。",
    ),
    ModuleMigrationStatus(
        key="api_and_user_surface",
        label="API 与用户测算面",
        current_state="v40_native_ready",
        reuse_policy="keep_v40_native",
        v30_sources=("frontend", "presentation"),
        v40_target="api/presentation",
        rc2_action="保留 report-first 流程，后续接入命理纵深输出。",
    ),
    ModuleMigrationStatus(
        key="admin_control_plane",
        label="Admin Control Plane",
        current_state="v40_native_ready",
        reuse_policy="keep_v40_native",
        v30_sources=("admin",),
        v40_target="admin",
        rc2_action="只做控制面和验收面，不回到主系统 admin 逻辑。",
    ),
    ModuleMigrationStatus(
        key="training_spine",
        label="训练闭环脊柱",
        current_state="v40_native_ready_needs_cases",
        reuse_policy="keep_v40_native",
        v30_sources=("training",),
        v40_target="training",
        rc2_action="接入真实案例、命理师校准和 before/after diff。",
    ),
    ModuleMigrationStatus(
        key="evaluation_release_gate",
        label="评测与发布闸门",
        current_state="v40_native_ready_needs_acceptance_window",
        reuse_policy="keep_v40_native",
        v30_sources=("evaluation", "validation"),
        v40_target="evaluation",
        rc2_action="建立 Real Case Bank / Acceptance Window。",
    ),
    ModuleMigrationStatus(
        key="bazi_native_runtime",
        label="八字原生运行时",
        current_state="v40_native_minimal_needs_depth",
        reuse_policy="refactor_v30_algorithm_into_v40",
        v30_sources=("core/pillars", "core/time_context", "core/luck_flow", "core/ten_gods"),
        v40_target="engines/bazi_native",
        rc2_action="升级为 Bazi Fact Engine Pro，先事实后信号，不输出 verdict。",
    ),
    ModuleMigrationStatus(
        key="bazi_fact_engine_pro",
        label="Bazi Fact Engine Pro",
        current_state="new_required",
        reuse_policy="build_v40_native_with_v30_reference_tests",
        v30_sources=("core", "docs/bazi_knowledge/calendar", "docs/bazi_knowledge/useful_god"),
        v40_target="engines/fact",
        rc2_action="补齐节气、真太阳时、大运起运、藏干、十神、合冲刑害破和用神候选事实。",
    ),
    ModuleMigrationStatus(
        key="signal_registry",
        label="信号注册与证据汇总",
        current_state="v40_native_ready_needs_assets",
        reuse_policy="migrate_v30_assets_as_runtime_signal",
        v30_sources=("evidence", "diagnosis/feature_engine", "rules"),
        v40_target="contracts/signal",
        rc2_action="把 V30 规则和特征萃取为 RuntimeSignal / CandidateSeed。",
    ),
    ModuleMigrationStatus(
        key="decision_engine",
        label="Decision Engine",
        current_state="v40_native_ready_needs_domain_depth",
        reuse_policy="keep_v40_native",
        v30_sources=("diagnosis/claim_generator", "reasoning"),
        v40_target="decision",
        rc2_action="继续作为唯一 verdict 授权者，接收 domain adapter hints。",
    ),
    ModuleMigrationStatus(
        key="domain_verdict_adapters",
        label="领域判断 Adapter",
        current_state="new_required",
        reuse_policy="build_v40_native_from_v30_domain_assets",
        v30_sources=("diagnosis/path_engine", "knowledge/packs", "rules"),
        v40_target="decision/domain_adapters",
        rc2_action="先做 wealth/career/relationship/health/useful_god/luck_timing/family。",
    ),
    ModuleMigrationStatus(
        key="llm_expression",
        label="LLM 表达层",
        current_state="v40_native_ready",
        reuse_policy="keep_v40_native",
        v30_sources=("llm", "expression", "semantics"),
        v40_target="expression",
        rc2_action="LLM 继续负责组织语言和解释，不负责最终命理裁决。",
    ),
    ModuleMigrationStatus(
        key="conversation_probe",
        label="智能对话与追问",
        current_state="v40_native_ready_needs_hidden_factor_depth",
        reuse_policy="migrate_v30_probe_assets_as_templates",
        v30_sources=("questions", "dialogue_chain", "hidden_factor/question_strategy"),
        v40_target="conversation",
        rc2_action="从一次性问答升级为可持续 probe chain，并写回训练标签。",
    ),
    ModuleMigrationStatus(
        key="hidden_factor_probe_engine",
        label="Hidden Factor Probe Engine",
        current_state="v40_native_v1_probe_signal_ready",
        reuse_policy="build_v40_native_with_v30_hidden_factor_assets",
        v30_sources=("hidden_factor",),
        v40_target="probes/hidden_factor",
        rc2_action="V1 已能按 VOI 生成隐藏线索 Probe，并把回答绑定为 reality_probe RuntimeSignal / HiddenAttributeUpdate / TrainingLabelEvent。",
    ),
    ModuleMigrationStatus(
        key="knowledge_cards",
        label="知识卡与解释依据",
        current_state="v30_asset_migration_required",
        reuse_policy="migrate_as_knowledge_card_not_judge",
        v30_sources=("knowledge", "docs/bazi_knowledge"),
        v40_target="knowledge_cards",
        rc2_action="只作为 ExplanationBasis，不允许直接下断语。",
    ),
    ModuleMigrationStatus(
        key="portrait_signals",
        label="画像信号",
        current_state="v30_asset_migration_required",
        reuse_policy="migrate_as_low_weight_portrait_signal",
        v30_sources=("portrait", "diagnosis/portrait_engine"),
        v40_target="signals/portrait",
        rc2_action="低权重进入候选判断，不直接输出用户强断语。",
    ),
    ModuleMigrationStatus(
        key="rule_path_assets",
        label="规则、路径与做功资产",
        current_state="v30_asset_migration_required",
        reuse_policy="migrate_as_signal_path_conflict",
        v30_sources=("rules", "diagnosis/rule_matcher", "diagnosis/path_engine", "diagnosis/graph"),
        v40_target="signals/path",
        rc2_action="规则只生成信号、路径和冲突候选，不直接变成 verdict。",
    ),
    ModuleMigrationStatus(
        key="ziwei_sidecar",
        label="紫微 Domain Lens",
        current_state="v40_sidecar_ready_needs_asset_migration",
        reuse_policy="sidecar_asset_migration_only",
        v30_sources=("ziwei",),
        v40_target="engines/ziwei_native",
        rc2_action="保持第二引擎旁路定位，只做辅助证据，不和八字平权。",
    ),
    ModuleMigrationStatus(
        key="asset_migration_gate",
        label="命理资产迁移 Gate",
        current_state="v40_native_v1_sidecar_ready",
        reuse_policy="build_v40_native",
        v30_sources=("core", "rules", "diagnosis", "knowledge", "portrait", "questions", "hidden_factor", "ziwei"),
        v40_target="migration/mingli_assets",
        rc2_action="V1 已支持 plain JSON asset -> RuntimeSignal sidecar；下一步接 before/after diff 与 enabled gate。",
    ),
    ModuleMigrationStatus(
        key="real_case_bank",
        label="真实案例库与验收窗口",
        current_state="new_required",
        reuse_policy="build_v40_native",
        v30_sources=("evaluation/case_bank",),
        v40_target="evaluation/acceptance_window",
        rc2_action="先收 100-200 个高质量案例，作为命理纵深验收主轴。",
    ),
    ModuleMigrationStatus(
        key="legacy_v30_ui_admin",
        label="V30 旧 UI/Admin/混合流程",
        current_state="no_reuse",
        reuse_policy="do_not_migrate_runtime_or_ui",
        v30_sources=("frontend", "admin_frontend", "admin"),
        v40_target="none",
        rc2_action="只参考体验，不迁移旧流程和主系统 admin 逻辑。",
    ),
)


def build_module_migration_status() -> dict[str, object]:
    status_counts = Counter(module.current_state for module in MODULES)
    reuse_counts = Counter(module.reuse_policy for module in MODULES)
    module_payload = [_serialize(module) for module in MODULES]
    reusable_v30_asset_groups = sum(
        1
        for module in MODULES
        if module.v30_sources
        and module.reuse_policy
        in {
            "refactor_v30_algorithm_into_v40",
            "build_v40_native_with_v30_reference_tests",
            "migrate_v30_assets_as_runtime_signal",
            "build_v40_native_from_v30_domain_assets",
            "migrate_v30_probe_assets_as_templates",
            "build_v40_native_with_v30_hidden_factor_assets",
            "migrate_as_knowledge_card_not_judge",
            "migrate_as_low_weight_portrait_signal",
            "migrate_as_signal_path_conflict",
            "sidecar_asset_migration_only",
        }
    )
    new_required = sum(1 for module in MODULES if module.current_state == "new_required")
    return {
        "version": "v40.module_migration_status.v1",
        "phase": "V40-RC2: Mingli Depth Migration",
        "summary": {
            "module_groups_total": len(MODULES),
            "v40_native_or_ready_groups": sum(1 for module in MODULES if module.current_state.startswith("v40_")),
            "v30_direct_runtime_reuse_allowed": 0,
            "reusable_v30_asset_groups": reusable_v30_asset_groups,
            "new_required_groups": new_required,
            "no_reuse_groups": status_counts.get("no_reuse", 0),
        },
        "status_counts": dict(sorted(status_counts.items())),
        "reuse_counts": dict(sorted(reuse_counts.items())),
        "modules": module_payload,
        "mainline_sequence": [
            "P0: Real Case Bank / Acceptance Window",
            "P1: Bazi Fact Engine Pro",
            "P2: Asset Migration Gate + V30 Mingli Asset Pipeline",
            "P3: Domain Verdict Adapters",
            "P4: Hidden Factor Probe Engine",
            "P5: Knowledge / Portrait / Ziwei sidecar enrichment",
        ],
        "hard_rule": "V40 can reuse V30 mingli assets only through DTO/adapters; direct v30 runtime import remains zero.",
        "boundary": "module_migration_status_observes_planned_reuse_without_importing_v30_runtime",
    }


def _serialize(module: ModuleMigrationStatus) -> dict[str, object]:
    return {
        "key": module.key,
        "label": module.label,
        "current_state": module.current_state,
        "reuse_policy": module.reuse_policy,
        "v30_sources": list(module.v30_sources),
        "v40_target": module.v40_target,
        "rc2_action": module.rc2_action,
    }
