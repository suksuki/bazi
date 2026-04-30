# V19 P68 Test Tiers

P68 解决开发效率问题：不是每次小改都跑完整测试，而是按风险分层验证。

## 测试分层

### fast

脚本：`v19/scripts/test_fast.sh`

用途：

- Python 语法编译。
- manifest JSON 基础校验。
- 当前多语言回答面和测试脚本的关键回归。

建议场景：前端 payload、回答文案、轻量后端 helper 改动后先跑。

### targeted

脚本：`v19/scripts/test_targeted.sh`

用途：

- 默认覆盖近期主线阶段：P46-P68、P10 review。
- 可传入 pytest `-k` 表达式，只跑指定阶段。

示例：

```bash
./v19/scripts/test_targeted.sh 'p67 or p68'
./v19/scripts/test_targeted.sh 'p65 or p66 or p67'
```

建议场景：涉及 Rule Graph、回答链路、主线审计、语言面时跑。

### full

脚本：`v19/scripts/test_full.sh`

用途：

- 完整运行 `v19/tests`。
- 支持继续传 pytest 参数。

建议场景：规则路由、知识库、服务端主链路、manifest 或多模块联动改动后，在收束前跑一次。

## 当前策略

- 小改先 fast。
- 触及主链路跑 targeted。
- 阶段收束或跨模块改动跑 full。
- full 仍保留，但不再作为每次保存后的默认动作。
