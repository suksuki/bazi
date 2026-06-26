from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model


PORTRAIT_PROJECTION_VERSION = "v30.portrait.macro_projection.v1"
PORTRAIT_PROJECTION_VIEW_VERSION = "v30.portrait.macro_projection_view.v1"
DIAGNOSTIC_ROLES = {"admin", "analyst", "lab", "practitioner"}
USER_VISIBLE_ROLES = {"guest", "user"}
GUEST_VISIBLE_DOMAINS = {"foundation", "wealth", "career", "relationship", "romance", "health"}


class MacroPortraitProjection(V30Model):
    projection_id: str
    version: str = PORTRAIT_PROJECTION_VERSION
    source_signal_id: str
    domain: str
    label_zh: str
    portrait_dimensions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    matched_evidence_domains: list[str] = Field(default_factory=list)
    confidence: float
    boundaries: list[str] = Field(default_factory=list)
    source_policy: str = "portrait_is_projection_not_fact_source"


class MacroPortraitProjectionView(V30Model):
    view_id: str
    version: str = PORTRAIT_PROJECTION_VIEW_VERSION
    projection_id: str
    source_signal_id: str
    domain: str
    label_zh: str
    role_key: str
    client: str
    visibility: str
    density: str
    summary: str
    portrait_dimensions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    matched_evidence_domains: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    display_tags: list[str] = Field(default_factory=list)
    confidence: float
    source_policy: str = "portrait_is_projection_not_fact_source"


def build_macro_portrait_projections(
    macro_dimension_signals: list[dict[str, object]],
) -> list[MacroPortraitProjection]:
    rows: list[MacroPortraitProjection] = []
    for signal in macro_dimension_signals:
        dimensions = _string_list(signal.get("portrait_dimensions", []))
        evidence_ids = _string_list(signal.get("evidence_ids", []))
        if not dimensions or not evidence_ids:
            continue
        domain = str(signal.get("domain", ""))
        rows.append(
            MacroPortraitProjection(
                projection_id=f"v30.portrait.macro.{domain}",
                source_signal_id=str(signal.get("signal_id", "")),
                domain=domain,
                label_zh=str(signal.get("label_zh", "")),
                portrait_dimensions=dimensions,
                evidence_ids=evidence_ids,
                matched_evidence_domains=_string_list(signal.get("matched_evidence_domains", [])),
                confidence=round(min(0.98, float(signal.get("score", 0.0)) * 0.92), 3),
                boundaries=_string_list(signal.get("boundaries", [])),
            )
        )
    return sorted(rows, key=lambda row: (-row.confidence, row.domain))


def build_macro_portrait_projection_views(
    projections: list[MacroPortraitProjection | dict[str, object]],
    *,
    role_key: str = "user",
    client: str = "web",
) -> list[MacroPortraitProjectionView]:
    normalized = [
        row if isinstance(row, MacroPortraitProjection) else MacroPortraitProjection.model_validate(row)
        for row in projections
        if isinstance(row, (MacroPortraitProjection, dict))
    ]
    diagnostic = role_key in DIAGNOSTIC_ROLES
    rows: list[MacroPortraitProjectionView] = []
    for projection in normalized:
        if role_key == "guest" and projection.domain not in GUEST_VISIBLE_DOMAINS:
            continue
        visibility = "diagnostic" if diagnostic else "user_visible"
        if projection.domain == "hidden_factor" and not diagnostic:
            visibility = "boundary_visible"
        density = "diagnostic" if diagnostic else ("compact" if client == "mobile" else "standard")
        rows.append(
            MacroPortraitProjectionView(
                view_id=f"{projection.projection_id}:view:{role_key}:{client}",
                projection_id=projection.projection_id,
                source_signal_id=projection.source_signal_id,
                domain=projection.domain,
                label_zh=projection.label_zh,
                role_key=role_key,
                client=client,
                visibility=visibility,
                density=density,
                summary=_projection_view_summary(projection, role_key=role_key, diagnostic=diagnostic),
                portrait_dimensions=projection.portrait_dimensions,
                evidence_ids=projection.evidence_ids,
                matched_evidence_domains=projection.matched_evidence_domains,
                boundaries=[
                    *projection.boundaries,
                    "portrait_projection_view_is_role_filtered_not_chart_fact",
                ],
                display_tags=_display_tags(projection, role_key=role_key, client=client, diagnostic=diagnostic),
                confidence=projection.confidence,
                source_policy=projection.source_policy,
            )
        )
    return sorted(rows, key=lambda row: (-row.confidence, row.domain, row.role_key, row.client))


def summarize_macro_portrait_projections(projections: list[MacroPortraitProjection]) -> dict[str, object]:
    return {
        "version": PORTRAIT_PROJECTION_VERSION,
        "projection_count": len(projections),
        "domains": sorted({row.domain for row in projections}),
        "portrait_dimensions": sorted({dimension for row in projections for dimension in row.portrait_dimensions}),
        "boundary_count": sum(len(row.boundaries) for row in projections),
        "source_policy": "portrait_is_projection_not_fact_source",
    }


def summarize_macro_portrait_projection_views(
    views: list[MacroPortraitProjectionView | dict[str, object]],
) -> dict[str, object]:
    normalized = [
        row if isinstance(row, MacroPortraitProjectionView) else MacroPortraitProjectionView.model_validate(row)
        for row in views
        if isinstance(row, (MacroPortraitProjectionView, dict))
    ]
    return {
        "version": PORTRAIT_PROJECTION_VIEW_VERSION,
        "view_count": len(normalized),
        "projection_count": len({row.projection_id for row in normalized}),
        "domains": sorted({row.domain for row in normalized}),
        "roles": sorted({row.role_key for row in normalized}),
        "clients": sorted({row.client for row in normalized}),
        "visibility": sorted({row.visibility for row in normalized}),
        "density": sorted({row.density for row in normalized}),
        "hidden_factor_view_count": sum(1 for row in normalized if row.domain == "hidden_factor"),
        "boundary_count": sum(len(row.boundaries) for row in normalized),
        "source_policy": "portrait_is_projection_not_fact_source",
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if str(row)]


def _projection_view_summary(
    projection: MacroPortraitProjection,
    *,
    role_key: str,
    diagnostic: bool,
) -> str:
    if diagnostic:
        dimensions = ",".join(projection.portrait_dimensions[:4])
        return (
            f"{projection.domain}:{projection.confidence:.3f}; "
            f"dimensions={dimensions}; policy={projection.source_policy}"
        )
    if projection.domain == "hidden_factor":
        return "隐藏放大因子只作为反馈约束下的画像线索，用来辅助追问，不能当成命盘事实。"
    label = projection.label_zh or projection.domain
    return f"{label}画像只作为证据投射，用来组织表达和追问，不替代原局事实。"


def _display_tags(
    projection: MacroPortraitProjection,
    *,
    role_key: str,
    client: str,
    diagnostic: bool,
) -> list[str]:
    tags = ["role_filtered", f"role:{role_key}", f"client:{client}", f"visibility:{'diagnostic' if diagnostic else 'bounded'}"]
    tags.extend(f"dimension:{dimension}" for dimension in projection.portrait_dimensions[:3])
    return tags
