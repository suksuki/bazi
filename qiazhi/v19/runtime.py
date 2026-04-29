from __future__ import annotations

import json
import getpass
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
SETTINGS_FILE = RUNTIME / "settings.json"
SESSIONS_FILE = RUNTIME / "sessions.json"
AUTH_SESSIONS_FILE = RUNTIME / "auth_sessions.json"
BAZI_PROFILES_FILE = RUNTIME / "bazi_profiles.json"
MASK = "********"
AUTH_ROLES = {"guest", "user", "practitioner", "admin"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_settings() -> Dict[str, Any]:
    return {
        "db": {
            "enabled": False,
            "backend": "postgres",
            "storage_backend": "file",
            "driver": "postgresql",
            "host": "127.0.0.1",
            "port": 5432,
            "database": "qiazhi_v19",
            "username": getpass.getuser() or "postgres",
            "password": "",
            "sslmode": "prefer",
            "url": "",
            "auto_migrate_json_to_postgres": False,
        },
        "llm": {
            "enabled": False,
            "execute_llm": True,
            "provider": "ollama",
            "host": "127.0.0.1",
            "port": 11434,
            "base_url": "",
            "username": "",
            "password": "",
            "api_key": "",
            "model": "qwen2.5:7b",
            "http_timeout_sec": 15,
            "fuse_wait_timeout_sec": 30,
            "temperature": 0.2,
            "max_tokens": 800,
            "audit_model": "",
            "audit_base_url": "",
            "audit_api_key": "",
        },
    }


def load_settings() -> Dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return default_settings()
    try:
        payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return default_settings()
    if not isinstance(payload, dict):
        return default_settings()
    settings = default_settings()
    settings["db"].update(dict(payload.get("db") or {}))
    settings["llm"].update(dict(payload.get("llm") or {}))
    return normalize_settings_payload(default_settings(), settings)


def save_settings(settings: Dict[str, Any]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def public_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    db = dict(settings.get("db") or {})
    llm = dict(settings.get("llm") or {})
    resolved_url = resolve_postgres_url(db)
    resolved_base_url = resolve_llm_base_url(llm)
    public = {
        "db": db,
        "llm": llm,
        "settings_path": str(SETTINGS_FILE),
        "runtime_dir": str(RUNTIME),
    }
    public["db"]["password"] = MASK if str(public["db"].get("password") or "") else ""
    public["db"]["url"] = mask_url(str(public["db"].get("url") or ""))
    public["db"]["resolved_url"] = mask_url(resolved_url)
    public["llm"]["password"] = MASK if str(public["llm"].get("password") or "") else ""
    public["llm"]["api_key"] = MASK if str(public["llm"].get("api_key") or "") else ""
    public["llm"]["audit_api_key"] = MASK if str(public["llm"].get("audit_api_key") or "") else ""
    public["llm"]["resolved_base_url"] = resolved_base_url
    return public


def normalize_settings_payload(current: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    base = default_settings()
    current_db = dict(base["db"])
    current_llm = dict(base["llm"])
    current_db.update(dict((current or {}).get("db") or {}))
    current_llm.update(dict((current or {}).get("llm") or {}))

    incoming_db = dict((incoming or {}).get("db") or {})
    incoming_llm = dict((incoming or {}).get("llm") or {})

    db = dict(current_db)
    llm = dict(current_llm)
    db.update(incoming_db)
    llm.update(incoming_llm)

    if _preserve_secret(incoming_db, "password"):
        db["password"] = str(current_db.get("password") or "")
    if "url" in incoming_db and MASK in str(incoming_db.get("url") or ""):
        db["url"] = str(current_db.get("url") or "")
    for secret_key in ("password", "api_key", "audit_api_key"):
        if _preserve_secret(incoming_llm, secret_key):
            llm[secret_key] = str(current_llm.get(secret_key) or "")

    normalized_db = {
        "enabled": bool(db.get("enabled")),
        "backend": _clean(db.get("backend"), "postgres"),
        "storage_backend": _clean(db.get("storage_backend"), "file"),
        "driver": _clean(db.get("driver"), "postgresql"),
        "host": _clean(db.get("host"), "127.0.0.1"),
        "port": _int(db.get("port"), 5432),
        "database": _clean(db.get("database"), "qiazhi_v19"),
        "username": _clean(db.get("username"), "postgres"),
        "password": str(db.get("password") or ""),
        "sslmode": _clean(db.get("sslmode"), "prefer"),
        "url": str(db.get("url") or "").strip(),
        "auto_migrate_json_to_postgres": bool(db.get("auto_migrate_json_to_postgres")),
    }
    normalized_llm = {
        "enabled": bool(llm.get("enabled")),
        "execute_llm": bool(llm.get("execute_llm", True)),
        "provider": _clean(llm.get("provider"), "ollama"),
        "host": _clean(llm.get("host"), "127.0.0.1"),
        "port": _int(llm.get("port"), 11434),
        "base_url": str(llm.get("base_url") or "").strip(),
        "username": str(llm.get("username") or "").strip(),
        "password": str(llm.get("password") or ""),
        "api_key": str(llm.get("api_key") or ""),
        "model": _clean(llm.get("model"), "qwen2.5:7b"),
        "http_timeout_sec": _clamp_float(llm.get("http_timeout_sec"), 15, 1, 600),
        "fuse_wait_timeout_sec": _clamp_float(llm.get("fuse_wait_timeout_sec"), 30, 1, 600),
        "temperature": _clamp_float(llm.get("temperature"), 0.2, 0, 2),
        "max_tokens": _int(llm.get("max_tokens"), 800),
        "audit_model": str(llm.get("audit_model") or "").strip(),
        "audit_base_url": str(llm.get("audit_base_url") or "").strip(),
        "audit_api_key": str(llm.get("audit_api_key") or ""),
    }
    return {"db": normalized_db, "llm": normalized_llm}


def resolve_postgres_url(db: Dict[str, Any]) -> str:
    url = str(db.get("url") or "").strip()
    if url:
        return url
    host = str(db.get("host") or "").strip()
    database = str(db.get("database") or "").strip()
    if not host or not database:
        return ""
    driver = str(db.get("driver") or "postgresql").strip() or "postgresql"
    if driver in {"postgres", "postgresql+psycopg", "postgresql+psycopg2"}:
        driver = "postgresql"
    port = _int(db.get("port"), 5432)
    username = str(db.get("username") or "postgres").strip() or "postgres"
    password = str(db.get("password") or "")
    sslmode = str(db.get("sslmode") or "prefer").strip() or "prefer"
    auth = quote_plus(username)
    if password:
        auth += ":" + quote_plus(password)
    return f"{driver}://{auth}@{host}:{port}/{quote_plus(database)}?sslmode={quote_plus(sslmode)}"


def resolve_llm_base_url(llm: Dict[str, Any]) -> str:
    explicit = str(llm.get("base_url") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = str(llm.get("host") or "").strip()
    if not host:
        return ""
    raw = host if host.startswith(("http://", "https://")) else f"http://{host}"
    parsed = urlsplit(raw)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    port = _int(llm.get("port"), 0)
    host_part = netloc.rsplit("@", 1)[-1]
    if port and ":" not in host_part:
        netloc = f"{netloc}:{port}"
    candidate = urlunsplit((scheme, netloc, path.rstrip("/"), "", "")).rstrip("/")
    if not candidate.endswith("/v1"):
        candidate += "/v1"
    return candidate


def mask_url(url: str) -> str:
    clean = str(url or "").strip()
    if not clean:
        return ""
    try:
        parsed = urlsplit(clean)
        if not parsed.password:
            return clean
        username = parsed.username or ""
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        netloc = f"{username}:********@{host}{port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
    except Exception:
        return clean.replace(str(clean), "[masked-url]")


def test_db(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    db = dict((settings or load_settings()).get("db") or {})
    if not bool(db.get("enabled")):
        return {"ok": True, "status": "disabled", "message": "DB bridge is disabled; sessions use local file storage."}
    url = resolve_postgres_url(db)
    if not url:
        return {"ok": False, "status": "missing_url", "message": "PostgreSQL URL or host/database is required."}
    if not (url.startswith("postgresql://") or url.startswith("postgres://")):
        return {"ok": False, "status": "unsupported_url", "message": "Only PostgreSQL URLs are accepted."}
    try:
        with _postgres_connection(url) as conn:
            _ensure_postgres_schema(conn)
        return {
            "ok": True,
            "status": "connected",
            "message": "PostgreSQL connection and V19 schema are ready.",
            "resolved_url": mask_url(url),
        }
    except Exception as exc:
        return {"ok": False, "status": "connection_failed", "message": str(exc), "resolved_url": mask_url(url)}


def ensure_local_database(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    db = dict((settings or load_settings()).get("db") or {})
    target_url = resolve_postgres_url(db)
    if not target_url:
        return {"ok": False, "status": "missing_url", "message": "PostgreSQL URL or host/database is required."}
    target = urlsplit(target_url)
    host = target.hostname or str(db.get("host") or "")
    if host not in {"", "localhost", "127.0.0.1", "::1"}:
        return {
            "ok": False,
            "status": "non_local_host",
            "message": "Database creation is only allowed for localhost / 127.0.0.1.",
            "resolved_url": mask_url(target_url),
        }
    database = str(db.get("database") or target.path.lstrip("/") or "").strip()
    if not database:
        return {"ok": False, "status": "missing_database", "message": "Database name is required."}
    if not re.match(r"^[A-Za-z0-9_\\-]+$", database):
        return {"ok": False, "status": "invalid_database", "message": "Database name may only contain letters, numbers, underscore, and hyphen."}

    maintenance_url = _maintenance_url(target_url)
    try:
        conn = _postgres_connection(maintenance_url)
        try:
            conn.autocommit = True
            existed = _database_exists(conn, database)
            if not existed:
                _create_database(conn, database)
        finally:
            conn.close()
        schema_result = test_db({"db": {**db, "enabled": True}})
        return {
            "ok": bool(schema_result.get("ok")),
            "status": "exists" if existed else "created",
            "message": "Local database already existed." if existed else "Local database created.",
            "schema": schema_result,
            "database": database,
            "resolved_url": mask_url(target_url),
        }
    except Exception as exc:
        return {"ok": False, "status": "create_failed", "message": str(exc), "resolved_url": mask_url(target_url)}


def create_or_append_session(payload: Dict[str, Any], turn: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    session_id = str(payload.get("session_id") or "").strip() or f"v19s_{uuid.uuid4().hex[:16]}"
    role = str(payload.get("role") or "guest").strip().lower()
    if role not in {"guest", "user", "practitioner", "admin"}:
        role = "guest"
    user_id = str(payload.get("user_id") or "").strip()
    session = get_session(session_id, settings=settings) or {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "created_at": utc_now(),
        "turns": [],
    }
    session["role"] = str(session.get("role") or role)
    session["user_id"] = str(session.get("user_id") or user_id)
    session["updated_at"] = utc_now()
    session["turns"].append(turn)
    saved = save_session(session, settings=settings)
    session["storage"] = saved
    return session


def create_auth_session(role: str, user_id: str = "", username: str = "") -> Dict[str, Any]:
    clean_role = str(role or "guest").strip().lower()
    if clean_role not in AUTH_ROLES:
        clean_role = "guest"
    clean_user_id = str(user_id or "").strip() or f"{clean_role}_{uuid.uuid4().hex[:10]}"
    token = "v19auth_" + uuid.uuid4().hex
    session = {
        "token": token,
        "role": clean_role,
        "user_id": clean_user_id,
        "username": str(username or clean_user_id).strip(),
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    sessions = _file_auth_sessions()
    sessions[token] = session
    _write_auth_sessions(sessions)
    return session


def get_auth_session(token: str) -> Dict[str, Any] | None:
    clean = str(token or "").strip()
    if not clean:
        return None
    session = _file_auth_sessions().get(clean)
    if not isinstance(session, dict):
        return None
    role = str(session.get("role") or "").strip().lower()
    if role not in AUTH_ROLES:
        return None
    return session


def delete_auth_session(token: str) -> None:
    clean = str(token or "").strip()
    if not clean:
        return
    sessions = _file_auth_sessions()
    if clean in sessions:
        del sessions[clean]
        _write_auth_sessions(sessions)


def list_bazi_profiles(owner_id: str) -> List[Dict[str, Any]]:
    owner = str(owner_id or "").strip()
    profiles = [dict(row) for row in _file_bazi_profiles().values() if str(row.get("owner_id") or "") == owner]
    return sorted(profiles, key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)


def get_bazi_profile(profile_id: str, owner_id: str = "") -> Dict[str, Any] | None:
    profile = _file_bazi_profiles().get(str(profile_id or "").strip())
    if not profile:
        return None
    owner = str(owner_id or "").strip()
    if owner and str(profile.get("owner_id") or "") != owner:
        return None
    return dict(profile)


def create_bazi_profile(owner_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    profiles = _file_bazi_profiles()
    profile_id = "bp_" + uuid.uuid4().hex[:16]
    now = utc_now()
    row = {
        "id": profile_id,
        "owner_id": str(owner_id or "").strip(),
        "name": str((payload or {}).get("name") or "My Bazi Profile").strip()[:80],
        "birth_input": dict((payload or {}).get("birth_input") or {}),
        "created_at": now,
        "updated_at": now,
    }
    profiles[profile_id] = row
    _write_bazi_profiles(profiles)
    return dict(row)


def update_bazi_profile(profile_id: str, owner_id: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    profiles = _file_bazi_profiles()
    clean_id = str(profile_id or "").strip()
    row = profiles.get(clean_id)
    if not row:
        return None
    owner = str(owner_id or "").strip()
    if owner and str(row.get("owner_id") or "") != owner:
        return None
    updated = dict(row)
    if "name" in (payload or {}):
        updated["name"] = str((payload or {}).get("name") or updated.get("name") or "My Bazi Profile").strip()[:80]
    if "birth_input" in (payload or {}):
        prior_birth = dict(updated.get("birth_input") or {})
        next_birth = dict((payload or {}).get("birth_input") or {})
        if "location" not in next_birth and prior_birth.get("location"):
            next_birth["location"] = prior_birth.get("location")
        updated["birth_input"] = next_birth
    updated["updated_at"] = utc_now()
    profiles[clean_id] = updated
    _write_bazi_profiles(profiles)
    return dict(updated)


def delete_bazi_profile(profile_id: str, owner_id: str) -> bool:
    profiles = _file_bazi_profiles()
    clean_id = str(profile_id or "").strip()
    row = profiles.get(clean_id)
    if not row:
        return False
    owner = str(owner_id or "").strip()
    if owner and str(row.get("owner_id") or "") != owner:
        return False
    del profiles[clean_id]
    _write_bazi_profiles(profiles)
    return True


def import_v17_admin_bazi_profiles(
    v17_db_path: str | Path | None = None,
    owner_id: str = "admin",
) -> Dict[str, Any]:
    db_path = Path(v17_db_path) if v17_db_path else ROOT.parent / "v17_rebirth" / ".runtime" / "v17_auth.db"
    if not db_path.exists():
        return {"ok": False, "code": "V17_AUTH_DB_NOT_FOUND", "message": f"V17 auth DB not found: {db_path}"}

    profiles = _file_bazi_profiles()
    existing_sources = {
        str((row.get("metadata") or {}).get("source_ref") or "")
        for row in profiles.values()
        if isinstance(row, dict)
    }
    rows = _read_v17_admin_profile_rows(db_path)
    imported: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    now = utc_now()

    for source in rows:
        source_ref = f"v17:auth_bazi_profiles:{source.get('id')}"
        if source_ref in existing_sources:
            skipped.append({"source_ref": source_ref, "name": source.get("profile_name"), "reason": "already_imported"})
            continue
        birth_input = _v17_birth_input(source)
        profile_id = "bp_" + uuid.uuid4().hex[:16]
        created_at = _iso_or_now(source.get("created_at"), now)
        updated_at = _iso_or_now(source.get("updated_at"), created_at)
        location = dict(birth_input.get("location") or {})
        row = {
            "id": profile_id,
            "owner_id": str(owner_id or "admin").strip() or "admin",
            "name": str(source.get("profile_name") or f"V17 Profile {source.get('id')}").strip()[:80],
            "birth_input": birth_input,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata": {
                "source": "v17_rebirth.auth_bazi_profiles",
                "source_ref": source_ref,
                "source_user_id": source.get("user_id"),
                "source_username": source.get("username"),
                "source_role": source.get("role"),
                "imported_at": now,
                "v17_location": location,
                "compatibility": {
                    "geo_preserved": bool(location.get("city_name") or location.get("city_code") or location.get("longitude") is not None),
                    "geo_not_used_by_v19_chart_engine": True,
                    "lunar_leap_month_preserved": bool(source.get("lunar_is_leap_month")),
                },
            },
        }
        profiles[profile_id] = row
        imported.append({"id": profile_id, "source_ref": source_ref, "name": row["name"], "location": location})
        existing_sources.add(source_ref)

    _write_bazi_profiles(profiles)
    return {
        "ok": True,
        "code": "OK",
        "source": str(db_path),
        "owner_id": str(owner_id or "admin").strip() or "admin",
        "scanned": len(rows),
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped,
    }


def get_session(session_id: str, settings: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    clean = str(session_id or "").strip()
    if not clean:
        return None
    db = dict((settings or load_settings()).get("db") or {})
    url = resolve_postgres_url(db)
    if db.get("enabled") and url:
        try:
            with _postgres_connection(url) as conn:
                _ensure_postgres_schema(conn)
                row = _db_get_session(conn, clean)
                if row:
                    return row
        except Exception:
            pass
    return _file_sessions().get(clean)


def list_sessions(settings: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    sessions = _file_sessions()
    return sorted(sessions.values(), key=lambda row: str(row.get("updated_at") or ""), reverse=True)[:50]


def save_session(session: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    db = dict((settings or load_settings()).get("db") or {})
    url = resolve_postgres_url(db)
    if db.get("enabled") and url:
        try:
            with _postgres_connection(url) as conn:
                _ensure_postgres_schema(conn)
                _db_save_session(conn, session)
            _file_save_session(session)
            return {"backend": "postgres", "fallback": "file_mirror", "resolved_url": mask_url(url)}
        except Exception as exc:
            _file_save_session(session)
            return {"backend": "file", "fallback_reason": str(exc), "resolved_url": mask_url(url)}
    _file_save_session(session)
    return {"backend": "file"}


def _file_sessions() -> Dict[str, Dict[str, Any]]:
    if not SESSIONS_FILE.exists():
        return {}
    try:
        payload = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): dict(value) for key, value in payload.items() if isinstance(value, dict)}


def _file_auth_sessions() -> Dict[str, Dict[str, Any]]:
    if not AUTH_SESSIONS_FILE.exists():
        return {}
    try:
        payload = json.loads(AUTH_SESSIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): dict(value) for key, value in payload.items() if isinstance(value, dict)}


def _write_auth_sessions(sessions: Dict[str, Dict[str, Any]]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    AUTH_SESSIONS_FILE.write_text(json.dumps(sessions, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _file_bazi_profiles() -> Dict[str, Dict[str, Any]]:
    if not BAZI_PROFILES_FILE.exists():
        return {}
    try:
        payload = json.loads(BAZI_PROFILES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): dict(value) for key, value in payload.items() if isinstance(value, dict)}


def _write_bazi_profiles(profiles: Dict[str, Dict[str, Any]]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    BAZI_PROFILES_FILE.write_text(json.dumps(profiles, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _read_v17_admin_profile_rows(db_path: Path) -> List[Dict[str, Any]]:
    sql = """
        select
            p.id,
            p.user_id,
            u.username,
            u.role,
            p.profile_name,
            p.birth_time_iso,
            p.gender,
            p.calendar_type,
            p.created_at,
            p.updated_at,
            p.last_used_at,
            p.city_name,
            p.city_code,
            p.city_group,
            p.city_longitude,
            p.lunar_is_leap_month
        from auth_bazi_profiles p
        join auth_users u on u.id = p.user_id
        where u.username = 'admin' and u.role = 'admin'
        order by p.id
    """
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql).fetchall()]


def _v17_birth_input(row: Dict[str, Any]) -> Dict[str, Any]:
    dt = _parse_v17_datetime(row.get("birth_time_iso"))
    calendar = str(row.get("calendar_type") or "solar").strip() or "solar"
    birth = {
        "calendar": calendar,
        "calendar_type": calendar,
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "gender": str(row.get("gender") or "unknown").strip() or "unknown",
        "lunar_is_leap_month": bool(row.get("lunar_is_leap_month")),
    }
    location = {
        "city_name": str(row.get("city_name") or "").strip(),
        "city_code": str(row.get("city_code") or "").strip(),
        "city_group": str(row.get("city_group") or "").strip(),
        "longitude": row.get("city_longitude"),
    }
    if location["city_name"] or location["city_code"] or location["city_group"] or location["longitude"] is not None:
        birth["location"] = location
    return birth


def _parse_v17_datetime(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime(1900, 1, 1)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")


def _iso_or_now(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(microsecond=0).isoformat()
    except ValueError:
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return fallback


def _file_save_session(session: Dict[str, Any]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    sessions = _file_sessions()
    sessions[str(session["session_id"])] = dict(session)
    SESSIONS_FILE.write_text(json.dumps(sessions, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _postgres_connection(url: str) -> Any:
    try:
        import psycopg  # type: ignore

        return psycopg.connect(url)
    except ModuleNotFoundError:
        import psycopg2  # type: ignore

        return psycopg2.connect(url)


def _ensure_postgres_schema(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS v19_agent_sessions (
                session_id TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_v19_agent_sessions_updated_at ON v19_agent_sessions(updated_at)")
    conn.commit()


def _db_save_session(conn: Any, session: Dict[str, Any]) -> None:
    payload = json.dumps(session, ensure_ascii=False, sort_keys=True)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO v19_agent_sessions (session_id, payload, created_at, updated_at)
            VALUES (%s, %s::jsonb, %s, %s)
            ON CONFLICT (session_id)
            DO UPDATE SET payload = EXCLUDED.payload, updated_at = EXCLUDED.updated_at
            """,
            (session["session_id"], payload, session.get("created_at"), session.get("updated_at")),
        )
    conn.commit()


def _db_get_session(conn: Any, session_id: str) -> Dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute("SELECT payload FROM v19_agent_sessions WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
    if not row:
        return None
    payload = row[0]
    if isinstance(payload, str):
        return dict(json.loads(payload))
    return dict(payload)


def _maintenance_url(target_url: str) -> str:
    parsed = urlsplit(target_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/postgres", parsed.query, parsed.fragment))


def _database_exists(conn: Any, database: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        return bool(cur.fetchone())


def _create_database(conn: Any, database: str) -> None:
    safe = database.replace('"', '""')
    with conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{safe}"')


def _preserve_secret(incoming: Dict[str, Any], key: str) -> bool:
    if key not in incoming:
        return True
    return str(incoming.get(key) or "").strip() in {"", MASK}


def _clean(value: Any, fallback: str = "") -> str:
    clean = str(value or "").strip()
    return clean or fallback


def _float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _clamp_float(value: Any, fallback: float, low: float, high: float) -> float:
    raw = _float(value, fallback)
    return max(low, min(high, raw))


def _int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
