# 测试说明 (Testing)

## 运行方式

### 1. 使用 pytest（推荐）

安装依赖后执行：

```bash
# 项目根目录
pip install pytest   # 或 pip install -r requirements-test.txt
python -m pytest tests/ -v --tb=short
```

仅运行 FDS 相关单元测试：

```bash
python -m pytest tests/unit/test_fds_inference_engine.py tests/unit/test_tensor_mapping_loader.py tests/unit/test_holographic_pattern_controller_fds.py tests/unit/test_ai_engine_pattern_overview.py tests/unit/test_build_full_index_a02.py -v
```

仅运行 FDS V4 回归（集成）：

```bash
python -m pytest tests/integration/test_fds_sop_v4_regression.py -v
# 或直接执行脚本（不依赖 pytest）
python tests/integration/test_fds_sop_v4_regression.py
```

### 2. 不使用 pytest

- **FDS SOP V3 集成**：`python tests/test_fds_sop_v3_integration.py`（自定义 `TestFDSSOPV3.run_all_tests()`）
- **FDS SOP V4 回归**：`python tests/integration/test_fds_sop_v4_regression.py`

## 测试范围与回归清单

| 类别 | 文件/模块 | 覆盖内容 |
|------|-----------|----------|
| 单元 | `test_fds_inference_engine.py` | FDS 推理引擎、JsonLogic、子格局识别 |
| 单元 | `test_tensor_mapping_loader.py` | TMM 加载、权重矩阵 |
| 单元 | `test_holographic_pattern_controller_fds.py` | `get_fds_sop_patterns`、`get_fds_pattern_detail`、`_chart_to_ten_gods`、`_calculate_fds_projection`、`calculate_tensor_projection(A-01)` |
| 单元 | `test_ai_engine_pattern_overview.py` | `_get_system_prompt_for_pattern`（A-01/A-02）、`_get_system_prompt_for_a02_semantic`、`generate_pattern_overview` |
| 单元 | `test_build_full_index_a02.py` | `resolve_manifest_for_pattern`(A-01/A-02)、`pipeline_expression` 优先、`get_weights_matrix`（A-02 回退） |
| 集成 | `test_fds_sop_v3_integration.py` | Manifest 存在与 schema、SOP 流程、QGA 格式、子格局、UI 注册 |
| 回归 | `test_fds_sop_v4_regression.py` | A-02 manifest、FDS 格局列表/详情、A-01 投影不报「格局不存在」、全量索引 A-02 表达式 |

## FDS V4.0 / A-02 相关断言要点

- **审计状态**：A-01=已审计，A-02=在审计中（`get_fds_sop_patterns` 的 `status`）。
- **A-02 法理**：`registry/holographic_pattern/A-02/A-02_manifest.json` 含 `classical_logic_rules.pipeline_expression`、`semantic_core_dimensions`、`tensor_mapping_matrix.weights`（可回退到 config/physics V4.0-BETA）。
- **全息页**：选 A-01/A-02 时走 `_calculate_fds_projection`，不再依赖旧 registry `get_pattern_by_id`，避免「格局 A-01 不存在」；`pattern_info` 为空时 UI 使用 `(pattern_info or {}).get(...)` 防护。

## 依赖

- 单元/集成测试不强制要求 518K 数据或 Ollama；部分用例在 manifest/registry 缺失时会 `pytest.skip`。
- 若需完整 E2E（含流形解读生成），需配置 Ollama 及可选 518K 数据路径。

---

## 全量测试与已知问题（最近一次运行）

在项目根执行（排除 3 个 import 失败模块）：

```bash
python -m pytest tests/ \
  --ignore=tests/final_arbitration_smoke_test.py \
  --ignore=tests/integration/test_meta_learning_integration.py \
  --ignore=tests/unit/test_video_logic.py \
  -v --tb=short
```

### 收集失败（ImportError，已用 --ignore 排除）

| 文件 | 原因 |
|------|------|
| `final_arbitration_smoke_test.py` | 无法从 `unified_arbitrator_master` 导入 `UnifiedArbitratorMaster` |
| `integration/test_meta_learning_integration.py` | 无模块 `core.bayesian_optimization` |
| `unit/test_video_logic.py` | 无模块 `yt_dlp` |

### 已知失败（与 FDS V4 无关，多为依赖/接口变更；最近一次约 10 failed / 155 passed）

- **test_jobs**：`QuantumEngine` 缺少 `calculate_chart`（扩展未加载）
- **test_theory_history**：Mock 返回值断言（LearningDB）
- **test_channel_workflow**：缺少 `youtube_transcript_api`
- **test_scheduler_logic**：缺少 `learning.knowledge_processor`
- **test_transformer_position_tuning**：`fuse_temporal_features` 形状 (5,) vs (10,) 不兼容
- **test_ui_modules**：`profile_section` 无 `_sync_profile_to_session`
- **test_ui_utils**：`ui.utils.st` 在 pytest 收集顺序下未正确 mock（streamlit）

### 仅跑 FDS + 核心通过用例

```bash
python -m pytest tests/unit/test_fds_inference_engine.py tests/unit/test_tensor_mapping_loader.py \
  tests/unit/test_holographic_pattern_controller_fds.py tests/unit/test_ai_engine_pattern_overview.py \
  tests/unit/test_build_full_index_a02.py tests/integration/test_fds_sop_v4_regression.py \
  tests/integration/test_controller_integration.py tests/test_fds_lkv.py \
  -v --tb=short
```
