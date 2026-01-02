# 📜 QGA 古典格局海选过滤器全集 (FDS-V3.0 逻辑版)

**版本**: V1.0  
**地位**: Step 2 逻辑普查法定清单  
**原则**: 无张量介入，纯干支逻辑  
**状态**: ENFORCED

---

## 核心原则

**"古法筛选 → 物理发现"**

1. Step 2 海选只使用干支、十神、月令逻辑
2. 物理张量在 Step 3 拟合时才介入
3. 严禁在海选阶段引入 E/O/M/S/R 约束

---

## 一、A类：官杀系 (Power Systems)

### A-01 正官格 (Direct Officer)

**核心逻辑**：月令主气为正官，天干透出，无伤官破格。

```python
def filter_A01(bazi):
    # F1: 月令主气为官
    if bazi.month_branch_main_energy != 'zheng_guan':
        return False
    # F2: 天干透官
    if 'zheng_guan' not in bazi.stem_array:
        return False
    # F3: 天干不露伤官
    if 'shang_guan' in bazi.stem_array:
        return False
    # F4: 地支有官星之根
    if bazi.count_root('zheng_guan') < 1:
        return False
    return True
```

---

### A-02 七杀格 (Seven Killings)

**核心逻辑**：月令主气为七杀，需有制化（食神制或印星化）。

```python
def filter_A02(bazi):
    # F1: 月令主气为七杀
    if bazi.month_branch_main_energy != 'qi_sha':
        return False
    # F2: 天干透杀
    if 'qi_sha' not in bazi.stem_array:
        return False
    # F3: 有制化（食神制杀 或 印星化杀）
    has_control = ('shi_shen' in bazi.stem_array or 
                   'pian_yin' in bazi.stem_array or
                   'zheng_yin' in bazi.stem_array)
    if not has_control:
        return False
    return True
```

---

### A-03 羊刃格 (Yang Blade)

**核心逻辑**：阳干生于刃地，喜官杀制约。

```python
# 羊刃对照表
YANG_REN_MAP = {
    '甲': '卯', '丙': '午', '戊': '午',
    '庚': '酉', '壬': '子'
}

def filter_A03(bazi):
    # F1: 日主为阳干
    if bazi.day_master not in ['甲', '丙', '戊', '庚', '壬']:
        return False
    # F2: 月令为羊刃
    expected_blade = YANG_REN_MAP.get(bazi.day_master)
    if bazi.month_branch != expected_blade:
        return False
    # F3: 天干透官或杀
    if not ('qi_sha' in bazi.stem_array or 'zheng_guan' in bazi.stem_array):
        return False
    return True
```

---

## 二、B类：食伤系 (Output Systems)

### B-01 食神格 (Eating God)

**核心逻辑**：月令食神，喜见财，忌枭夺。

```python
def filter_B01(bazi):
    # F1: 月令主气食神
    if bazi.month_branch_main_energy != 'shi_shen':
        return False
    # F2: 天干见财（正财或偏财）
    has_wealth = ('zheng_cai' in bazi.stem_array or 
                  'pian_cai' in bazi.stem_array)
    if not has_wealth:
        return False
    # F3: 若见枭（偏印），必须见偏财制之
    if 'pian_yin' in bazi.stem_array:
        if 'pian_cai' not in bazi.stem_array:
            return False  # 枭神夺食，无制则剔除
    return True
```

---

### B-02 伤官格 (Hurting Officer)

**核心逻辑**：月令伤官，忌见官，喜佩印或生财。

```python
def filter_B02(bazi):
    # F1: 月令主气伤官
    if bazi.month_branch_main_energy != 'shang_guan':
        return False
    # F2: 天干透伤官
    if 'shang_guan' not in bazi.stem_array:
        return False
    # F3: 若见正官，需有印星护（否则剔除）
    if 'zheng_guan' in bazi.stem_array:
        if 'zheng_yin' not in bazi.stem_array:
            return False  # 伤官见官，大忌
    return True
```

---

## 三、C类：印枭系 (Resource Systems)

### C-01 正印格 (Direct Seal)

**核心逻辑**：月令正印，喜官杀生印，忌财破印。

```python
def filter_C01(bazi):
    # F1: 月令主气正印
    if bazi.month_branch_main_energy != 'zheng_yin':
        return False
    # F2: 天干透印
    if 'zheng_yin' not in bazi.stem_array:
        return False
    # F3: 财星不可过旺（正财+偏财 <= 2）
    wealth_count = bazi.stem_array.count('zheng_cai') + bazi.stem_array.count('pian_cai')
    if wealth_count > 2:
        return False  # 财多破印
    return True
```

---

### C-02 偏印格 (Indirect Seal)

**核心逻辑**：月令偏印，无食神则可用，有食神则需财制。

```python
def filter_C02(bazi):
    # F1: 月令主气偏印
    if bazi.month_branch_main_energy != 'pian_yin':
        return False
    # F2: 天干透偏印
    if 'pian_yin' not in bazi.stem_array:
        return False
    # F3: 若有食神，必须有偏财制枭
    if 'shi_shen' in bazi.stem_array:
        if 'pian_cai' not in bazi.stem_array:
            return False  # 枭神夺食，无制剔除
    return True
```

---

## 四、D类：财星系 (Wealth Systems)

### D-01 正财格 (Direct Wealth)

**核心逻辑**：月令正财，身强能任，忌比劫争财。

```python
def filter_D01(bazi):
    # F1: 月令主气正财
    if bazi.month_branch_main_energy != 'zheng_cai':
        return False
    # F2: 天干透财
    if 'zheng_cai' not in bazi.stem_array:
        return False
    # F3: 日主得令或得助（简化判断：有印或比劫助身）
    has_support = ('zheng_yin' in bazi.stem_array or 
                   'pian_yin' in bazi.stem_array or
                   'bi_jian' in bazi.stem_array)
    # F4: 比劫不可过旺
    if bazi.stem_array.count('bi_jian') + bazi.stem_array.count('jie_cai') > 2:
        return False  # 比劫争财
    return True
```

---

### D-02 偏财格 (Indirect Wealth)

**核心逻辑**：月令偏财，身强任财，忌比劫夺财。

```python
def filter_D02(bazi):
    # F1: 月令主气偏财
    if bazi.month_branch_main_energy != 'pian_cai':
        return False
    # F2: 天干透偏财
    if 'pian_cai' not in bazi.stem_array:
        return False
    # F3: 有官杀护财（制比劫）
    has_protection = ('zheng_guan' in bazi.stem_array or 
                      'qi_sha' in bazi.stem_array)
    # F4: 比劫不过旺
    if bazi.stem_array.count('bi_jian') + bazi.stem_array.count('jie_cai') > 2:
        if not has_protection:
            return False  # 比劫争财无制
    return True
```

---

## 五、海选执行规范

### 5.1 调用流程

```python
def census_pattern(pattern_id, universe_518k):
    """Step 2 海选主函数"""
    # 1. 从知识库调取过滤器
    filter_func = load_filter_from_lkv(pattern_id)
    
    # 2. 全库筛选
    matched = [sample for sample in universe_518k if filter_func(sample)]
    
    # 3. 输出结果
    return {
        "pattern_id": pattern_id,
        "matched_count": len(matched),
        "samples": matched
    }
```

### 5.2 输出规范

- 输出文件：`results/{pattern_id}_census.matched.json`
- 必须记录：`N_hit`（命中数）、`abundance`（丰度 = N_hit / 518400）
- 禁止包含：任何 5D 张量数据

---

## 六、注入协议

- **分片 ID**: `PROT_CLASSICAL_CENSUS_{PATTERN_ID}`
- **元数据**: `{"layer": "census", "logic_type": "boolean", "tensor_free": true}`
