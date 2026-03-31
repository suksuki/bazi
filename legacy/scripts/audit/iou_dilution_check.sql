-- FDS V5.5 Step 7.2：新格局接入后，全量格局丰度对比（稀释坍缩检查）
-- 执行时机：每增加一个新格局后运行，对比本次与上次 baseline 各格局 n 与 mean 变化
-- 此处仅输出当前各格局 COUNT 与五维均值，与 audit_logs/v2_0_physics_baseline.json 对比

SELECT
  pattern_id,
  COUNT(*) AS n,
  AVG(E) AS mean_E, AVG(O) AS mean_O, AVG(M) AS mean_M, AVG(S) AS mean_S, AVG(R) AS mean_R
FROM pattern_points
GROUP BY pattern_id
ORDER BY pattern_id;
