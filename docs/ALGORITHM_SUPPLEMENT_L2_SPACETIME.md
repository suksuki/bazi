# Antigravity L2 补充文档：时空相对论 (Spacetime Relativity)
**主题**: 多维场域叠加逻辑
**版本**: V3.0 (The Environmental Field)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`
**状态**: ACTIVE (Logic Standard)

---

## 1. 宏观场 (Macro-Field)
* **定义**: 时代的背景辐射 (Background Radiation)。
* **逻辑**: 个体命运受当前历元（如三元九运）的主气影响。
    * 顺应时代主气的五行获得 **共振加成 (Resonance Bonus)**。
    * 背离时代主气的五行受到 **阻尼抑制 (Damping)**。
    * *注：具体加成系数由 `@config.spacetime.macro_bonus` 定义。*

---

## 2. 中观场 (Meso-Field)
* **定义**: 地理环境对物理常数的修正。
* **逻辑**: 
    * **纬度修正**: 根据 `@config.spacetime.latitude_coefficients` 修正水火既济的平衡点。
    * **半球修正**: 南北半球的季节（月令）定义相反，由 `@config.spacetime.invert_seasons` 开关控制。

---

## 3. 微观场 (Micro-Field)
* **定义**: 观察者的相对时空坐标。
* **逻辑**: 
    * **真太阳时**: 所有排盘计算必须基于太阳过顶时间。
    * **时差校准**: 经度差异直接转化为时间偏移量，公式参数引用 `@config.spacetime.solar_time_correction`。
