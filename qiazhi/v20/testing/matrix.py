from __future__ import annotations

TEST_COVERAGE_AREAS = (
    {
        "area": "runtime_feature_spine",
        "tests": ("v20/tests/test_v20_runtime.py",),
        "contracts": ("ChartFacts", "CoreInference", "BaziFeature", "AnswerPlan"),
        "tier": "fast",
    },
    {
        "area": "explicit_time_layer",
        "tests": ("v20/tests/test_v20_runtime.py", "v20/tests/test_v20_server.py"),
        "contracts": ("TimeContext", "feature.time.explicit_context", "q_time_layer_context"),
        "tier": "fast",
    },
    {
        "area": "knowledge_llm_i18n",
        "tests": ("v20/tests/test_v20_runtime.py", "v20/tests/test_v20_question_ranking.py"),
        "contracts": ("KnowledgeRef", "llm_assist", "deterministic_i18n_terms", "QuestionRankingPolicy"),
        "tier": "fast",
    },
    {
        "area": "access_roles",
        "tests": ("v20/tests/test_v20_access.py",),
        "contracts": ("AccessRolePolicy", "role_runtime_view"),
        "tier": "fast",
    },
    {
        "area": "ops_storage_redis",
        "tests": ("v20/tests/test_v20_ops.py", "v20/tests/test_v20_storage.py", "v20/tests/test_v20_redis.py"),
        "contracts": ("RuntimeConfig", "Postgres schema", "Redis keyspaces", "dependency_readiness"),
        "tier": "fast",
    },
    {
        "area": "corpus_learning_validation",
        "tests": (
            "v20/tests/test_v20_learning_corpus.py",
            "v20/tests/test_v20_feedback_learning.py",
            "v20/tests/test_v20_runtime.py",
        ),
        "contracts": ("518400 coverage plan", "SyntheticSuite", "EvolutionDryRunPlan", "FeedbackLedger"),
        "tier": "fast",
    },
    {
        "area": "ui_static_shell",
        "tests": ("v20/tests/test_v20_ui.py",),
        "contracts": ("v20/frontend", "/v20/ui/"),
        "tier": "fast",
    },
)


def build_test_coverage_matrix() -> dict[str, object]:
    return {
        "version": "v20.test_coverage_matrix.v1",
        "area_count": len(TEST_COVERAGE_AREAS),
        "areas": list(TEST_COVERAGE_AREAS),
        "default_tier": "fast",
        "runtime_mutation": False,
        "guardrails": [
            "COVERAGE_MATRIX_IS_DOCUMENTATION_AND_AUDIT",
            "NO_ADDITIONAL_TEST_RUNTIME",
            "FAST_TIER_REMAINS_DEFAULT",
        ],
    }
