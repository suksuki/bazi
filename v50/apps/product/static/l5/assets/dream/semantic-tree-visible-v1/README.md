# SEMANTIC_TREE_VISIBLE_V1

阿布生命森林固定生命树的正式分层素材候选包。

```text
status: OWNER_REVIEW_REQUIRED
scope: Stage 2｜SEMANTIC_TREE_VISIBLE
source_pack_sha256: 475fe133ff098a216257bc56fe24585139a3312446b1b0180ce46b15835717ee
```

## 交付内容

```text
assets/tree_base_clean.png
assets/leaf_basic_01.png
assets/leaf_basic_02.png
assets/trunk_backbone_01.png
assets/energy_flow_mask.png
assets/energy_flow_mask.svg
assets/flower_bud_closed.png
assets/flower_open.png
assets/fruit_white.png
assets/foreground_occlusion.png
assets/abu_character_v1_poster.png
assets/abu_character_v1.webm

masks/leaf_basic_01_hit_mask.png
masks/leaf_basic_02_hit_mask.png
masks/trunk_backbone_01_hit_mask.png
masks/flower_bud_closed_hit_mask.png
masks/flower_open_hit_mask.png
masks/fruit_white_hit_mask.png
```

## 正式语义

```text
ROOT_SOURCE_SNAPSHOT
  = 服务端数据来源与命理根基，不是点击节点

LEAF_BASIC_01 / 02
  = 两项结构事实题

TRUNK_BACKBONE_01
  = 一项整盘骨干判断题

FLOWER_BLINDROUND_01
  = 三项前置完成后由服务端解锁

FRUIT_RESULT
  = Player Seal + System Seal 成立后的结果状态
```

## 视觉状态

1. 初始固定树：
   `tree_base_clean + 两片叶 + 树干纹理 + flower_bud_closed + 独立 Abu`
2. 三项前置完成：
   播放 `energy_flow_mask`，原位将花骨朵替换为 `flower_open`
3. 双 Seal 成立：
   原位将花替换为 `fruit_white`
4. `foreground_occlusion` 位于花或果实之前，用于形成真实枝叶遮挡。

果实在双 Seal 前不得显示。花朵解锁只能读取服务端状态。

## 图层顺序

```text
0  tree_base_clean
1  energy_flow_mask（仅传导时显示）
2  trunk_backbone_01（默认 opacity 0.62）
3  leaf_basic_01 / leaf_basic_02
4  flower_bud_closed / flower_open / fruit_white（三选一）
5  foreground_occlusion
6  ABU_CHARACTER_V1
7  问题带与必要 UI
```

## 接入硬边界

- 固定镜头，不推近、不上下移动。
- 页面无滚动、无悬浮球、无轨道环、无问号按钮。
- 所有器官必须保持在同一棵树的锚点上。
- 不得把正确答案、判定规则或解锁条件写入前端。
- 不得回退到旧树、烘焙旧大阿布的母版或 CSS 假叶片。
- `tree_base_clean` 内没有阿布、花、果实或题目标记。
- `ABU_03` 与三树选择过程不在本包改动范围内。

## Owner 验收

先查看：

```text
previews/semantic_tree_desktop_three_states.png
previews/semantic_tree_mobile_stage2.png
previews/semantic_tree_organ_contact_sheet.png
```

本次只需回答一个问题：

```text
这是不是我们要的、真正长在同一棵生命树上的两片叶、树干和花骨朵？
```

