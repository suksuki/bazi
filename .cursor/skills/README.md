# 项目级 Cursor Skills（本仓库）

本目录存放 **随仓库共享** 的 Agent Skills：每个 Skill 为独立子目录，**必须**包含 `SKILL.md`（YAML frontmatter + 正文）。详见 Cursor 约定与用户侧 `create-skill` 技能说明。

---

## 目录结构（约定）

```
.cursor/skills/
├── README.md                 # 本文件：规范与索引
├── ROADMAP.md                # 计划中的 Skill 与分阶段补充
├── _templates/
│   └── SKILL.template.md     # 新建 Skill 时可复制改名
├── fds-sop-classical-engine/ # 示例：FDS 古典引擎
│   └── SKILL.md
├── fds-sop-llm-verdict/
│   └── SKILL.md
└── （未来）qiazhi-xxx/       # 新 Skill：见命名规则
    └── SKILL.md
```

**原则**：

- **扁平**：Skill 子目录**直接**放在 `skills/` 下，**不要**再套一层 `skills/fds/xxx`（避免工具链不识别）。
- **前缀区分领域**（建议）：
  - **`fds-`**：Antigravity / FDS / `legacy/` 相关流程与 SOP。
  - **`qiazhi-`**：Qiazhi-Bazi / `qiazhi/`、`qiazhi_core` 相关协议与交互。
  - 其他主题可用 **`repo-`** 或领域缩写，在下方索引表中登记。
- **可选附件**：同一 Skill 目录内可放 `reference.md`、`examples.md`、`scripts/` 等（与官方建议一致）。

---

## 当前索引

| 目录名 | `name`（frontmatter） | 用途摘要 |
|--------|------------------------|----------|
| `fds-sop-classical-engine` | `fds-sop-classical-engine` | 古典格局匹配、registry、全息页格局展示等（legacy） |
| `fds-sop-llm-verdict` | `fds-sop-llm-verdict` | 全息 LLM 判词、Ollama/Qwen、流式中文叙事（legacy） |

（新 Skill 落地后请在本表追加一行。）

---

## 新建 Skill 的步骤

1. 复制 `_templates/SKILL.template.md` 为 `新目录名/SKILL.md`。
2. 填写 frontmatter：`name`（小写、连字符）、`description`（第三人称 + **何时触发**，≤1024 字）。
3. 正文写清：范围、与 `QIAZHI_BAZI_MASTER_PLAN.md` / `.cursorrules` 的对齐点、禁止事项。
4. 在 **本 README「当前索引」表** 与 **`ROADMAP.md`** 中登记或勾选。
5. 若 Skill 针对 Qiazhi，在描述中显式写 `qiazhi`、`BaziMetadata` 等触发词，便于 Agent 发现。

---

## 与北极星文档的关系

- 产品级原则见仓库根目录 **`QIAZHI_BAZI_MASTER_PLAN.md`**、**`.cursorrules`**。
- Skill 是 **任务级** 的操作说明，不替代宪法；物理参数仍以 `legacy/config` 等为唯一数值源（零硬编码）。
