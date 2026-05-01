from __future__ import annotations

from v20.testing.schema import TestCommand, TestTier


TEST_TIERS: tuple[TestTier, ...] = (
    TestTier(
        name="smoke",
        purpose="Sub-second to few-second contract check for syntax, runtime spine, and ops profile health.",
        budget_seconds=8,
        default_for=("small_python_edit", "doc_adjacent_code_edit", "pre_commit_first_pass"),
        commands=(
            TestCommand(
                name="py_compile_v20",
                argv=("__PYTHON_BIN__", "-m", "py_compile", "__V20_PY_FILES__"),
                purpose="Compile V20 Python files only.",
            ),
            TestCommand(
                name="runtime_spine_smoke",
                argv=(
                    "__PYTHON_BIN__",
                    "-m",
                    "pytest",
                    "-q",
                    "v20/tests/test_v20_runtime.py::test_v20_runtime_builds_feature_spine_answer_plan",
                    "v20/tests/test_v20_ops.py::test_v20_ops_profiles_cover_macos_linux_postgres_and_redis",
                ),
                purpose="Check the deterministic Bazi measurement spine and runtime profiles.",
            ),
        ),
    ),
    TestTier(
        name="fast",
        purpose="Default V20 developer loop; all current unit-contract tests, no services, no network.",
        budget_seconds=20,
        default_for=("normal_code_edit", "feature_spine_edit", "ops_config_edit", "llm_contract_edit"),
        commands=(
            TestCommand(
                name="py_compile_v20",
                argv=("__PYTHON_BIN__", "-m", "py_compile", "__V20_PY_FILES__"),
                purpose="Compile V20 Python files only.",
            ),
            TestCommand(
                name="pytest_v20_unit_contracts",
                argv=("__PYTHON_BIN__", "-m", "pytest", "-q", "v20/tests"),
                purpose="Run V20 unit and contract tests.",
            ),
        ),
    ),
    TestTier(
        name="targeted",
        purpose="Run selected V20 tests by pytest expression or explicit paths.",
        budget_seconds=45,
        default_for=("focused_bugfix", "module_specific_refactor", "mainline_target_check"),
        commands=(
            TestCommand(
                name="pytest_v20_targeted",
                argv=("__PYTHON_BIN__", "-m", "pytest", "-q", "v20/tests", "__PYTEST_ARGS__"),
                purpose="Run explicit pytest selectors without expanding to slow suites.",
            ),
        ),
    ),
    TestTier(
        name="full",
        purpose="All V20 non-service tests. This remains bounded and excludes opt-in integration suites.",
        budget_seconds=90,
        default_for=("phase_closeout", "cross_module_refactor", "before_commit"),
        commands=(
            TestCommand(
                name="py_compile_v20",
                argv=("__PYTHON_BIN__", "-m", "py_compile", "__V20_PY_FILES__"),
                purpose="Compile V20 Python files only.",
            ),
            TestCommand(
                name="pytest_v20_all_local",
                argv=("__PYTHON_BIN__", "-m", "pytest", "-q", "v20/tests"),
                purpose="Run all local V20 tests.",
            ),
            TestCommand(
                name="git_diff_check",
                argv=("git", "diff", "--check"),
                purpose="Catch whitespace and conflict marker issues.",
            ),
        ),
    ),
    TestTier(
        name="services",
        purpose="Explicit opt-in checks for Postgres, Redis, Linux/macOS sync, and server health.",
        budget_seconds=180,
        default_for=("database_migration", "redis_queue_change", "deploy_or_sync_change"),
        commands=(
            TestCommand(
                name="pytest_v20_services",
                argv=("__PYTHON_BIN__", "-m", "pytest", "-q", "v20/tests", "-k", "service or postgres or redis or sync"),
                purpose="Service-dependent tests; skipped unless the env gate is set.",
                opt_in_env="RUN_V20_SERVICE_TESTS",
            ),
        ),
        guardrails=(
            "TEST_TIER_IS_EXPLICIT",
            "SERVICE_TESTS_REQUIRE_OPT_IN",
            "NO_SECRET_VALUES_IN_TEST_OUTPUT",
            "NO_PRODUCTION_DATA_MUTATION",
        ),
    ),
    TestTier(
        name="corpus",
        purpose="Explicit opt-in synthetic corpus and full 518K coverage jobs.",
        budget_seconds=3600,
        default_for=("corpus_precompute", "learning_dataset_generation", "coverage_report"),
        commands=(
            TestCommand(
                name="pytest_v20_corpus",
                argv=("__PYTHON_BIN__", "-m", "pytest", "-q", "v20/tests", "-k", "corpus or coverage or full_518k"),
                purpose="Long-running corpus tests; never part of default loops.",
                opt_in_env="RUN_V20_CORPUS_TESTS",
            ),
        ),
        guardrails=(
            "TEST_TIER_IS_EXPLICIT",
            "CORPUS_TESTS_REQUIRE_OPT_IN",
            "LONG_JOBS_WRITE_RUN_LEDGER",
            "NO_RUNTIME_RULE_MUTATION",
        ),
    ),
)


def get_tier(name: str) -> TestTier:
    for tier in TEST_TIERS:
        if tier.name == name:
            return tier
    raise KeyError(name)


def test_tier_manifest() -> dict[str, object]:
    return {
        "version": "v20.test_tier_manifest.v1",
        "tiers": [tier.to_dict() for tier in TEST_TIERS],
        "default_tier": "fast",
        "fast_budget_seconds": get_tier("fast").budget_seconds,
        "guardrails": [
            "FAST_TESTS_STAY_LOCAL_AND_BOUNDED",
            "SERVICE_AND_CORPUS_TESTS_REQUIRE_OPT_IN",
            "MARKDOWN_DOCS_MIRROR_EXECUTABLE_MANIFEST",
        ],
    }
