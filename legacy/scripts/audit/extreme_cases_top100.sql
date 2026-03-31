-- FDS V5.5 Step 6.1：极端异类点 Top100（按到质心欧氏距离）
-- 用法：将 'A-07' 替换为目标 pattern_id 后执行；或直接运行 python3 scripts/audit/extreme_cases_audit.py --pattern A-07
-- 输出：ref, line_index, E, O, M, S, R, d_to_centroid

WITH cen AS (
  SELECT AVG(E) AS e, AVG(O) AS o, AVG(M) AS m, AVG(S) AS s, AVG(R) AS r
  FROM pattern_points WHERE pattern_id = 'A-07'
)
SELECT p.ref, p.line_index, p.E, p.O, p.M, p.S, p.R,
  SQRT(POWER(p.E - c.e, 2) + POWER(p.O - c.o, 2) + POWER(p.M - c.m, 2) + POWER(p.S - c.s, 2) + POWER(p.R - c.r, 2)) AS d_to_centroid
FROM pattern_points p, cen c
WHERE p.pattern_id = 'A-07'
ORDER BY d_to_centroid DESC
LIMIT 100;
