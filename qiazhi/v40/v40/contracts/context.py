from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from v40.contracts.base import ClientKey, EngineKey, EngineMode, LocaleKey, RoleKey, Topic, V40Model


class LocaleContext(V40Model):
    version: str = "v40.locale_context.v1"
    locale: LocaleKey = "zh-CN"
    fallback_locale: LocaleKey = "zh-CN"
    user_language: str = "zh-CN"
    output_language: str = "zh-CN"
    terminology_style: Literal["plain", "professional", "mixed"] = "mixed"
    tone: Literal["concise", "consultative", "gentle", "professional"] = "consultative"
    boundary: str = "locale_context_drives_projection_and_expression_not_frontend_translation"


class MingliTermEntry(V40Model):
    version: str = "v40.mingli_term_entry.v1"
    canonical_key: str
    zh_cn: str
    en_us: str
    ko_kr: str
    plain_zh: str = ""
    boundary: str = "mingli_term_entry_keeps_internal_logic_on_canonical_keys"

    @model_validator(mode="after")
    def _term_boundary(self) -> "MingliTermEntry":
        if not self.canonical_key.strip():
            raise ValueError("MingliTermEntry requires canonical_key")
        if not all([self.zh_cn.strip(), self.en_us.strip(), self.ko_kr.strip()]):
            raise ValueError("MingliTermEntry requires zh/en/ko labels")
        return self


class MingliTermDictionary(V40Model):
    version: str = "v40.mingli_term_dictionary.v1"
    dictionary_id: str = "mingli_terms.v1"
    entries: list[MingliTermEntry] = Field(default_factory=list)
    default_locale: LocaleKey = "zh-CN"
    boundary: str = "mingli_term_dictionary_localizes_terms_without_changing_canonical_claim_keys"

    @model_validator(mode="after")
    def _dictionary_boundary(self) -> "MingliTermDictionary":
        keys = [entry.canonical_key for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("MingliTermDictionary requires unique canonical_key")
        return self


class RoleContext(V40Model):
    version: str = "v40.role_context.v1"
    role: RoleKey = "user"
    permissions: list[str] = Field(default_factory=list)
    can_view_evidence: bool = False
    can_view_branch_detail: bool = False
    can_submit_calibration: bool = False
    can_view_debug: bool = False
    can_create_training_label: bool = False
    boundary: str = "role_context_controls_projection_permissions_not_ui_button_hiding"

    @model_validator(mode="after")
    def _role_permissions(self) -> "RoleContext":
        if self.role == "guest" and any(
            [self.can_view_branch_detail, self.can_submit_calibration, self.can_view_debug, self.can_create_training_label]
        ):
            raise ValueError("guest RoleContext cannot access practitioner/admin capabilities")
        if self.role == "user" and (self.can_submit_calibration or self.can_view_debug):
            raise ValueError("user RoleContext cannot submit calibration or view debug")
        if self.role == "practitioner" and self.can_view_debug:
            raise ValueError("practitioner RoleContext cannot view admin debug")
        return self


class UserAppSessionContext(V40Model):
    version: str = "v40.user_app_session_context.v1"
    session_id: str = "local-user-app-session"
    role_key: RoleKey = "user"
    role_context: RoleContext = Field(default_factory=RoleContext)
    authenticated: bool = False
    source: str = "default:user_app"
    admin_mapped_to_practitioner: bool = False
    allowed_user_app_roles: list[RoleKey] = Field(default_factory=lambda: ["guest", "user", "practitioner"])
    admin_control_plane_separated: bool = True
    boundary: str = "user_app_session_context_derives_role_server_side_without_granting_admin_control"

    @model_validator(mode="after")
    def _session_boundary(self) -> "UserAppSessionContext":
        if self.role_key not in {"guest", "user", "practitioner"}:
            raise ValueError("User app session role must be guest, user, or practitioner")
        if self.role_context.role != self.role_key:
            raise ValueError("User app session role_context must match role_key")
        if "admin" in self.allowed_user_app_roles:
            raise ValueError("Admin is not a user app role")
        if not self.admin_control_plane_separated:
            raise ValueError("User app session cannot merge Admin control plane")
        return self


class ClientContext(V40Model):
    version: str = "v40.client_context.v1"
    client: ClientKey = "web"
    device_type: Literal["desktop", "tablet", "mobile"] = "desktop"
    viewport: Literal["wide", "medium", "narrow"] = "wide"
    interaction_mode: Literal["keyboard_mouse", "touch", "mixed"] = "keyboard_mouse"
    supports_side_panel: bool = True
    supports_drawer: bool = True
    prefers_compact_cards: bool = False
    boundary: str = "client_context_changes_density_and_layout_not_mingli_verdict"

    @model_validator(mode="after")
    def _client_density(self) -> "ClientContext":
        if self.device_type == "mobile" and self.supports_side_panel:
            raise ValueError("mobile ClientContext cannot require side panel")
        if self.device_type == "mobile" and self.viewport != "narrow":
            raise ValueError("mobile ClientContext requires narrow viewport")
        return self


class EngineCapability(V40Model):
    version: str = "v40.engine_capability.v1"
    engine: EngineKey
    can_emit_facts: bool = False
    can_emit_signals: bool = False
    can_emit_probe_candidates: bool = False
    can_emit_training_labels: bool = False
    supported_domains: list[Topic] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    default_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    max_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    can_directly_generate_verdict: bool = False
    boundary: str = "engine_capability_declares_material_outputs_not_verdict_authority"

    @model_validator(mode="after")
    def _capability_boundary(self) -> "EngineCapability":
        if self.can_directly_generate_verdict:
            raise ValueError("EngineCapability cannot directly generate verdict")
        if self.default_weight > self.max_weight:
            raise ValueError("EngineCapability default_weight cannot exceed max_weight")
        if self.engine == EngineKey.ZIWEI and self.max_weight > 0.15:
            raise ValueError("Ziwei EngineCapability max_weight must remain sidecar")
        return self


class EngineContext(V40Model):
    version: str = "v40.engine_context.v1"
    enabled_engines: list[EngineKey] = Field(default_factory=lambda: [EngineKey.BAZI])
    requested_engines: list[EngineKey] = Field(default_factory=list)
    unavailable_engines: list[EngineKey] = Field(default_factory=list)
    engine_plan_id: str = ""
    engine_policy_version: str = "baseline"
    engine_weights: dict[EngineKey, float] = Field(default_factory=lambda: {EngineKey.BAZI: 1.0})
    engine_run_modes: dict[EngineKey, EngineMode] = Field(default_factory=lambda: {EngineKey.BAZI: EngineMode.SIGNAL_SIDECAR})
    capabilities: list[EngineCapability] = Field(default_factory=list)
    boundary: str = "engine_context_schedules_engines_through_capabilities_without_direct_verdict"

    @model_validator(mode="after")
    def _engine_context_boundary(self) -> "EngineContext":
        if EngineKey.BAZI not in self.enabled_engines:
            raise ValueError("EngineContext requires Bazi engine")
        for engine, weight in self.engine_weights.items():
            if weight < 0 or weight > 1:
                raise ValueError(f"EngineContext invalid weight for {engine}")
        if self.engine_weights.get(EngineKey.ZIWEI, 0.0) > 0.15:
            raise ValueError("Ziwei engine weight must remain sidecar")
        return self


class RuntimeContext(V40Model):
    version: str = "v40.runtime_context.v1"
    locale_context: LocaleContext = Field(default_factory=LocaleContext)
    role_context: RoleContext = Field(default_factory=RoleContext)
    client_context: ClientContext = Field(default_factory=ClientContext)
    engine_context: EngineContext = Field(default_factory=EngineContext)
    training_context: dict[str, object] = Field(default_factory=dict)
    boundary: str = "runtime_context_carries_locale_role_client_engine_and_training_dimensions"


def default_role_context(role: RoleKey) -> RoleContext:
    if role == "practitioner":
        return RoleContext(
            role=role,
            permissions=["view_evidence", "view_branch_detail", "submit_calibration", "create_training_label"],
            can_view_evidence=True,
            can_view_branch_detail=True,
            can_submit_calibration=True,
            can_create_training_label=True,
        )
    if role == "admin":
        return RoleContext(
            role=role,
            permissions=["view_evidence", "view_branch_detail", "view_debug", "create_training_label"],
            can_view_evidence=True,
            can_view_branch_detail=True,
            can_view_debug=True,
            can_create_training_label=True,
        )
    if role == "guest":
        return RoleContext(role=role, permissions=["light_feedback"])
    return RoleContext(role=role, permissions=["report", "conversation", "feedback"], can_create_training_label=True)


def default_client_context(client: ClientKey) -> ClientContext:
    if client == "mobile":
        return ClientContext(
            client=client,
            device_type="mobile",
            viewport="narrow",
            interaction_mode="touch",
            supports_side_panel=False,
            supports_drawer=True,
            prefers_compact_cards=True,
        )
    if client == "tablet":
        return ClientContext(client=client, device_type="tablet", viewport="medium", interaction_mode="touch")
    return ClientContext(client=client, device_type="desktop", viewport="wide", interaction_mode="keyboard_mouse")


def default_locale_context(locale: LocaleKey) -> LocaleContext:
    resolved = _normalize_locale(locale)
    return LocaleContext(locale=resolved, user_language=resolved, output_language=resolved)


def _normalize_locale(locale: LocaleKey) -> LocaleKey:
    aliases: dict[str, LocaleKey] = {
        "zh": "zh-CN",
        "en": "en-US",
        "ko": "ko-KR",
    }
    return aliases.get(str(locale), locale)
