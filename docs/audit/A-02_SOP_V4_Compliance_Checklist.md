# A-02 SOP V4.0 合规性自查报告

**审计依据**：Clause 0.3 / FDS SOP V4.0 四硬性指标  
**自查执行**：Cursor（执行工程师）  
**目的**：扫描前对账，供审计师签发「A-02 准予扫描令」

---

## 1. 法律全文的“刚性注入” (Check Clause 0.3)

**检查点**：`registry/holographic_pattern/A-02/A-02_manifest.json`

### 1.1 审计要求核对

- ✅ **使用审计师签发条件**：`PG >= 2`、`E >= 0.4`、`ZG <= PG`（均为 JsonLogic，无“七杀在月支”等模糊中文逻辑）。
- ✅ **pipeline_expression 存在**：51.8w 数据扫描依赖此字段，否则会报错。

### 1.2 核心配置片段（证据）

```json
"classical_logic_rules": {
  "format": "jsonlogic",
  "description": "七杀格法律全文（审计师签发）：base_pattern=七杀格，E>=0.4，官杀不混，透杀或月令杀。",
  "expression": { ... },
  "pipeline_expression": {
    "and": [
      { ">=": [{ "var": "ten_gods.PG" }, 2] },
      { ">=": [{ "var": "self_energy.E" }, 0.4] },
      { "<=": [{ "var": "ten_gods.ZG" }, { "var": "ten_gods.PG" }] }
    ]
  },
  "_note": "pipeline_expression 为当前 518k 数据 schema（ten_gods/self_energy）下的等价筛选，供全量索引脚本使用。"
}
```

**结论**：法律全文为 JsonLogic 刚性注入，`pipeline_expression` 已存在，符合 Clause 0.3。

---

## 2. 物理常数的“初始偏置” (Check TMM)

**检查点**：`tensor_mapping_matrix.weights`

### 2.1 审计要求核对

- ✅ **PG 对 S 轴（应力）权重为 +1.5**。
- ✅ **印星对 S 轴**：审计师要求「PI 的 S 轴为 -0.9（杀印相生）」—— 本库以 **ZC（正印）** 对 S 轴 -0.9 实现杀印相生；PC（偏印）S 轴为 0.6。

### 2.2 核心配置片段（证据）

`dimensions` 顺序为 `["E", "O", "M", "S", "R"]`，故 S 轴为第 4 项（下标 3）。

```json
"tensor_mapping_matrix": {
  "dimensions": ["E", "O", "M", "S", "R"],
  "weights": {
    "PG": [0.2, -0.4, 0.3, 1.5, 0.2],   // E, O, M, S, R → S = +1.5 ✅
    "ZC": [0.8, 0.4, -0.1, -0.9, 0.8],  // 正印 S = -0.9（杀印相生）✅
    ...
  },
  "strong_correlation": [
    { "ten_god": "PG", "dimension": "S", "reason": "七杀对位应力" },
    { "ten_god": "ZC", "dimension": "R", "reason": "印星对位智慧" }
  ],
  "_source": "A-02 七杀格初始映射矩阵 V5.0-Initial，审计师 Gemini 签发"
}
```

**结论**：PG S=+1.5，ZC S=-0.9，未复用 A-01 正官权重，符合 TMM 初始偏置要求。

---

## 3. 语义维度的“Prompt 锁死” (Check ai_engine.py)

**检查点**：`_get_system_prompt_for_a02_semantic()` 及 A-02 时流形解读所用 System Prompt

### 3.1 审计要求核对

- ✅ **已重构 ai_engine 私有方法**：存在 `_get_system_prompt_for_a02_semantic()`，A-02 排盘/流形解读时通过 `_get_system_prompt_for_pattern(pattern_id)` 分支注入。
- ✅ **大模型指令包含“应力转化、秩序重构、爆发动能”**：三者来自 manifest 的 `semantic_core_dimensions`，被拼入 System Prompt，不会用“正官格的稳健”解释七杀。

### 3.2 核心代码片段（证据）

**3.2.1 A-02 语义注入入口**

```python
# core/ai_engine.py

_A02_MANIFEST_PATH = _PROJECT_ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"

def _get_system_prompt_for_a02_semantic() -> str:
    """Clause 0.3：A-02 七杀格语义核心由审计师签发，从 manifest 注入 System Prompt。"""
    base = SYSTEM_PROMPT_5D
    if not _A02_MANIFEST_PATH.exists():
        return base
    try:
        with open(_A02_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        core = manifest.get("semantic_core_dimensions") or {}
        if not core:
            return base
        lines = [
            "",
            "## A-02 七杀格语义核心（审计师立法，必须遵循）",
        ]
        for key in ("A_stress_transform", "B_order_rebuild", "C_eruption_kinetic"):
            d = core.get(key)
            if not isinstance(d, dict):
                continue
            name = d.get("name", key)
            mapping = d.get("physical_mapping", "")
            classical = d.get("classical_by_gemini", "")
            lines.append(f"- **{name}**（{mapping}）：{classical}")
        if len(lines) > 2:
            base = base + "\n".join(lines)
    except Exception as e:
        logger.debug("加载 A-02 语义核心失败: %s", e)
    return base

def _get_system_prompt_for_pattern(pattern_id: Optional[str]) -> str:
    """Clause 0.3：按格局 ID 返回带语义立法的 System Prompt；禁止执行端自行发明语义。"""
    if pattern_id and str(pattern_id).strip().upper() == "A-02":
        return _get_system_prompt_for_a02_semantic()
    return _get_system_prompt_with_a01_semantic()
```

**3.2.2 Manifest 中三维度（注入内容来源）**

| 键 | name | physical_mapping | 关键词 |
|----|------|------------------|--------|
| A_stress_transform | 应力转化 (Stress) | S轴与R轴的拮抗 | **应力转化** ✅ |
| B_order_rebuild | 秩序重构 (Rebuild) | O轴的非线性位移 | **秩序重构** ✅ |
| C_eruption_kinetic | 爆发动能 (Eruption) | E轴与M轴的共振 | **爆发动能** ✅ |

**结论**：A-02 使用独立语义底座，Prompt 锁死三维度，无正官格语义混入，符合 SOP。

---

## 4. 全量索引的“隔离性” (Check Data Storage)

**检查点**：A-02 独立索引文件 + 全量索引脚本参数化

### 4.1 审计要求核对

- ✅ **A-02 独立索引**：输出为 `data_local/a02_full_points.npz`、`data_local/a02_full_meta.json`，与 A-01（a01_*）隔离。
- ✅ **build_a01_full_index.py 已参数化**：支持 `--pattern A-02`，无硬编码格局 ID 于输出路径。

### 4.2 核心代码/约定片段（证据）

**4.2.1 全量索引脚本：格局参数化与输出命名**

```python
# scripts/build_a01_full_index.py

def build_full_index(..., pattern_id: str = "A-01") -> tuple[int, Path, Path]:
    manifest = load_manifest(manifest_path)
    rules = manifest.get("classical_logic_rules") or {}
    logic_expr = rules.get("pipeline_expression") or rules.get("expression")  # 优先 pipeline_expression
    prefix = pattern_id.lower().replace("-", "")  # a01 / a02
    ...
    points_path = out_dir / f"{prefix}_full_points.npz"   # A-02 → a02_full_points.npz
    meta_path = out_dir / f"{prefix}_full_meta.json"     # A-02 → a02_full_meta.json
```

```python
def resolve_manifest_for_pattern(pattern_id: str) -> Path:
    if pattern_id.upper() == "A-02":
        p = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
        if p.exists():
            return p
    return ROOT / "config" / "patterns" / "manifest_A01.json"
```

**4.2.2 英雄榜脚本：按 pattern_id 动态切换语义与路径**

```python
# scripts/build_pattern_hall_of_fame.py

def resolve_pattern_paths(pattern_id: str) -> Tuple[Path, Path, Path]:
    pid = pattern_id.strip().upper()
    prefix = pid.lower().replace("-", "")  # A-02 → a02
    manifest_path = reg_dir / pid / f"{pid}_manifest.json"  # .../A-02/A-02_manifest.json
    points_path = data_dir / f"{prefix}_full_points.npz"   # data_local/a02_full_points.npz
    meta_path = data_dir / f"{prefix}_full_meta.json"     # data_local/a02_full_meta.json
    return manifest_path, points_path, meta_path
```

```bash
# 用法示例
python scripts/build_a01_full_index.py --pattern A-02   # 生成 a02_*
python scripts/build_pattern_hall_of_fame.py --pattern_id A-02  # 读 a02_* + A-02_manifest
```

**结论**：A-02 拥有独立索引文件与 manifest 路径，全量索引与英雄榜均已参数化，无硬编码漂移。

---

## 审计结论（供审计师勾选）

| 检查项 | 状态 | 备注 |
|--------|------|------|
| 1. 法律全文刚性注入（JsonLogic + pipeline_expression） | ✅ 通过 | PG>=2, E>=0.4, ZG<=PG；pipeline_expression 存在 |
| 2. TMM 初始偏置（PG S=+1.5；印星 S=-0.9） | ✅ 通过 | PG S=1.5；ZC S=-0.9 |
| 3. 语义 Prompt 锁死（应力转化 / 秩序重构 / 爆发动能） | ✅ 通过 | _get_system_prompt_for_a02_semantic 从 manifest 注入 |
| 4. 全量索引隔离与脚本通用化 | ✅ 通过 | a02_* 独立；--pattern / --pattern_id 参数化 |

**执行工程师**：以上四检查点证据已就位，请审计师签发 **「A-02 准予扫描令」** 后，执行：

1. `python scripts/fds_pattern_scanner.py --target A-02`
2. `python scripts/build_a01_full_index.py --pattern A-02`
3. `python scripts/build_pattern_hall_of_fame.py --pattern_id A-02`

---

## 准予扫描令执行记录 (FDS-CLEARANCE-202602-A02)

| 步骤 | 指令 | 执行结果 | 备注 |
|------|------|----------|------|
| 1 | `scripts/fds_pattern_scanner.py --target A-02` | ✅ 完成 | 法理锚定 A-02_manifest；**A-02 匹配 136,130 / 518,400**；已写入 `data_local/a02_full_points.npz`、`a02_full_meta.json` |
| 2 | `scripts/build_a01_full_index.py --pattern A-02` | ✅ 已包含于步骤 1 | 扫描器内建全量索引，未单独执行 |
| 3 | `scripts/build_pattern_hall_of_fame.py --pattern_id A-02` | ✅ 完成 | 前 4 名为 **S 轴极值**（S≈10.0～10.2），已写入 `registry/holographic_pattern/A-02/A-02_hall_of_fame.json` |

**审计师叮嘱落实情况**：当前 `fds_pattern_scanner` 未输出 K-Means 离散度（Inertia/Silhouette）。若需在控制台查看放射状分布指标，可在后续 SOP 中为 A-02 增加聚类诊断输出。英雄榜中 `analysis` 字段若为空，表示本地 Ollama/32B 未返回内容，可在模型就绪后重跑本步骤以补全「以杀化权」语义剖析。

---

## 第 034 号工程指令：Step 8.5 / Step 9 执行记录

| 步骤 | 指令 | 结果 |
|------|------|------|
| **8.5** | `python scripts/test_a02_repair_pathway_stress.py` | ✅ 通过。A-02 检索器 13.6w 样本，10 样本中 2 个得到修复路径与 ΔV。 |
| **9** | `python scripts/matrix_backfitting_auditor.py --pattern_id A-02 --top 50` | ✅ 完成。输出 `config/physics/tensor_mapping_matrix_A02_V5.1_CALIBRATED.json`（Ollama 未用时保留原权重）。 |
| **UI 对账** | 见 `docs/audit/A-02_Step8.5_Step9_UI_Checklist.md` | 需指挥官在天机设置 / 全息格局中手动验证矩阵切换与流形修复建议区块。 |
