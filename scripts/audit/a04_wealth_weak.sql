-- A-04 正财格：身强财弱坍缩（M 低分位 + E 高）
-- 审计场景：禄劫破财、盲目冲刺型流形

SELECT ref, line_index, E, O, M, S, R
FROM pattern_points
WHERE pattern_id = 'A-04'
  AND M < -1.0
  AND E > 1.2
ORDER BY M ASC, E DESC
LIMIT 50;
