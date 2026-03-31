# FDS 测试说明 (Testing Guide)

## 运行方式

### 1. FDS SOP V3 集成测试（推荐先跑）

```bash
python tests/test_fds_sop_v3_integration.py
```

- **覆盖**: Manifest/Registry 存在性、QGA 信封、子格局、丰度、UI 注册、Step 8 报告、TMM 加载器、推理引擎报告结构。
- **共 23 项断言**，无 pytest 依赖。

### 2. Pytest 单元与 LKV 测试

```bash
# 需先安装: pip install pytest numpy json-logic-quibble
pytest tests/unit/test_tensor_mapping_loader.py tests/unit/test_fds_inference_engine.py -v
pytest tests/unit/test_flux.py tests/unit/test_ui_logic.py tests/test_fds_lkv.py -v
```

- **FDS 相关**:
  - `tests/unit/test_tensor_mapping_loader.py`: V4.0 优先加载、回退、无效 V4 回退。
  - `tests/unit/test_fds_inference_engine.py`: 引擎加载、十神归一化、5D 投影、归位报告含 `matrix_version`、混合态与知识注入。
- **LKV**: `tests/test_fds_lkv.py` 中 VaultManager / QGAVV 依赖 `chromadb`，未安装时自动 skip。

### 3. 全量 pytest（部分模块可能缺依赖）

```bash
pytest tests/ --ignore=tests/batch_pressure_test_*.py --ignore=tests/pattern_lab.py -v
```

- 若出现 `ModuleNotFoundError`（如 pandas、lunar_python、ollama），属环境依赖，可只跑上述 1、2。

## 测试用例与文档对应

| 测试文件 | 对应文档/功能 |
|----------|----------------|
| `test_fds_sop_v3_integration.py` | FDS_SOP_v3.0.md Step 0–8、QGA 注册、Step 8 报告 |
| `test_tensor_mapping_loader.py` | 全局 TMM 加载、V4.0-BETA 优先（第 021 号指令） |
| `test_fds_inference_engine.py` | 推理引擎、流形归位、matrix_version 公示（第 018/021 号） |
| `test_fds_lkv.py` | LKV 协议、LogicCompiler、CensusEngine、ProtocolChecker |

## 新增/更新说明（本次全面测试）

- **新增**: `tests/unit/test_tensor_mapping_loader.py`（4 条）
- **新增**: `tests/unit/test_fds_inference_engine.py`（8 条）
- **扩展**: `test_fds_sop_v3_integration.py` 增加测试 9（Step 8 报告）、10（TMM 加载器）、11（推理报告含 matrix_version）
- **修复**: `test_fds_lkv.py` 中 LogicCompiler 断言（`filter_A_03`）、CensusEngine 使用 `compiler._compiled_filters`；VaultManager/QGAVV 使用 `pytest.importorskip("chromadb")` 避免缺依赖报错
