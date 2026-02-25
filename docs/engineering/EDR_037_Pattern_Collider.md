# 第 037 号工程指令：全息格局对撞与决策引擎

**状态**: 任务 1、2 已实现  
**SOP 依据**: FDS SOP V5.0（物理投影 + 语义融合）

---

## 目标

将审计过的格局、全量索引与 32B 推理整合为「全息格局对撞与决策引擎」：物理投影 + 置信度评分 + 混合格局语义合成，不做单一格局 if-else 排他。

---

## 任务 1：格局对撞调度器 (Pattern Collider) ✅

**位置**: `core/pattern_collider.py`

**逻辑**:
- 从 `registry/qga_manifest.json` 的 `topics.holographic_pattern` 读取已注册格局（A-01、A-02、A-03）。
- 对同一组十神向量，用各格局的 TMM 做**多矩阵并行投影**，得到每个格局下的 5D 点。
- 计算命主点到各格局流形质心的**马氏距离** $D_M$（A-01 使用 registry 内 mean/cov；A-02/A-03 使用 npz 均值或欧氏距离）。
- 通过软 max（`exp(-D_M/temperature)`）归一化得到**置信度**，输出 `Probabilistic_Patterns` 列表。

**使用**:
```python
from core.pattern_collider import run_pattern_collision, PatternCollider

ten_gods = {"ZG": 0.5, "PG": 2.1, ...}  # 或由 Controller._chart_to_ten_gods(chart, day_master) 得到
result = run_pattern_collision(ten_gods, temperature=1.0)
# result: [{"pattern_id": "A-02", "confidence_pct": 85.0, "d_m": 1.2, "point_5d": {...}}, ...]
```

**验收**: 已通过单元调用测试，返回 A-01/A-02/A-03 概率化比例及 $D_M$。

---

## 任务 2：混合格局语义合成 Prompt 模板 ✅

**位置**: `config/ai/prompts/combined_pattern_analysis.yaml`

**内容**:
- `system`: 角色与判词要求（兼顾各格局语义、格局间制衡、ΔV 优化方向）。
- `user_template`: 占位符 `mixed_ratio`、`hkb_semantic_a02`、`hkb_semantic_a03`、`point_5d_*`、`delta_v_repair`。
- 要求判词兼顾格局间相互制衡（如偏财生杀时的压力转化）。

**注入参数**: 由调用方从对撞结果与 HKB、Step 7 修复路径填充。

---

## B 计划：混合格局语义调用链闭环 ✅

**数据装配与上下文聚合**:
- **ai_engine**：`generate_combined_pattern_verdict(probabilistic_patterns, point_5d, repair_vector=..., debug_print_prompt=..., prompt_only=...)` 读取对撞结果、5D 坐标与 ΔV，填充 `combined_pattern_analysis.yaml`，调用 32B 生成判词；判词强制包含「五维运势断言」。
- **HKB 语义**：A-02 从 `registry/.../A-02_manifest.json` 的 `semantic_core_dimensions` 注入；A-03 从 `config/hkb/hkb_params.json` 的 `a03_semantic_core` 注入（缺失时使用默认偏财格描述）。
- **ΔV**：由调用方传入 `pathway_analyzer.analyze_repair_pathway(retriever, user_point)` 的 `repair_vector`（含 `delta_vector`）。

**控制器**:
- `HolographicPatternController.get_mixed_pattern_context(chart, day_master)`：返回 `{ probabilistic_patterns, point_5d }`，其中 `point_5d` 为按置信度加权的混合 5D 点，供测算页直接用于判词与 pathway。

**输出验证**:
- `python3 scripts/run_combined_pattern_prompt_demo.py --prompt-only`：在控制台打印 A-02 + A-03 混合案例的完整 Prompt，确保法理逻辑无漂移。

---

## 任务 3：UI 五维运势可视化（待实施）

- 动态雷达图：命主 5D 初始点。
- 流年位移线：雷达图上绘制流年位移矢量。
- 地域修正：下拉框 + E/O/M/S/R 修正参数。

---

## 任务 4：Step 6 验收（混合模式 IoU）

- 验证 A-01/A-02 在混合模式下的 IoU 审计是否正常，确保混合不导致物理坐标崩坏。

---

## 依赖

- `registry/qga_manifest.json` 中已注册的格局及 `manifest_ref` 可读。
- A-01 流形：`registry/holographic_pattern/A-01.json` 含 `feature_anchors.standard_manifold`。
- A-02/A-03 流形：可选 `data_local/a02_full_points.npz` 等用于均值/协方差（否则退化为欧氏距离）。
