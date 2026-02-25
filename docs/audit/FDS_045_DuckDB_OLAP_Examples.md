# 第 045 号 DuckDB 秒级审计 SQL 示例 (OLAP 专项)

FDS 2.0 特征层表：`pattern_points`（`core/database/fds_physics.duckdb`）

**列说明**：`pattern_id`, `ref`, `line_index`, `E`, `O`, `M`, `S`, `R`（五维顺序 E/O/M/S/R）

---

## 1. 身强财弱且见劫财（A-04 正财格物理坍缩）

**审计场景**：正财格中 M 轴低分位（财富弱）、E 轴极高（身强），易形成「身强财弱」或见劫财夺财的物理坍缩样本。

```sql
-- 在 DuckDB CLI 或 Python duckdb 中执行前，请先 ATTACH 数据库
-- Python: conn = duckdb.connect("core/database/fds_physics.duckdb")

SELECT ref, line_index, E, O, M, S, R
FROM pattern_points
WHERE pattern_id = 'A-04'
  AND M < -1.0
  AND E > 1.2
ORDER BY M ASC, E DESC
LIMIT 10;
```

**预期性能**：百毫秒级返回（518k 量级下，有索引 `idx_pp_pattern`）。

---

## 2. 按格局全量分布统计（生成 2.0 基线）

```sql
SELECT
  pattern_id,
  COUNT(*) AS n,
  AVG(E) AS mean_E, AVG(O) AS mean_O, AVG(M) AS mean_M, AVG(S) AS mean_S, AVG(R) AS mean_R,
  STDDEV(E) AS std_E, STDDEV(M) AS std_M, STDDEV(S) AS std_S
FROM pattern_points
GROUP BY pattern_id
ORDER BY pattern_id;
```

---

## 3. A-07 伤官格 S 轴高应力样本（伤官见官风险带）

```sql
SELECT ref, E, O, M, S, R
FROM pattern_points
WHERE pattern_id = 'A-07' AND S >= 1.5
ORDER BY S DESC
LIMIT 20;
```

---

## 4. A-10 阳刃格 E/S 双高「刀尖」样本

```sql
SELECT ref, E, O, M, S, R
FROM pattern_points
WHERE pattern_id = 'A-10' AND E > 1.5 AND S > 1.5
ORDER BY S DESC, E DESC
LIMIT 20;
```

---

*说明：表中无 `dominant_pattern` 字段，每行已由 `pattern_id` 限定格局；多格局叠加态需在应用层对撞后再查对应格局表。*
