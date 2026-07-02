from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field, model_validator

from v40.contracts.base import RoleKey, V40Model
from v40.contracts.chart import BaziChartFacts, BirthInputCanonical, ZiweiChartFacts


class UserAccountPublic(V40Model):
    version: str = "v40.user_account_public.v1"
    user_id: str
    email: str
    display_name: str = ""
    role_key: RoleKey = "user"
    active: bool = True
    boundary: str = "user_account_public_exposes_user_app_identity_without_password_material"

    @model_validator(mode="after")
    def _public_role_boundary(self) -> "UserAccountPublic":
        if self.role_key not in {"user", "practitioner"}:
            raise ValueError("User app account role must be user or practitioner")
        if not self.user_id.strip():
            raise ValueError("UserAccountPublic requires user_id")
        if "@" not in self.email:
            raise ValueError("UserAccountPublic requires email")
        return self


class UserAccountInternal(UserAccountPublic):
    version: str = "v40.user_account_internal.v1"
    password_hash: str
    password_salt: str
    boundary: str = "user_account_internal_is_storage_only_and_never_returned_to_user_app"

    def public(self) -> UserAccountPublic:
        return UserAccountPublic(
            user_id=self.user_id,
            email=self.email,
            display_name=self.display_name,
            role_key=self.role_key,
            active=self.active,
        )


class UserSessionRecord(V40Model):
    version: str = "v40.user_session_record.v1"
    session_id: str
    user_id: str
    role_key: RoleKey = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    revoked: bool = False
    boundary: str = "user_session_record_scopes_user_app_state_without_admin_control"

    @model_validator(mode="after")
    def _session_boundary(self) -> "UserSessionRecord":
        if self.role_key not in {"user", "practitioner"}:
            raise ValueError("User app session role must be user or practitioner")
        if not self.session_id.strip():
            raise ValueError("UserSessionRecord requires session_id")
        if not self.user_id.strip():
            raise ValueError("UserSessionRecord requires user_id")
        return self


class BaziProfileRecord(V40Model):
    version: str = "v40.bazi_profile_record.v1"
    profile_id: str
    user_id: str
    display_name: str
    gender: str = ""
    chart_facts: BaziChartFacts
    birth_input: BirthInputCanonical | None = None
    ziwei_chart_facts: ZiweiChartFacts | None = None
    is_default: bool = False
    deleted: bool = False
    tags: list[str] = Field(default_factory=list)
    boundary: str = "bazi_profile_record_is_user_owned_input_material_not_trainable_policy"

    @model_validator(mode="after")
    def _profile_boundary(self) -> "BaziProfileRecord":
        if not self.profile_id.strip():
            raise ValueError("BaziProfileRecord requires profile_id")
        if not self.user_id.strip():
            raise ValueError("BaziProfileRecord requires user_id")
        if not self.display_name.strip():
            raise ValueError("BaziProfileRecord requires display_name")
        if self.chart_facts.gender and self.gender and self.chart_facts.gender != self.gender:
            raise ValueError("Bazi profile gender must match chart facts gender")
        return self

