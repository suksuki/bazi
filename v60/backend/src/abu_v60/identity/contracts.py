from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class AccountView(BaseModel):
    account_ref: str
    email: str
    display_name: str
    account_role: str


class ProfileView(BaseModel):
    profile_ref: str
    display_name: str
    gender: str
    calendar_type: str
    birth_date: date
    birth_time: time
    birth_location: str
    timezone: str


class SessionView(BaseModel):
    account: AccountView
    profiles: list[ProfileView]
