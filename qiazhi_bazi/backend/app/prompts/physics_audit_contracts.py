"""物理审计 JSON 契约行（无 skills 依赖，供 Registry / prompts 包安全 import）。"""

AUDIT_JSON_SCHEMA_LINE = (
    '{"diagnosis":"","alignment_score":0,"top_anomaly":"","causal_reasoning":"",'
    '"tuning_suggestions":[""],"sql_patch":"","refresh_hint":"",'
    '"logic_proposal":{"title":"","param_key":"","suggested_value":0,"reason":"","expected_impact":"",'
    '"sql_patch":"","source_role":"LLM"}}'
)
