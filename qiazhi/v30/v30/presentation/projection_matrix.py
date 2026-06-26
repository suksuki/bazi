from __future__ import annotations

from v30.contracts import ClientKey, CoreRuntimeResult, LocaleKey, RoleKey
from v30.presentation.client_model import build_presentation_model
from v30.presentation.client_profiles import CLIENT_PROFILES


PROJECTION_MATRIX_VERSION = "v30.role_locale_client_projection_matrix.v1"
ROLE_KEYS: tuple[RoleKey, ...] = ("guest", "user", "practitioner", "analyst", "admin", "lab")
LOCALE_KEYS: tuple[LocaleKey, ...] = ("zh", "en", "ko")
CLIENT_KEYS: tuple[ClientKey, ...] = ("web", "mobile", "admin", "lab")
DEFAULT_SMOKE_COMBINATIONS: tuple[tuple[RoleKey, LocaleKey, ClientKey], ...] = (
    ("guest", "zh", "mobile"),
    ("user", "zh", "web"),
    ("practitioner", "zh", "web"),
    ("analyst", "en", "admin"),
    ("admin", "en", "admin"),
    ("lab", "ko", "lab"),
)


def build_role_locale_client_projection_matrix(runtime: CoreRuntimeResult) -> dict[str, object]:
    samples = [
        _sample_projection(runtime, role_key=role_key, locale=locale, client=client)
        for role_key, locale, client in DEFAULT_SMOKE_COMBINATIONS
    ]
    return {
        "version": PROJECTION_MATRIX_VERSION,
        "roles": list(ROLE_KEYS),
        "locales": list(LOCALE_KEYS),
        "clients": list(CLIENT_KEYS),
        "combination_count": len(ROLE_KEYS) * len(LOCALE_KEYS) * len(CLIENT_KEYS),
        "client_profiles": {
            key: profile.model_dump(mode="json")
            for key, profile in CLIENT_PROFILES.items()
        },
        "sampled_combinations": samples,
        "sampled_combination_count": len(samples),
        "sampled_roles": sorted({str(row["role_key"]) for row in samples}),
        "sampled_locales": sorted({str(row["locale"]) for row in samples}),
        "sampled_clients": sorted({str(row["client"]) for row in samples}),
        "diagnostic_roles": sorted({
            str(row["role_key"]) for row in samples if bool(row.get("diagnostics_visible"))
        }),
        "compact_clients": sorted({
            str(row["client"]) for row in samples if row.get("density") == "compact"
        }),
        "boundary": "role_locale_client_projection_changes_visibility_language_density_not_chart_fact",
    }


def _sample_projection(
    runtime: CoreRuntimeResult,
    *,
    role_key: RoleKey,
    locale: LocaleKey,
    client: ClientKey,
) -> dict[str, object]:
    payload = build_presentation_model(
        runtime,
        role_key=role_key,
        locale=locale,
        client=client,
    ).model_dump(mode="json")
    questions = payload.get("questions", [])
    return {
        "role_key": payload.get("role_key"),
        "locale": payload.get("locale"),
        "client": payload.get("client"),
        "density": payload.get("layout", {}).get("density"),
        "question_count": len(questions) if isinstance(questions, list) else 0,
        "diagnostics_visible": bool(payload.get("diagnostics")),
        "actions": [
            str(row.get("type"))
            for row in payload.get("actions", [])
            if isinstance(row, dict)
        ],
        "label_fallback_count": payload.get("layout", {})
        .get("rendered_question_label_summary", {})
        .get("fallback_count", 0),
        "boundary": "projection_sample_is_presentation_contract_not_chart_fact",
    }
