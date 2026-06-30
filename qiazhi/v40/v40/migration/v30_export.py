from __future__ import annotations

from pydantic import Field, model_validator

from v40.contracts.base import V40Model


class V30ExportEnvelope(V40Model):
    """DTO boundary for V30 -> V40 migration.

    This module intentionally avoids runtime imports from the prior version. V30 must export plain JSON
    into this shape; V40 validates and converts it into native V40 contracts.
    """

    version: str = "v40.v30_export_envelope.v1"
    export_id: str
    source_version: str = "v30"
    reading_id: str
    exported_at: str = ""
    chart_facts: dict[str, object] = Field(default_factory=dict)
    feature_rows: list[dict[str, object]] = Field(default_factory=list)
    signal_rows: list[dict[str, object]] = Field(default_factory=list)
    verdict_rows: list[dict[str, object]] = Field(default_factory=list)
    advice_rows: list[dict[str, object]] = Field(default_factory=list)
    probe_rows: list[dict[str, object]] = Field(default_factory=list)
    product_projection_rows: list[dict[str, object]] = Field(default_factory=list)
    raw_runtime_path: str = ""
    raw_database_ref: str = ""
    raw_redis_key: str = ""
    boundary: str = "v30_export_envelope_accepts_plain_json_without_importing_or_mutating_v30_runtime"

    @model_validator(mode="after")
    def _export_boundary(self) -> "V30ExportEnvelope":
        if not self.export_id.strip():
            raise ValueError("V30ExportEnvelope requires export_id")
        if not self.reading_id.strip():
            raise ValueError("V30ExportEnvelope requires reading_id")
        if self.source_version != "v30":
            raise ValueError("V30ExportEnvelope source_version must be v30")
        if self.raw_runtime_path or self.raw_database_ref or self.raw_redis_key:
            raise ValueError("V40 migration importer cannot receive raw V30 runtime paths, DB refs, or Redis keys")
        return self


class V30ToV40MigrationPlan(V40Model):
    version: str = "v40.v30_to_v40_migration_plan.v1"
    plan_id: str
    export_id: str
    target_reading_id: str
    enabled_importers: list[str] = Field(default_factory=list)
    blocked_importers: list[str] = Field(default_factory=list)
    shadow_compare_only: bool = True
    writes_v30_state: bool = False
    writes_v40_production: bool = False
    boundary: str = "migration_plan_runs_shadow_compare_before_any_production_migration"

    @model_validator(mode="after")
    def _migration_plan_boundary(self) -> "V30ToV40MigrationPlan":
        if self.writes_v30_state:
            raise ValueError("V40 migration plan cannot write V30 state")
        if self.writes_v40_production:
            raise ValueError("V40 migration plan cannot write production before release gate")
        return self
