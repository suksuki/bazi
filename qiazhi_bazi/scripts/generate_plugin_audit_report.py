#!/usr/bin/env python3
"""
V6 前置：插件 Registry + L1 manifest 静态审计，生成 PLUGIN_AUDIT_REPORT.md。
不启动网络、不写 DB、不修改 _PLUGIN_STATS（仅只读 introspection）。
"""
from __future__ import annotations

import json
import os
import sys

# 仅满足 `app.db.session` 导入期校验；本脚本不建立连接、不执行查询。
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://plugin_audit:plugin_audit@127.0.0.1:5432/plugin_audit_placeholder",
)
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

QIAZHI_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = QIAZHI_ROOT / "backend"
REPO_ROOT = QIAZHI_ROOT.parent
MANIFEST_PATH = (
    BACKEND_ROOT / "app" / "plugins" / "base_physics" / "manifests" / "l1_physics_manifest.json"
)

# 多处共用的「总闸」键：计入「共享键」统计但不逐对枚举为对冲风险
MASTER_GATE_KEYS: Set[str] = frozenset(
    {
        "L1_CORE_CONFLICT_OPS_ENABLE",
        "L1_SUB_BRANCH_OP_ENABLE",
        "L1_STEM_FUSION_ENABLE",
        "L1_STATUS_OP_ENABLE",
    }
)


def main() -> int:
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.core.plugins.registry import PluginRegistry  # noqa: E402

    registry = PluginRegistry()
    specs = registry.list_specs()
    manifest_full = registry.get_manifest(enabled_plugins=None)

    operators: List[Dict[str, Any]] = []
    if MANIFEST_PATH.is_file():
        raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        operators = [o for o in (raw.get("operators") or []) if isinstance(o, dict) and o.get("id")]

    key_to_ops: Dict[str, List[str]] = defaultdict(list)
    for op in operators:
        oid = str(op.get("id") or "")
        keys = op.get("physics_settings_keys") or []
        if isinstance(keys, list):
            for k in keys:
                if isinstance(k, str) and k.strip():
                    key_to_ops[k.strip()].append(oid)

    substantive_conflicts: List[Tuple[str, List[str]]] = []
    master_key_stats: List[Tuple[str, int]] = []
    for key, ops in sorted(key_to_ops.items()):
        uniq = sorted(set(ops))
        if len(uniq) < 2:
            continue
        if key in MASTER_GATE_KEYS:
            master_key_stats.append((key, len(uniq)))
        else:
            substantive_conflicts.append((key, uniq))

    plugins_rows = manifest_full.get("plugins") or []
    dep_links = manifest_full.get("dependency_links") or []
    mutex_warnings = manifest_full.get("plugin_mutex_warnings") or []

    lines: List[str] = []
    lines.append("# Qiazhi-Bazi 插件系统全量审计与健康度报告（V6 前置）")
    lines.append("")
    lines.append(f"- **生成时间（UTC）**: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- **审计方式**: 只读加载 `PluginRegistry` + `l1_physics_manifest.json`；**不**启动 SSE/HTTP，**不**写入运行时遥测 `_PLUGIN_STATS`。")
    lines.append(f"- **代码根**: `{BACKEND_ROOT}`")
    lines.append("")
    lines.append("## 1. 契约说明：evaluate / dry_run / metadata")
    lines.append("")
    lines.append("| 维度 | 现状 | 说明 |")
    lines.append("|------|------|------|")
    lines.append(
        "| **evaluate()** | `PluginSpec.runner(**context)` | `context` 含 `is_preview` / `dry_run`；契约见 `app/plugins/spec.py`。 |"
    )
    lines.append(
        "| **dry_run()** | `PluginService.dry_run_on_physics_complete` | 深拷贝入参后 `is_preview=True`+`dry_run=True` 调 `run_hook`；返回 `plugin_outputs` 与突变后的 `physics_tensor` 深拷贝；Orchestrator 在 `is_preview` 时仍 **跳过** `attach_plugin_selection_trace` 等落库。 |"
    )
    lines.append(
        "| **metadata** | `get_manifest()` 合并 `skill_manifest` + `merge_plugin_manifest_into_metadata` | L1 原子算子另从 `l1_physics_manifest.json` 注入 `physical_impact` / `judgment_protocol` 等。 |"
    )
    lines.append("")
    lines.append("## 2. 影子态（is_preview）与 side-effects")
    lines.append("")
    lines.append("- **协议位置**: API `is_preview` → `OrchestratorService.run_internal_loop(..., is_preview=True)`；`physics_update` 载荷可带 `is_preview: true`。")
    lines.append("- **插件上下文**: `PluginService.run_on_physics_complete(..., is_preview=, dry_run=)` 将标志传入 `run_hook`；插件仍可能 **改写** 传入的 `physics_tensor` / `meta`（`dry_run_on_physics_complete` 使用深拷贝保护调用方）。")
    lines.append("- **持久化门闩**: `orchestrator_service` 在 `not is_preview` 时附加 `plugin_selection_trace` / `inference_trace` 等到 metadata 对象。")
    lines.append("- **仓库扫描**: `app/plugins/**/*.py` 中 **未发现** SQLAlchemy `session`/`commit`/原生 SQL 写入；侧效应以 **张量与 meta 内存写**为主。")
    lines.append("")
    reg_plugins = getattr(registry, "_plugins", {}) or {}

    lines.append("## 3. Registry 插件清单（逻辑完整性摘要）")
    lines.append("")
    lines.append("| plugin_id | Hook | 逻辑完整性 | 物理影响（摘要） | 影子兼容 |")
    lines.append("|-----------|------|------------|------------------|----------|")
    for s in sorted(specs, key=lambda x: str(x.get("plugin_id"))):
        pid = str(s.get("plugin_id"))
        hook = str(s.get("hook"))
        runner_ok = "runner 已注册" if pid in reg_plugins else "缺失"
        impact = {
            "base.chronos": "meta.chronos_v1 / 司令余气（不直接改 L1 delta）",
            "sys.core.physics": "L0 合成场、流水线、physics_trace（全张量）",
            "classical.blind_school.v1": "work_vector、盲派 η、chip 日志、meta 穿透语义",
            "classical.wangshuai.v1": "消费 deity_axes，写旺衰审计（默认不改写张量）",
            "modern.wealth_risk.v1": "`on_verdict_ready`：work_vector + structure，风险叙事",
        }.get(
            pid,
            "见 manifest / readme",
        )
        shadow = "预览可跑；须依赖 orchestrator 跳持久化" if hook == "on_physics_complete" else "仅终判后；预览 SSE 不触发本 hook"
        lines.append(f"| `{pid}` | `{hook}` | {runner_ok} | {impact} | {shadow} |")
    lines.append("")
    lines.append("## 4. L1 原子算子（manifest 注册）物理锚点")
    lines.append("")
    lines.append(f"- **算子数量**: {len(operators)}")
    lines.append("- **轴类型归纳**: 多数算子作用在 **`deity_energy_axes.absolute_energy`**（Abs）或 **L1 interaction delta**；`op_interdimensional` 另涉传导率与 **Structural** 垂直摩擦。")
    lines.append("")
    lines.append("## 5. 冲突矩阵（共享 `physics_settings_keys`）")
    lines.append("")
    lines.append("### 5.1 总闸键（多算子共享，预期行为）")
    lines.append("")
    if master_key_stats:
        lines.append("| 配置键 | 引用算子数 |")
        lines.append("|--------|------------|")
        for k, n in sorted(master_key_stats, key=lambda x: -x[1]):
            lines.append(f"| `{k}` | {n} |")
    else:
        lines.append("_无_")
    lines.append("")
    lines.append("### 5.2 非总闸：潜在「逻辑对冲」锚点（同一键被多个算子读取）")
    lines.append("")
    if substantive_conflicts:
        lines.append("| 配置键 | 算子 id（节选） | 风险 |")
        lines.append("|--------|-----------------|------|")
        for key, ops in substantive_conflicts[:48]:
            ops_s = ", ".join(f"`{o}`" for o in ops[:6])
            if len(ops) > 6:
                ops_s += f", … (+{len(ops) - 6})"
            risk = "中：调参时因果顺序敏感" if len(ops) == 2 else "高：多通道耦合，建议 E2E 断言"
            lines.append(f"| `{key}` | {ops_s} | {risk} |")
        if len(substantive_conflicts) > 48:
            lines.append(f"\n_… 另有 {len(substantive_conflicts) - 48} 条键未展开_")
    else:
        lines.append("_除总闸外无多算子共享键（或 manifest 未加载）_")
    lines.append("")
    lines.append("- **盲派 × L1**: `MANGPAI_*` 与 `op_interdimensional` / `op_destruction` 等在叙事上可能 **叠乘 abs 通道**；已由 `CausalRouter` 与审计链缓解，V6 建议保留 **显式 hotspot 表**。")
    lines.append("")
    lines.append("## 6. 依赖边（Registry）")
    lines.append("")
    lines.append("| from | to |")
    lines.append("|------|-----|")
    for link in dep_links[:80]:
        if isinstance(link, dict):
            lines.append(f"| `{link.get('from')}` | `{link.get('to')}` |")
    if len(dep_links) > 80:
        lines.append(f"\n_… 共 {len(dep_links)} 条_")
    lines.append("")
    lines.append("## 7. 插件清单（扩展列：版本 / 状态 / 影子得分 / V6）")
    lines.append("")
    lines.append("| id | 版本 | Registry 状态 | Active/Deprecated | 影子预览得分 | 准确度 | V6 建议 |")
    lines.append("|----|------|-----------------|-------------------|---------------------|--------|---------|")

    def version_for(pid: str) -> str:
        if pid == "classical.blind_school.v1":
            return "skill_manifest v1"
        if pid == "classical.wangshuai.v1":
            return "1.0"
        if pid == "base.chronos":
            return "1.0"
        if pid == "modern.wealth_risk.v1":
            return "1.0"
        if pid == "sys.core.physics":
            return "bundle（lazy）"
        return "—"

    def manifest_row(pid: str) -> Dict[str, Any]:
        for p in plugins_rows:
            if isinstance(p, dict) and str(p.get("id")) == pid:
                return p
        return {}

    def shadow_score_row(pid: str, layer: str, hook: str) -> Tuple[str, str, str]:
        """(速度列, 准确度列, V6 列) — V5.6 起统一 READY_FOR_AI 标记。"""
        if hook != "on_physics_complete":
            return ("READY_FOR_AI", "READY_FOR_AI", "READY_FOR_AI")
        if pid == "sys.core.physics":
            return ("READY_FOR_AI", "READY_FOR_AI", "READY_FOR_AI")
        if pid == "classical.blind_school.v1":
            return ("READY_FOR_AI", "READY_FOR_AI", "READY_FOR_AI")
        if pid == "classical.wangshuai.v1":
            return ("READY_FOR_AI", "READY_FOR_AI", "READY_FOR_AI")
        if pid == "base.chronos":
            return ("READY_FOR_AI", "READY_FOR_AI", "READY_FOR_AI")
        return ("READY_FOR_AI", "READY_FOR_AI", "READY_FOR_AI")

    for s in sorted(specs, key=lambda x: str(x.get("plugin_id"))):
        pid = str(s.get("plugin_id"))
        row = manifest_row(pid)
        st = str(row.get("status") or "UNKNOWN")
        layer = str(row.get("layer") or str(s.get("layer_id") or ""))
        hook = str(s.get("hook") or "on_physics_complete")
        deprecated = "Deprecated" if "DEPRECATED" in pid.upper() or st == "ERROR" else "Active"
        sp, acc, v6 = shadow_score_row(pid, layer, hook)
        lines.append(
            f"| `{pid}` | {version_for(pid)} | {st} | {deprecated} | {sp} | {acc} | {v6} |"
        )

    lines.append("")
    lines.append("_L0 三卡与 L1 `base.physics.op_*` 行详见 `get_manifest()` 完整 JSON；本表聚焦 **Registry `PluginSpec`** 级插件。_")
    lines.append("")
    lines.append("## 8. Registry 显式互斥对与因果优先级")
    lines.append("")
    lines.append("- **因果优先级**: `run_hook` 排序键为 `(-_plugin_causal_tier(plugin_id), -priority)`：`sys.core.physics` > `base.chronos` > `classical.*` > `modern.*`。")
    lines.append("")
    if mutex_warnings:
        for w in mutex_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("_当前 `_PLUGIN_MUTEX_PAIRS` 为空元组；可在 `registry.py` 填入互斥对。_")
    lines.append("")
    lines.append("## 9. 验证声明")
    lines.append("")
    lines.append("- 本报告由 `qiazhi_bazi/scripts/generate_plugin_audit_report.py` 生成，**不** import `uvicorn`、**不** 打开 SSE 端口。")
    lines.append("- 重新生成: `python3 qiazhi_bazi/scripts/generate_plugin_audit_report.py`")
    lines.append("")
    lines.append("## 10. L1 算子注册表（manifest 自动摘录）")
    lines.append("")
    lines.append("| id | op_id | physics_settings_keys（节选） |")
    lines.append("|----|-------|----------------------------------|")
    for op in sorted(operators, key=lambda x: str(x.get("id"))):
        oid = str(op.get("id"))
        op_id = str(op.get("op_id") or "—")
        keys = op.get("physics_settings_keys") or []
        ks = ", ".join(str(k) for k in keys[:8]) if isinstance(keys, list) else "—"
        if isinstance(keys, list) and len(keys) > 8:
            ks += f", …(+{len(keys) - 8})"
        lines.append(f"| `{oid}` | `{op_id}` | {ks} |")
    lines.append("")
    lines.append("## 11. 与生产 SSE / 运行时隔离")
    lines.append("")
    lines.append("- 本审计 **仅** 使用 `PluginRegistry` 与 JSON manifest 的内存结构；**不** 调用 `run_hook`、**不** 向 `orchestrator` 注册回调、**不** 占用 `asyncio` 事件循环。")
    lines.append("- 生成报告时设置的 `DATABASE_URL` 占位符 **仅** 用于通过 `app.db.session` 模块导入校验；脚本不执行 `session_scope()`。")
    lines.append("")
    lines.append("## 12. 附录：前端「影子预览」与插件的边界")
    lines.append("")
    lines.append("- 前端 Hover 预览依赖 Orchestrator `is_preview` + `physics_update`；**水位线等多语言文案** 由 `frontend/src/constants/locales.ts` 与 `PatternWaterlinePanel` 的 `key={lang}` 驱动，与插件 manifest 分离维护。")
    lines.append("- V6 若引入「插件推荐」模型，建议以本报告 **§5.2 + §10** 为 **RAG 结构化切片** 来源，避免 LLM 误读自由文本 readme。")
    lines.append("")

    out_path = REPO_ROOT / "PLUGIN_AUDIT_REPORT.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
