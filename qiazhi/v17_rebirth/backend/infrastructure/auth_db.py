from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from v17_rebirth.paths import RUNTIME_DIR

ROLE_VALUES = {"admin", "manager", "practitioner", "user"}
GENDER_VALUES = {"male", "female"}
CALENDAR_VALUES = {"solar", "lunar"}
ROLE_REQUEST_STATUS_VALUES = {"pending", "approved", "rejected", "cancelled"}
PRACTITIONER_FEEDBACK_STATUS_VALUES = {"confirm", "reject", "watch", "review"}
PRACTITIONER_CASE_STATUS_VALUES = {"draft", "submitted", "accepted", "rejected", "benchmark_candidate"}
LEARNING_REVIEW_STATUS_VALUES = {"watch", "approved_for_experiment", "rejected"}
LEARNING_RELEASE_STATUS_VALUES = {"proposed", "approved", "rejected", "rolled_back"}
LEARNING_SCORECARD_VERDICT_VALUES = {"promote", "rework", "reject"}
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_DISPLAY_NAME = "System Admin"
DEFAULT_ADMIN_PASSWORD = "abcd1235"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _json_list(value: Any, *, limit: int = 40, item_limit: int = 160) -> List[str]:
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = []
    out: List[str] = []
    for item in raw_items:
        text = str(item or "").strip()
        if not text:
            continue
        out.append(text[:item_limit])
        if len(out) >= limit:
            break
    return out


def _json_dict(value: Any, *, key_limit: int = 80, value_limit: int = 160) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, str] = {}
    for key, val in value.items():
        key_text = str(key or "").strip()[:key_limit]
        if not key_text:
            continue
        out[key_text] = str(val or "").strip()[:value_limit]
    return out


def _load_json_list(value: Any) -> List[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except Exception:
        parsed = []
    return _json_list(parsed)


def _load_json_dict(value: Any) -> Dict[str, str]:
    try:
        parsed = json.loads(str(value or "{}"))
    except Exception:
        parsed = {}
    return _json_dict(parsed)


def _password_hash(password: str, *, iterations: int = 240_000, salt_hex: str | None = None) -> str:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iterations_raw, salt_hex, digest_hex = str(encoded or "").split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        expected = _password_hash(password, iterations=int(iterations_raw), salt_hex=salt_hex)
        return hmac.compare_digest(expected, encoded)
    except Exception:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _contribution_tier(score: float) -> str:
    if score >= 24:
        return "anchor"
    if score >= 10:
        return "active"
    if score > 0:
        return "seed"
    return "none"


@dataclass
class V17AuthDB:
    db_path: Path | None = None

    def __post_init__(self) -> None:
        self.db_path = self.db_path or (RUNTIME_DIR / "v17_auth.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._ensure_default_admin()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    last_seen_at TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    FOREIGN KEY(user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_role_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    requested_role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    reviewer_user_id INTEGER,
                    reviewer_role TEXT NOT NULL DEFAULT '',
                    reviewer_note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    decided_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES auth_users(id),
                    FOREIGN KEY(reviewer_user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_bazi_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    profile_name TEXT NOT NULL,
                    birth_time_iso TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    calendar_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_used_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS practitioner_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reviewer_role TEXT NOT NULL,
                    reviewer_weight REAL NOT NULL,
                    session_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    claim_id TEXT NOT NULL,
                    plugin_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    target_god TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source_title TEXT NOT NULL,
                    source_summary TEXT NOT NULL,
                    chart_fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS practitioner_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    owner_role TEXT NOT NULL,
                    owner_weight REAL NOT NULL,
                    case_key TEXT NOT NULL,
                    case_title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    birth_time_iso TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    calendar_type TEXT NOT NULL,
                    lunar_is_leap_month INTEGER NOT NULL DEFAULT 0,
                    city_name TEXT NOT NULL DEFAULT '',
                    city_code TEXT NOT NULL DEFAULT '',
                    city_group TEXT NOT NULL DEFAULT '',
                    city_longitude REAL,
                    four_pillars_json TEXT NOT NULL,
                    luck_pillar TEXT NOT NULL,
                    flow_pillar TEXT NOT NULL,
                    flow_year INTEGER,
                    tags_json TEXT NOT NULL,
                    expected_patterns_json TEXT NOT NULL,
                    expected_use_gods_json TEXT NOT NULL,
                    expected_risks_json TEXT NOT NULL,
                    boundary_flags_json TEXT NOT NULL,
                    failure_modes_json TEXT NOT NULL,
                    expected_notes TEXT NOT NULL,
                    source_feedback_ids_json TEXT NOT NULL,
                    chart_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS practitioner_learning_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT NOT NULL,
                    parameter_family TEXT NOT NULL,
                    reviewer_user_id INTEGER NOT NULL,
                    reviewer_role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reviewer_note TEXT NOT NULL,
                    safety_gate TEXT NOT NULL,
                    candidate_snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(reviewer_user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS practitioner_learning_releases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    parameter_family TEXT NOT NULL,
                    reviewer_user_id INTEGER NOT NULL,
                    reviewer_role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    release_summary TEXT NOT NULL,
                    test_report TEXT NOT NULL,
                    rollback_plan TEXT NOT NULL,
                    experiment_snapshot_json TEXT NOT NULL,
                    applied INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(reviewer_user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS practitioner_learning_scorecards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    parameter_family TEXT NOT NULL,
                    reviewer_user_id INTEGER NOT NULL,
                    reviewer_role TEXT NOT NULL,
                    synthetic_passed INTEGER NOT NULL DEFAULT 0,
                    practitioner_passed INTEGER NOT NULL DEFAULT 0,
                    improvement_count INTEGER NOT NULL DEFAULT 0,
                    regression_count INTEGER NOT NULL DEFAULT 0,
                    verdict TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(reviewer_user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_feedback_session ON practitioner_feedback(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_feedback_evidence ON practitioner_feedback(evidence_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_feedback_plugin ON practitioner_feedback(plugin_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_role_requests_user_status ON auth_role_requests(user_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_role_requests_status ON auth_role_requests(status)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_practitioner_cases_user_key ON practitioner_cases(user_id, case_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_cases_status ON practitioner_cases(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_cases_fingerprint ON practitioner_cases(chart_fingerprint)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_learning_reviews_candidate ON practitioner_learning_reviews(candidate_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_learning_reviews_status ON practitioner_learning_reviews(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_learning_releases_experiment ON practitioner_learning_releases(experiment_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_learning_releases_status ON practitioner_learning_releases(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_learning_scorecards_experiment ON practitioner_learning_scorecards(experiment_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_practitioner_learning_scorecards_verdict ON practitioner_learning_scorecards(verdict)")
            self._ensure_profile_columns(conn)
            conn.commit()

    def _ensure_profile_columns(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute("PRAGMA table_info(auth_bazi_profiles)").fetchall()
        existing = {str(row["name"] or "").strip() for row in rows}
        additions = [
            ("city_name", "TEXT NOT NULL DEFAULT ''"),
            ("city_code", "TEXT NOT NULL DEFAULT ''"),
            ("city_group", "TEXT NOT NULL DEFAULT ''"),
            ("city_longitude", "REAL"),
            ("lunar_is_leap_month", "INTEGER NOT NULL DEFAULT 0"),
        ]
        for column_name, column_type in additions:
            if column_name in existing:
                continue
            conn.execute(f"ALTER TABLE auth_bazi_profiles ADD COLUMN {column_name} {column_type}")

    def _count_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM auth_users").fetchone()
        return int(row["c"] if row else 0)

    def _count_admin_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM auth_users WHERE role = 'admin' AND is_active = 1"
            ).fetchone()
        return int(row["c"] if row else 0)

    def _ensure_default_admin(self) -> None:
        if self._count_admin_users() > 0:
            return
        now = _iso(_now_utc())
        encoded = _password_hash(DEFAULT_ADMIN_PASSWORD)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_users (
                    username, display_name, email, password_hash, role, is_active, created_at, updated_at
                ) VALUES (?, ?, NULL, ?, 'admin', 1, ?, ?)
                """,
                (
                    DEFAULT_ADMIN_USERNAME,
                    DEFAULT_ADMIN_DISPLAY_NAME,
                    encoded,
                    now,
                    now,
                ),
            )
            conn.commit()

    def _clean_user_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["is_active"] = bool(item.get("is_active"))
        item["role"] = str(item.get("role") or "user").strip() or "user"
        if "role_request_id" in item:
            try:
                item["role_request_id"] = int(item.get("role_request_id") or 0)
            except Exception:
                item["role_request_id"] = 0
        for key in (
            "role_request_status",
            "role_request_role",
            "role_request_reason",
            "role_request_created_at",
            "role_request_updated_at",
        ):
            if key in item:
                item[key] = str(item.get(key) or "").strip()
        contribution_int_keys = (
            "practitioner_feedback_count",
            "practitioner_confirm_count",
            "practitioner_reject_count",
            "practitioner_watch_count",
            "practitioner_review_count",
            "practitioner_case_count",
            "practitioner_benchmark_count",
        )
        for key in contribution_int_keys:
            if key in item:
                try:
                    item[key] = int(item.get(key) or 0)
                except Exception:
                    item[key] = 0
        if "practitioner_feedback_count" in item or "practitioner_case_count" in item:
            feedback_count = int(item.get("practitioner_feedback_count") or 0)
            confirm_count = int(item.get("practitioner_confirm_count") or 0)
            review_count = int(item.get("practitioner_review_count") or 0)
            watch_count = int(item.get("practitioner_watch_count") or 0)
            case_count = int(item.get("practitioner_case_count") or 0)
            benchmark_count = int(item.get("practitioner_benchmark_count") or 0)
            score = (
                feedback_count * 1.0
                + confirm_count * 0.8
                + (review_count + watch_count) * 0.4
                + case_count * 3.0
                + benchmark_count * 4.0
            )
            item["practitioner_contribution_score"] = round(score, 2)
            item["practitioner_contribution_tier"] = _contribution_tier(score)
            latest_feedback_at = str(item.get("practitioner_latest_feedback_at") or "").strip()
            latest_case_at = str(item.get("practitioner_latest_case_at") or "").strip()
            item["practitioner_latest_contribution_at"] = max(latest_feedback_at, latest_case_at)
            item.pop("practitioner_latest_feedback_at", None)
            item.pop("practitioner_latest_case_at", None)
        return item

    def create_user(
        self,
        *,
        username: str,
        password: str,
        display_name: str | None = None,
        email: str | None = None,
        role: str | None = None,
    ) -> Dict[str, Any]:
        username_clean = str(username or "").strip().lower()
        if len(username_clean) < 3:
            raise ValueError("用户名至少 3 个字符。")
        if len(str(password or "")) < 8:
            raise ValueError("密码至少 8 个字符。")
        display_name_clean = str(display_name or username_clean).strip() or username_clean
        email_clean = str(email or "").strip().lower() or None
        requested_role = str(role or "user").strip().lower() or "user"
        if requested_role not in ROLE_VALUES:
            requested_role = "user"

        if requested_role == "admin":
            raise ValueError("管理员账号为系统保留账号，不允许直接注册。")
        final_role = requested_role if requested_role in {"manager", "practitioner", "user"} else "user"
        now = _iso(_now_utc())
        encoded = _password_hash(password)

        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO auth_users (
                        username, display_name, email, password_hash, role, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        username_clean,
                        display_name_clean,
                        email_clean,
                        encoded,
                        final_role,
                        now,
                        now,
                    ),
                )
                user_id = int(cursor.lastrowid)
                row = conn.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
                conn.commit()
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "username" in message:
                raise ValueError("用户名已存在。") from exc
            if "email" in message:
                raise ValueError("邮箱已存在。") from exc
            raise ValueError("用户创建失败。") from exc

        user = self._clean_user_row(row)
        if not user:
            raise ValueError("用户创建失败。")
        user["bootstrap_admin"] = False
        return user

    def authenticate(self, identifier: str, password: str) -> Dict[str, Any] | None:
        ident = str(identifier or "").strip().lower()
        if not ident or not password:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM auth_users
                WHERE username = ? OR lower(coalesce(email, '')) = ?
                LIMIT 1
                """,
                (ident, ident),
            ).fetchone()
            user = self._clean_user_row(row)
            if not user or not user.get("is_active"):
                return None
            if not _verify_password(password, str(user.get("password_hash") or "")):
                return None
            now = _iso(_now_utc())
            conn.execute("UPDATE auth_users SET last_login_at = ?, updated_at = ? WHERE id = ?", (now, now, user["id"]))
            conn.commit()
            user["last_login_at"] = now
            return user

    def create_session(
        self,
        *,
        user_id: int,
        user_agent: str | None = None,
        ip_address: str | None = None,
        lifetime_days: int = 7,
    ) -> Dict[str, Any]:
        created_at = _now_utc()
        expires_at = created_at + timedelta(days=max(1, lifetime_days))
        token = secrets.token_urlsafe(32)
        token_digest = _token_hash(token)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_sessions (
                    user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at, user_agent, ip_address
                ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    user_id,
                    token_digest,
                    _iso(created_at),
                    _iso(expires_at),
                    _iso(created_at),
                    str(user_agent or "").strip(),
                    str(ip_address or "").strip(),
                ),
            )
            conn.commit()
        return {
            "session_token": token,
            "created_at": _iso(created_at),
            "expires_at": _iso(expires_at),
        }

    def get_user_by_session_token(self, token: str, *, touch: bool = True) -> Dict[str, Any] | None:
        raw = str(token or "").strip()
        if not raw:
            return None
        digest = _token_hash(raw)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    u.*,
                    s.id AS session_id,
                    s.created_at AS session_created_at,
                    s.expires_at AS session_expires_at,
                    s.revoked_at AS session_revoked_at
                FROM auth_sessions s
                JOIN auth_users u ON u.id = s.user_id
                WHERE s.token_hash = ?
                LIMIT 1
                """,
                (digest,),
            ).fetchone()
            user = self._clean_user_row(row)
            if not user or not user.get("is_active"):
                return None
            expires_at = _parse_iso(user.get("session_expires_at"))
            revoked_at = _parse_iso(user.get("session_revoked_at"))
            now = _now_utc()
            if revoked_at is not None or expires_at is None or expires_at <= now:
                return None
            if touch:
                conn.execute(
                    "UPDATE auth_sessions SET last_seen_at = ? WHERE id = ?",
                    (_iso(now), int(user.get("session_id") or 0)),
                )
                conn.commit()
            return user

    def revoke_session(self, token: str) -> None:
        raw = str(token or "").strip()
        if not raw:
            return
        with self._connect() as conn:
            conn.execute(
                "UPDATE auth_sessions SET revoked_at = ? WHERE token_hash = ?",
                (_iso(_now_utc()), _token_hash(raw)),
            )
            conn.commit()

    def list_users(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.display_name,
                    u.email,
                    u.role,
                    u.is_active,
                    u.created_at,
                    u.updated_at,
                    u.last_login_at,
                    (
                        SELECT s.ip_address
                        FROM auth_sessions s
                        WHERE s.user_id = u.id
                        ORDER BY coalesce(s.last_seen_at, s.created_at) DESC, s.id DESC
                        LIMIT 1
                    ) AS latest_ip_address,
                    (
                        SELECT s.user_agent
                        FROM auth_sessions s
                        WHERE s.user_id = u.id
                        ORDER BY coalesce(s.last_seen_at, s.created_at) DESC, s.id DESC
                        LIMIT 1
                    ) AS latest_user_agent,
                    (
                        SELECT coalesce(s.last_seen_at, s.created_at)
                        FROM auth_sessions s
                        WHERE s.user_id = u.id
                        ORDER BY coalesce(s.last_seen_at, s.created_at) DESC, s.id DESC
                        LIMIT 1
                    ) AS latest_seen_at,
                    (
                        SELECT rr.id
                        FROM auth_role_requests rr
                        WHERE rr.user_id = u.id
                        ORDER BY rr.created_at DESC, rr.id DESC
                        LIMIT 1
                    ) AS role_request_id,
                    (
                        SELECT rr.status
                        FROM auth_role_requests rr
                        WHERE rr.user_id = u.id
                        ORDER BY rr.created_at DESC, rr.id DESC
                        LIMIT 1
                    ) AS role_request_status,
                    (
                        SELECT rr.requested_role
                        FROM auth_role_requests rr
                        WHERE rr.user_id = u.id
                        ORDER BY rr.created_at DESC, rr.id DESC
                        LIMIT 1
                    ) AS role_request_role,
                    (
                        SELECT rr.reason
                        FROM auth_role_requests rr
                        WHERE rr.user_id = u.id
                        ORDER BY rr.created_at DESC, rr.id DESC
                        LIMIT 1
                    ) AS role_request_reason,
                    (
                        SELECT rr.created_at
                        FROM auth_role_requests rr
                        WHERE rr.user_id = u.id
                        ORDER BY rr.created_at DESC, rr.id DESC
                        LIMIT 1
                    ) AS role_request_created_at,
                    (
                        SELECT rr.updated_at
                        FROM auth_role_requests rr
                        WHERE rr.user_id = u.id
                        ORDER BY rr.created_at DESC, rr.id DESC
                        LIMIT 1
                    ) AS role_request_updated_at,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_feedback pf
                        WHERE pf.user_id = u.id
                    ) AS practitioner_feedback_count,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_feedback pf
                        WHERE pf.user_id = u.id AND pf.status = 'confirm'
                    ) AS practitioner_confirm_count,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_feedback pf
                        WHERE pf.user_id = u.id AND pf.status = 'reject'
                    ) AS practitioner_reject_count,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_feedback pf
                        WHERE pf.user_id = u.id AND pf.status = 'watch'
                    ) AS practitioner_watch_count,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_feedback pf
                        WHERE pf.user_id = u.id AND pf.status = 'review'
                    ) AS practitioner_review_count,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_cases pc
                        WHERE pc.user_id = u.id
                    ) AS practitioner_case_count,
                    (
                        SELECT COUNT(*)
                        FROM practitioner_cases pc
                        WHERE pc.user_id = u.id AND pc.status = 'benchmark_candidate'
                    ) AS practitioner_benchmark_count,
                    (
                        SELECT MAX(pf.updated_at)
                        FROM practitioner_feedback pf
                        WHERE pf.user_id = u.id
                    ) AS practitioner_latest_feedback_at,
                    (
                        SELECT MAX(pc.updated_at)
                        FROM practitioner_cases pc
                        WHERE pc.user_id = u.id
                    ) AS practitioner_latest_case_at
                FROM auth_users u
                ORDER BY id ASC
                """
            ).fetchall()
        return [self._clean_user_row(row) or {} for row in rows]

    def _clean_role_request_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["user_id"] = int(item.get("user_id") or 0)
        item["requested_role"] = str(item.get("requested_role") or "").strip().lower()
        item["status"] = str(item.get("status") or "pending").strip().lower() or "pending"
        item["reason"] = str(item.get("reason") or "").strip()
        item["reviewer_user_id"] = int(item.get("reviewer_user_id") or 0)
        item["reviewer_role"] = str(item.get("reviewer_role") or "").strip().lower()
        item["reviewer_note"] = str(item.get("reviewer_note") or "").strip()
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        item["decided_at"] = str(item.get("decided_at") or "").strip()
        item["username"] = str(item.get("username") or "").strip()
        item["display_name"] = str(item.get("display_name") or "").strip()
        item["email"] = str(item.get("email") or "").strip()
        item["current_role"] = str(item.get("current_role") or "").strip().lower()
        item["reviewer_username"] = str(item.get("reviewer_username") or "").strip()
        item["reviewer_display_name"] = str(item.get("reviewer_display_name") or "").strip()
        return item

    def _fetch_role_request(self, conn: sqlite3.Connection, request_id: int) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT
                rr.*,
                u.username,
                u.display_name,
                u.email,
                u.role AS current_role,
                reviewer.username AS reviewer_username,
                reviewer.display_name AS reviewer_display_name
            FROM auth_role_requests rr
            JOIN auth_users u ON u.id = rr.user_id
            LEFT JOIN auth_users reviewer ON reviewer.id = rr.reviewer_user_id
            WHERE rr.id = ?
            LIMIT 1
            """,
            (int(request_id),),
        ).fetchone()

    def create_role_request(self, *, user_id: int, requested_role: str, reason: str | None = None) -> Dict[str, Any]:
        requested_role_clean = str(requested_role or "").strip().lower()
        if requested_role_clean != "practitioner":
            raise ValueError("当前仅支持申请命理师权限。")
        reason_clean = str(reason or "").strip()[:1200]
        now = _iso(_now_utc())
        with self._connect() as conn:
            user_row = conn.execute("SELECT * FROM auth_users WHERE id = ?", (int(user_id),)).fetchone()
            user = self._clean_user_row(user_row)
            if not user:
                raise ValueError("用户不存在。")
            if str(user.get("role") or "user") in {"practitioner", "manager", "admin"}:
                raise ValueError("当前账号已具备命理师工作权限。")
            pending = conn.execute(
                """
                SELECT id FROM auth_role_requests
                WHERE user_id = ? AND requested_role = ? AND status = 'pending'
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (int(user_id), requested_role_clean),
            ).fetchone()
            if pending:
                request_id = int(pending["id"])
                conn.execute(
                    """
                    UPDATE auth_role_requests
                    SET reason = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (reason_clean, now, request_id),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO auth_role_requests (
                        user_id, requested_role, status, reason, created_at, updated_at
                    ) VALUES (?, ?, 'pending', ?, ?, ?)
                    """,
                    (int(user_id), requested_role_clean, reason_clean, now, now),
                )
                request_id = int(cursor.lastrowid)
            row = self._fetch_role_request(conn, request_id)
            conn.commit()
        request_row = self._clean_role_request_row(row)
        if not request_row:
            raise ValueError("角色申请创建失败。")
        return request_row

    def list_role_requests(self, *, status: str | None = "pending", limit: int = 80) -> List[Dict[str, Any]]:
        status_clean = str(status or "pending").strip().lower()
        limit_clean = max(1, min(int(limit or 80), 200))
        params: List[Any] = []
        where = ""
        if status_clean and status_clean != "all":
            if status_clean not in ROLE_REQUEST_STATUS_VALUES:
                raise ValueError("无效申请状态。")
            where = "WHERE rr.status = ?"
            params.append(status_clean)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    rr.*,
                    u.username,
                    u.display_name,
                    u.email,
                    u.role AS current_role,
                    reviewer.username AS reviewer_username,
                    reviewer.display_name AS reviewer_display_name
                FROM auth_role_requests rr
                JOIN auth_users u ON u.id = rr.user_id
                LEFT JOIN auth_users reviewer ON reviewer.id = rr.reviewer_user_id
                {where}
                ORDER BY
                    CASE rr.status WHEN 'pending' THEN 0 ELSE 1 END,
                    rr.created_at DESC,
                    rr.id DESC
                LIMIT ?
                """,
                (*params, limit_clean),
            ).fetchall()
        return [self._clean_role_request_row(row) or {} for row in rows]

    def decide_role_request(
        self,
        request_id: int,
        *,
        status: str,
        reviewer_user_id: int,
        reviewer_role: str,
        reviewer_note: str | None = None,
    ) -> Dict[str, Any]:
        status_clean = str(status or "").strip().lower()
        if status_clean in {"approve", "accept"}:
            status_clean = "approved"
        if status_clean in {"reject", "deny"}:
            status_clean = "rejected"
        if status_clean not in {"approved", "rejected"}:
            raise ValueError("审核结果必须是 approved 或 rejected。")
        reviewer_role_clean = str(reviewer_role or "").strip().lower()
        if reviewer_role_clean not in {"manager", "admin"}:
            raise ValueError("只有 manager 或 admin 可以审核命理师申请。")
        note_clean = str(reviewer_note or "").strip()[:1200]
        now = _iso(_now_utc())
        with self._connect() as conn:
            row = self._fetch_role_request(conn, int(request_id))
            request_row = self._clean_role_request_row(row)
            if not request_row:
                raise ValueError("角色申请不存在。")
            if request_row["status"] != "pending":
                raise ValueError("该申请已经处理。")
            if request_row["requested_role"] != "practitioner":
                raise ValueError("当前仅支持审核命理师权限申请。")

            updated_user_row = conn.execute(
                "SELECT * FROM auth_users WHERE id = ?",
                (int(request_row["user_id"]),),
            ).fetchone()
            updated_user = self._clean_user_row(updated_user_row)
            if not updated_user:
                raise ValueError("申请用户不存在。")
            if status_clean == "approved" and str(updated_user.get("role") or "user") == "user":
                conn.execute(
                    "UPDATE auth_users SET role = 'practitioner', updated_at = ? WHERE id = ?",
                    (now, int(request_row["user_id"])),
                )
                updated_user_row = conn.execute(
                    "SELECT * FROM auth_users WHERE id = ?",
                    (int(request_row["user_id"]),),
                ).fetchone()
                updated_user = self._clean_user_row(updated_user_row)
            conn.execute(
                """
                UPDATE auth_role_requests
                SET status = ?, reviewer_user_id = ?, reviewer_role = ?, reviewer_note = ?, updated_at = ?, decided_at = ?
                WHERE id = ?
                """,
                (status_clean, int(reviewer_user_id), reviewer_role_clean, note_clean, now, now, int(request_id)),
            )
            final_row = self._fetch_role_request(conn, int(request_id))
            conn.commit()

        final_request = self._clean_role_request_row(final_row)
        if not final_request:
            raise ValueError("角色申请审核失败。")
        return {
            "request": final_request,
            "updated_user": updated_user or {},
        }

    def _clean_profile_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["user_id"] = int(item.get("user_id") or 0)
        item["profile_name"] = str(item.get("profile_name") or "").strip()
        item["birth_time_iso"] = str(item.get("birth_time_iso") or "").strip()
        item["gender"] = str(item.get("gender") or "").strip().lower() or "male"
        item["calendar_type"] = str(item.get("calendar_type") or "").strip().lower() or "solar"
        item["lunar_is_leap_month"] = bool(item.get("lunar_is_leap_month"))
        item["city_name"] = str(item.get("city_name") or "").strip()
        item["city_code"] = str(item.get("city_code") or "").strip()
        item["city_group"] = str(item.get("city_group") or "").strip()
        raw_longitude = item.get("city_longitude")
        try:
            item["city_longitude"] = None if raw_longitude in (None, "") else float(raw_longitude)
        except Exception:
            item["city_longitude"] = None
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        item["last_used_at"] = str(item.get("last_used_at") or "").strip()
        return item

    def list_profiles(self, user_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    user_id,
                    profile_name,
                    birth_time_iso,
                    gender,
                    calendar_type,
                    lunar_is_leap_month,
                    city_name,
                    city_code,
                    city_group,
                    city_longitude,
                    created_at,
                    updated_at,
                    last_used_at
                FROM auth_bazi_profiles
                WHERE user_id = ?
                ORDER BY coalesce(last_used_at, updated_at, created_at) DESC, id DESC
                """,
                (int(user_id),),
            ).fetchall()
        return [self._clean_profile_row(row) or {} for row in rows]

    def create_profile(
        self,
        *,
        user_id: int,
        profile_name: str,
        birth_time_iso: str,
        gender: str,
        calendar_type: str,
        lunar_is_leap_month: bool = False,
        city_name: str = "",
        city_code: str = "",
        city_group: str = "",
        city_longitude: float | None = None,
    ) -> Dict[str, Any]:
        profile_name_clean = str(profile_name or "").strip()
        if not profile_name_clean:
            raise ValueError("档案名称不能为空。")
        if len(profile_name_clean) > 80:
            raise ValueError("档案名称最多 80 个字符。")
        birth_time_clean = str(birth_time_iso or "").strip()
        if not birth_time_clean:
            raise ValueError("出生时间不能为空。")
        gender_clean = str(gender or "").strip().lower()
        if gender_clean not in GENDER_VALUES:
            raise ValueError("无效性别。")
        calendar_clean = str(calendar_type or "").strip().lower()
        if calendar_clean not in CALENDAR_VALUES:
            raise ValueError("无效历法。")
        city_name_clean = str(city_name or "").strip()
        if len(city_name_clean) > 80:
            raise ValueError("城市名称最多 80 个字符。")
        city_code_clean = str(city_code or "").strip()
        if len(city_code_clean) > 40:
            raise ValueError("城市编码无效。")
        city_group_clean = str(city_group or "").strip()
        if len(city_group_clean) > 80:
            raise ValueError("城市分组无效。")
        city_longitude_value: float | None
        try:
            city_longitude_value = None if city_longitude in (None, "") else float(city_longitude)
        except Exception as exc:
            raise ValueError("城市经度无效。") from exc
        now = _iso(_now_utc())
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO auth_bazi_profiles (
                    user_id,
                    profile_name,
                    birth_time_iso,
                    gender,
                    calendar_type,
                    lunar_is_leap_month,
                    city_name,
                    city_code,
                    city_group,
                    city_longitude,
                    created_at,
                    updated_at,
                    last_used_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    profile_name_clean,
                    birth_time_clean,
                    gender_clean,
                    calendar_clean,
                    1 if lunar_is_leap_month and calendar_clean == "lunar" else 0,
                    city_name_clean,
                    city_code_clean,
                    city_group_clean,
                    city_longitude_value,
                    now,
                    now,
                    now,
                ),
            )
            profile_id = int(cursor.lastrowid)
            row = conn.execute(
                """
                SELECT
                    id,
                    user_id,
                    profile_name,
                    birth_time_iso,
                    gender,
                    calendar_type,
                    lunar_is_leap_month,
                    city_name,
                    city_code,
                    city_group,
                    city_longitude,
                    created_at,
                    updated_at,
                    last_used_at
                FROM auth_bazi_profiles
                WHERE id = ?
                """,
                (profile_id,),
            ).fetchone()
            conn.commit()
        profile = self._clean_profile_row(row)
        if not profile:
            raise ValueError("档案创建失败。")
        return profile

    def update_profile(
        self,
        profile_id: int,
        *,
        user_id: int,
        profile_name: str,
        birth_time_iso: str,
        gender: str,
        calendar_type: str,
        lunar_is_leap_month: bool = False,
        city_name: str = "",
        city_code: str = "",
        city_group: str = "",
        city_longitude: float | None = None,
    ) -> Dict[str, Any]:
        profile_name_clean = str(profile_name or "").strip()
        if not profile_name_clean:
            raise ValueError("档案名称不能为空。")
        if len(profile_name_clean) > 80:
            raise ValueError("档案名称最多 80 个字符。")
        birth_time_clean = str(birth_time_iso or "").strip()
        if not birth_time_clean:
            raise ValueError("出生时间不能为空。")
        gender_clean = str(gender or "").strip().lower()
        if gender_clean not in GENDER_VALUES:
            raise ValueError("无效性别。")
        calendar_clean = str(calendar_type or "").strip().lower()
        if calendar_clean not in CALENDAR_VALUES:
            raise ValueError("无效历法。")
        city_name_clean = str(city_name or "").strip()
        if len(city_name_clean) > 80:
            raise ValueError("城市名称最多 80 个字符。")
        city_code_clean = str(city_code or "").strip()
        if len(city_code_clean) > 40:
            raise ValueError("城市编码无效。")
        city_group_clean = str(city_group or "").strip()
        if len(city_group_clean) > 80:
            raise ValueError("城市分组无效。")
        city_longitude_value: float | None
        try:
            city_longitude_value = None if city_longitude in (None, "") else float(city_longitude)
        except Exception as exc:
            raise ValueError("城市经度无效。") from exc
        now = _iso(_now_utc())
        with self._connect() as conn:
            current = conn.execute(
                "SELECT id FROM auth_bazi_profiles WHERE id = ? AND user_id = ?",
                (int(profile_id), int(user_id)),
            ).fetchone()
            if not current:
                raise ValueError("档案不存在。")
            conn.execute(
                """
                UPDATE auth_bazi_profiles
                SET
                    profile_name = ?,
                    birth_time_iso = ?,
                    gender = ?,
                    calendar_type = ?,
                    lunar_is_leap_month = ?,
                    city_name = ?,
                    city_code = ?,
                    city_group = ?,
                    city_longitude = ?,
                    updated_at = ?,
                    last_used_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    profile_name_clean,
                    birth_time_clean,
                    gender_clean,
                    calendar_clean,
                    1 if lunar_is_leap_month and calendar_clean == "lunar" else 0,
                    city_name_clean,
                    city_code_clean,
                    city_group_clean,
                    city_longitude_value,
                    now,
                    now,
                    int(profile_id),
                    int(user_id),
                ),
            )
            row = conn.execute(
                """
                SELECT
                    id,
                    user_id,
                    profile_name,
                    birth_time_iso,
                    gender,
                    calendar_type,
                    lunar_is_leap_month,
                    city_name,
                    city_code,
                    city_group,
                    city_longitude,
                    created_at,
                    updated_at,
                    last_used_at
                FROM auth_bazi_profiles
                WHERE id = ?
                """,
                (int(profile_id),),
            ).fetchone()
            conn.commit()
        profile = self._clean_profile_row(row)
        if not profile:
            raise ValueError("档案更新失败。")
        return profile

    def delete_profile(self, profile_id: int, *, user_id: int) -> None:
        with self._connect() as conn:
            current = conn.execute(
                "SELECT id FROM auth_bazi_profiles WHERE id = ? AND user_id = ?",
                (int(profile_id), int(user_id)),
            ).fetchone()
            if not current:
                raise ValueError("档案不存在。")
            conn.execute(
                "DELETE FROM auth_bazi_profiles WHERE id = ? AND user_id = ?",
                (int(profile_id), int(user_id)),
            )
            conn.commit()

    def touch_profile(self, profile_id: int, *, user_id: int) -> Dict[str, Any]:
        now = _iso(_now_utc())
        with self._connect() as conn:
            current = conn.execute(
                "SELECT id FROM auth_bazi_profiles WHERE id = ? AND user_id = ?",
                (int(profile_id), int(user_id)),
            ).fetchone()
            if not current:
                raise ValueError("档案不存在。")
            conn.execute(
                "UPDATE auth_bazi_profiles SET last_used_at = ? WHERE id = ? AND user_id = ?",
                (now, int(profile_id), int(user_id)),
            )
            row = conn.execute(
                """
                SELECT
                    id,
                    user_id,
                    profile_name,
                    birth_time_iso,
                    gender,
                    calendar_type,
                    lunar_is_leap_month,
                    city_name,
                    city_code,
                    city_group,
                    city_longitude,
                    created_at,
                    updated_at,
                    last_used_at
                FROM auth_bazi_profiles
                WHERE id = ?
                """,
                (int(profile_id),),
            ).fetchone()
            conn.commit()
        profile = self._clean_profile_row(row)
        if not profile:
            raise ValueError("档案更新时间失败。")
        return profile

    def update_user_role(self, user_id: int, role: str, *, actor_role: str = "admin") -> Dict[str, Any]:
        next_role = str(role or "").strip().lower()
        if next_role not in ROLE_VALUES:
            raise ValueError("无效角色。")
        actor_role_clean = str(actor_role or "").strip().lower() or "user"
        if actor_role_clean not in ROLE_VALUES:
            raise ValueError("无效操作者角色。")
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
            user = self._clean_user_row(row)
            if not user:
                raise ValueError("用户不存在。")
            current_role = str(user.get("role") or "").strip().lower()
            if actor_role_clean == "manager":
                if current_role == "admin":
                    raise ValueError("manager 无权修改管理员账号。")
                if next_role == "admin":
                    raise ValueError("manager 无权提升为管理员。")
            if next_role == "admin" and str(user.get("role") or "") != "admin":
                raise ValueError("系统仅允许唯一管理员账号。")
            if str(user.get("role") or "") == "admin" and next_role != "admin":
                raise ValueError("系统默认管理员不可降级。")
            now = _iso(_now_utc())
            conn.execute(
                "UPDATE auth_users SET role = ?, updated_at = ? WHERE id = ?",
                (next_role, now, user_id),
            )
            if next_role == "practitioner":
                conn.execute(
                    """
                    UPDATE auth_role_requests
                    SET status = 'approved',
                        reviewer_role = ?,
                        reviewer_note = CASE
                            WHEN reviewer_note = '' THEN 'manual role update'
                            ELSE reviewer_note
                        END,
                        updated_at = ?,
                        decided_at = coalesce(decided_at, ?)
                    WHERE user_id = ?
                      AND requested_role = 'practitioner'
                      AND status = 'pending'
                    """,
                    (actor_role_clean, now, now, user_id),
                )
            row = conn.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
            conn.commit()
        updated = self._clean_user_row(row)
        if not updated:
            raise ValueError("角色更新失败。")
        return updated

    def _clean_feedback_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["user_id"] = int(item.get("user_id") or 0)
        item["reviewer_role"] = str(item.get("reviewer_role") or "user").strip().lower() or "user"
        item["reviewer_weight"] = float(item.get("reviewer_weight") or 1.0)
        item["session_id"] = str(item.get("session_id") or "").strip()
        item["evidence_id"] = str(item.get("evidence_id") or "").strip()
        item["claim_id"] = str(item.get("claim_id") or "").strip()
        item["plugin_id"] = str(item.get("plugin_id") or "").strip()
        item["evidence_type"] = str(item.get("evidence_type") or "").strip()
        item["target_god"] = str(item.get("target_god") or "").strip()
        item["status"] = str(item.get("status") or "").strip()
        item["reason"] = str(item.get("reason") or "").strip()
        item["confidence"] = float(item.get("confidence") or 0.0)
        item["source_title"] = str(item.get("source_title") or "").strip()
        item["source_summary"] = str(item.get("source_summary") or "").strip()
        item["chart_fingerprint"] = str(item.get("chart_fingerprint") or "").strip()
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        try:
            payload = json.loads(str(item.get("payload_json") or "{}"))
        except Exception:
            payload = {}
        item["payload"] = payload if isinstance(payload, dict) else {}
        item.pop("payload_json", None)
        return item

    def create_practitioner_feedback(
        self,
        *,
        user_id: int,
        reviewer_role: str,
        session_id: str,
        evidence_id: str,
        claim_id: str = "",
        plugin_id: str = "",
        evidence_type: str = "",
        target_god: str = "",
        status: str,
        reason: str = "",
        confidence: float = 0.0,
        source_title: str = "",
        source_summary: str = "",
        chart_fingerprint: str = "",
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        role_clean = str(reviewer_role or "user").strip().lower() or "user"
        if role_clean not in ROLE_VALUES:
            role_clean = "user"
        status_clean = str(status or "").strip().lower()
        if status_clean not in PRACTITIONER_FEEDBACK_STATUS_VALUES:
            raise ValueError("无效反馈状态。")
        session_clean = str(session_id or "").strip()[:120]
        evidence_clean = str(evidence_id or "").strip()[:180]
        if not evidence_clean:
            raise ValueError("证据 ID 不能为空。")
        reason_clean = str(reason or "").strip()
        if len(reason_clean) > 1000:
            raise ValueError("反馈理由最多 1000 个字符。")
        try:
            confidence_value = max(0.0, min(1.0, float(confidence or 0.0)))
        except Exception:
            confidence_value = 0.0
        reviewer_weight = {"user": 1.0, "practitioner": 2.0, "manager": 2.2, "admin": 2.6}.get(role_clean, 1.0)
        payload_obj = payload if isinstance(payload, dict) else {}
        payload_json = json.dumps(payload_obj, ensure_ascii=False, sort_keys=True, default=str)
        if len(payload_json) > 12000:
            payload_json = json.dumps({"truncated": True, "source_title": str(source_title or "")[:240]}, ensure_ascii=False)
        now = _iso(_now_utc())
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO practitioner_feedback (
                    user_id,
                    reviewer_role,
                    reviewer_weight,
                    session_id,
                    evidence_id,
                    claim_id,
                    plugin_id,
                    evidence_type,
                    target_god,
                    status,
                    reason,
                    confidence,
                    source_title,
                    source_summary,
                    chart_fingerprint,
                    payload_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    role_clean,
                    reviewer_weight,
                    session_clean,
                    evidence_clean,
                    str(claim_id or "").strip()[:180],
                    str(plugin_id or "").strip()[:180],
                    str(evidence_type or "").strip()[:80],
                    str(target_god or "").strip()[:80],
                    status_clean,
                    reason_clean,
                    confidence_value,
                    str(source_title or "").strip()[:240],
                    str(source_summary or "").strip()[:800],
                    str(chart_fingerprint or "").strip()[:160],
                    payload_json,
                    now,
                    now,
                ),
            )
            feedback_id = int(cursor.lastrowid)
            row = conn.execute("SELECT * FROM practitioner_feedback WHERE id = ?", (feedback_id,)).fetchone()
            conn.commit()
        feedback = self._clean_feedback_row(row)
        if not feedback:
            raise ValueError("反馈记录失败。")
        return feedback

    def list_practitioner_feedback(
        self,
        *,
        user_id: int,
        reviewer_role: str,
        session_id: str = "",
        evidence_id: str = "",
        plugin_id: str = "",
        scope: str = "own",
        limit: int = 80,
    ) -> List[Dict[str, Any]]:
        role_clean = str(reviewer_role or "user").strip().lower()
        can_view_all = role_clean in {"manager", "admin"} and str(scope or "").strip().lower() == "all"
        where: List[str] = []
        params: List[Any] = []
        if not can_view_all:
            where.append("pf.user_id = ?")
            params.append(int(user_id))
        session_clean = str(session_id or "").strip()
        evidence_clean = str(evidence_id or "").strip()
        plugin_clean = str(plugin_id or "").strip()
        if session_clean:
            where.append("pf.session_id = ?")
            params.append(session_clean)
        if evidence_clean:
            where.append("pf.evidence_id = ?")
            params.append(evidence_clean)
        if plugin_clean:
            where.append("pf.plugin_id = ?")
            params.append(plugin_clean)
        sql = "SELECT pf.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name FROM practitioner_feedback pf JOIN auth_users u ON u.id = pf.user_id"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY pf.created_at DESC, pf.id DESC LIMIT ?"
        params.append(max(1, min(300, int(limit or 80))))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        out: List[Dict[str, Any]] = []
        for row in rows:
            item = self._clean_feedback_row(row)
            if not item:
                continue
            item["reviewer_username"] = str(dict(row).get("reviewer_username") or "").strip()
            item["reviewer_display_name"] = str(dict(row).get("reviewer_display_name") or "").strip()
            out.append(item)
        return out

    def _clean_practitioner_case_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["user_id"] = int(item.get("user_id") or 0)
        item["owner_role"] = str(item.get("owner_role") or "user").strip().lower() or "user"
        item["owner_weight"] = float(item.get("owner_weight") or 1.0)
        item["case_key"] = str(item.get("case_key") or "").strip()
        item["case_title"] = str(item.get("case_title") or "").strip()
        item["description"] = str(item.get("description") or "").strip()
        item["birth_time_iso"] = str(item.get("birth_time_iso") or "").strip()
        item["gender"] = str(item.get("gender") or "").strip()
        item["calendar_type"] = str(item.get("calendar_type") or "").strip()
        item["lunar_is_leap_month"] = bool(item.get("lunar_is_leap_month"))
        item["city_name"] = str(item.get("city_name") or "").strip()
        item["city_code"] = str(item.get("city_code") or "").strip()
        item["city_group"] = str(item.get("city_group") or "").strip()
        item["city_longitude"] = item.get("city_longitude")
        item["four_pillars"] = _load_json_dict(item.get("four_pillars_json"))
        item["luck_pillar"] = str(item.get("luck_pillar") or "").strip()
        item["flow_pillar"] = str(item.get("flow_pillar") or "").strip()
        item["flow_year"] = item.get("flow_year")
        item["tags"] = _load_json_list(item.get("tags_json"))
        item["expected_patterns"] = _load_json_list(item.get("expected_patterns_json"))
        item["expected_use_gods"] = _load_json_list(item.get("expected_use_gods_json"))
        item["expected_risks"] = _load_json_list(item.get("expected_risks_json"))
        item["boundary_flags"] = _load_json_list(item.get("boundary_flags_json"))
        item["failure_modes"] = _load_json_list(item.get("failure_modes_json"))
        item["expected_notes"] = str(item.get("expected_notes") or "").strip()
        item["source_feedback_ids"] = _load_json_list(item.get("source_feedback_ids_json"))
        item["chart_fingerprint"] = str(item.get("chart_fingerprint") or "").strip()
        item["status"] = str(item.get("status") or "draft").strip()
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        try:
            payload = json.loads(str(item.get("payload_json") or "{}"))
        except Exception:
            payload = {}
        item["payload"] = payload if isinstance(payload, dict) else {}
        for key in (
            "four_pillars_json",
            "tags_json",
            "expected_patterns_json",
            "expected_use_gods_json",
            "expected_risks_json",
            "boundary_flags_json",
            "failure_modes_json",
            "source_feedback_ids_json",
            "payload_json",
        ):
            item.pop(key, None)
        return item

    def create_practitioner_case(
        self,
        *,
        user_id: int,
        owner_role: str,
        case_key: str = "",
        case_title: str,
        description: str = "",
        birth_time_iso: str,
        gender: str,
        calendar_type: str = "solar",
        lunar_is_leap_month: bool = False,
        city_name: str = "",
        city_code: str = "",
        city_group: str = "",
        city_longitude: Any = None,
        four_pillars: Dict[str, Any] | None = None,
        luck_pillar: str = "",
        flow_pillar: str = "",
        flow_year: Any = None,
        tags: Any = None,
        expected_patterns: Any = None,
        expected_use_gods: Any = None,
        expected_risks: Any = None,
        boundary_flags: Any = None,
        failure_modes: Any = None,
        expected_notes: str = "",
        source_feedback_ids: Any = None,
        chart_fingerprint: str = "",
        status: str = "submitted",
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        role_clean = str(owner_role or "user").strip().lower() or "user"
        if role_clean not in ROLE_VALUES:
            role_clean = "user"
        title_clean = str(case_title or "").strip()
        if len(title_clean) < 2:
            raise ValueError("案例标题至少 2 个字符。")
        birth_clean = str(birth_time_iso or "").strip()
        if not birth_clean:
            raise ValueError("出生时间不能为空。")
        gender_clean = str(gender or "").strip().lower()
        if gender_clean not in GENDER_VALUES:
            raise ValueError("无效性别。")
        calendar_clean = str(calendar_type or "solar").strip().lower() or "solar"
        if calendar_clean not in CALENDAR_VALUES:
            raise ValueError("无效历法。")
        status_clean = str(status or "submitted").strip().lower() or "submitted"
        if status_clean not in PRACTITIONER_CASE_STATUS_VALUES:
            raise ValueError("无效案例状态。")
        if role_clean not in {"practitioner", "manager", "admin"} and status_clean not in {"draft", "submitted"}:
            status_clean = "submitted"
        key_clean = str(case_key or "").strip().replace(" ", "_")[:120]
        if not key_clean:
            key_clean = f"case_{secrets.token_hex(6)}"
        try:
            longitude_value = None if city_longitude in (None, "") else float(city_longitude)
        except Exception:
            longitude_value = None
        try:
            flow_year_value = None if flow_year in (None, "") else int(flow_year)
        except Exception:
            flow_year_value = None
        pillars_clean = _json_dict(four_pillars or {}, key_limit=12, value_limit=12)
        payload_obj = payload if isinstance(payload, dict) else {}
        payload_json = json.dumps(payload_obj, ensure_ascii=False, sort_keys=True, default=str)
        if len(payload_json) > 20000:
            payload_json = json.dumps({"truncated": True, "case_title": title_clean[:120]}, ensure_ascii=False)
        owner_weight = {"user": 1.0, "practitioner": 2.0, "manager": 2.2, "admin": 2.6}.get(role_clean, 1.0)
        now = _iso(_now_utc())
        values = (
            int(user_id),
            role_clean,
            owner_weight,
            key_clean,
            title_clean[:160],
            str(description or "").strip()[:1200],
            birth_clean[:80],
            gender_clean,
            calendar_clean,
            1 if bool(lunar_is_leap_month) and calendar_clean == "lunar" else 0,
            str(city_name or "").strip()[:120],
            str(city_code or "").strip()[:80],
            str(city_group or "").strip()[:80],
            longitude_value,
            json.dumps(pillars_clean, ensure_ascii=False, sort_keys=True),
            str(luck_pillar or "").strip()[:16],
            str(flow_pillar or "").strip()[:16],
            flow_year_value,
            json.dumps(_json_list(tags, limit=30), ensure_ascii=False),
            json.dumps(_json_list(expected_patterns, limit=20), ensure_ascii=False),
            json.dumps(_json_list(expected_use_gods, limit=20), ensure_ascii=False),
            json.dumps(_json_list(expected_risks, limit=20), ensure_ascii=False),
            json.dumps(_json_list(boundary_flags, limit=30), ensure_ascii=False),
            json.dumps(_json_list(failure_modes, limit=30), ensure_ascii=False),
            str(expected_notes or "").strip()[:1600],
            json.dumps(_json_list(source_feedback_ids, limit=80), ensure_ascii=False),
            str(chart_fingerprint or "").strip()[:160],
            status_clean,
            payload_json,
            now,
            now,
        )
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO practitioner_cases (
                        user_id,
                        owner_role,
                        owner_weight,
                        case_key,
                        case_title,
                        description,
                        birth_time_iso,
                        gender,
                        calendar_type,
                        lunar_is_leap_month,
                        city_name,
                        city_code,
                        city_group,
                        city_longitude,
                        four_pillars_json,
                        luck_pillar,
                        flow_pillar,
                        flow_year,
                        tags_json,
                        expected_patterns_json,
                        expected_use_gods_json,
                        expected_risks_json,
                        boundary_flags_json,
                        failure_modes_json,
                        expected_notes,
                        source_feedback_ids_json,
                        chart_fingerprint,
                        status,
                        payload_json,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
                case_id = int(cursor.lastrowid)
                row = conn.execute("SELECT * FROM practitioner_cases WHERE id = ?", (case_id,)).fetchone()
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("同一账号下案例 key 已存在。") from exc
        item = self._clean_practitioner_case_row(row)
        if not item:
            raise ValueError("案例记录失败。")
        return item

    def list_practitioner_cases(
        self,
        *,
        user_id: int,
        owner_role: str,
        scope: str = "own",
        case_key: str = "",
        status: str = "",
        chart_fingerprint: str = "",
        limit: int = 80,
    ) -> List[Dict[str, Any]]:
        role_clean = str(owner_role or "user").strip().lower()
        can_view_all = role_clean in {"manager", "admin"} and str(scope or "").strip().lower() == "all"
        where: List[str] = []
        params: List[Any] = []
        if not can_view_all:
            where.append("pc.user_id = ?")
            params.append(int(user_id))
        key_clean = str(case_key or "").strip()
        status_clean = str(status or "").strip().lower()
        fingerprint_clean = str(chart_fingerprint or "").strip()
        if key_clean:
            where.append("pc.case_key = ?")
            params.append(key_clean)
        if status_clean:
            where.append("pc.status = ?")
            params.append(status_clean)
        if fingerprint_clean:
            where.append("pc.chart_fingerprint = ?")
            params.append(fingerprint_clean)
        sql = "SELECT pc.*, u.username AS owner_username, u.display_name AS owner_display_name FROM practitioner_cases pc JOIN auth_users u ON u.id = pc.user_id"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY pc.updated_at DESC, pc.id DESC LIMIT ?"
        params.append(max(1, min(300, int(limit or 80))))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        out: List[Dict[str, Any]] = []
        for row in rows:
            item = self._clean_practitioner_case_row(row)
            if not item:
                continue
            row_dict = dict(row)
            item["owner_username"] = str(row_dict.get("owner_username") or "").strip()
            item["owner_display_name"] = str(row_dict.get("owner_display_name") or "").strip()
            out.append(item)
        return out

    def _clean_learning_review_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["reviewer_user_id"] = int(item.get("reviewer_user_id") or 0)
        item["candidate_id"] = str(item.get("candidate_id") or "").strip()
        item["parameter_family"] = str(item.get("parameter_family") or "").strip()
        item["reviewer_role"] = str(item.get("reviewer_role") or "").strip().lower()
        item["status"] = str(item.get("status") or "").strip().lower()
        item["reviewer_note"] = str(item.get("reviewer_note") or "").strip()
        item["safety_gate"] = str(item.get("safety_gate") or "").strip()
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        try:
            snapshot = json.loads(str(item.get("candidate_snapshot_json") or "{}"))
        except Exception:
            snapshot = {}
        item["candidate_snapshot"] = snapshot if isinstance(snapshot, dict) else {}
        item.pop("candidate_snapshot_json", None)
        item["reviewer_username"] = str(item.get("reviewer_username") or "").strip()
        item["reviewer_display_name"] = str(item.get("reviewer_display_name") or "").strip()
        return item

    def create_practitioner_learning_review(
        self,
        *,
        reviewer_user_id: int,
        reviewer_role: str,
        candidate_id: str,
        parameter_family: str,
        status: str,
        reviewer_note: str = "",
        safety_gate: str = "manual_review_required",
        candidate_snapshot: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        role_clean = str(reviewer_role or "user").strip().lower() or "user"
        if role_clean not in {"manager", "admin"}:
            raise ValueError("只有 manager/admin 可以审计学习候选。")
        candidate_clean = str(candidate_id or "").strip()[:240]
        family_clean = str(parameter_family or "").strip()[:160]
        if not candidate_clean or not family_clean:
            raise ValueError("学习候选 ID 与参数族不能为空。")
        status_clean = str(status or "").strip().lower()
        if status_clean not in LEARNING_REVIEW_STATUS_VALUES:
            raise ValueError("无效学习候选审计状态。")
        note_clean = str(reviewer_note or "").strip()
        if len(note_clean) > 1200:
            raise ValueError("审计备注最多 1200 个字符。")
        snapshot_obj = candidate_snapshot if isinstance(candidate_snapshot, dict) else {}
        snapshot_json = json.dumps(snapshot_obj, ensure_ascii=False, sort_keys=True, default=str)
        if len(snapshot_json) > 16000:
            snapshot_json = json.dumps(
                {
                    "truncated": True,
                    "candidate_id": candidate_clean,
                    "parameter_family": family_clean,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        now = _iso(_now_utc())
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO practitioner_learning_reviews (
                    candidate_id,
                    parameter_family,
                    reviewer_user_id,
                    reviewer_role,
                    status,
                    reviewer_note,
                    safety_gate,
                    candidate_snapshot_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_clean,
                    family_clean,
                    int(reviewer_user_id),
                    role_clean,
                    status_clean,
                    note_clean,
                    str(safety_gate or "manual_review_required").strip()[:80],
                    snapshot_json,
                    now,
                    now,
                ),
            )
            review_id = int(cursor.lastrowid)
            row = conn.execute(
                """
                SELECT lr.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name
                FROM practitioner_learning_reviews lr
                JOIN auth_users u ON u.id = lr.reviewer_user_id
                WHERE lr.id = ?
                """,
                (review_id,),
            ).fetchone()
            conn.commit()
        review = self._clean_learning_review_row(row)
        if not review:
            raise ValueError("学习候选审计记录失败。")
        return review

    def list_practitioner_learning_reviews(
        self,
        *,
        candidate_id: str = "",
        status: str = "",
        limit: int = 80,
    ) -> List[Dict[str, Any]]:
        where: List[str] = []
        params: List[Any] = []
        candidate_clean = str(candidate_id or "").strip()
        status_clean = str(status or "").strip().lower()
        if candidate_clean:
            where.append("lr.candidate_id = ?")
            params.append(candidate_clean)
        if status_clean:
            where.append("lr.status = ?")
            params.append(status_clean)
        sql = """
            SELECT lr.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name
            FROM practitioner_learning_reviews lr
            JOIN auth_users u ON u.id = lr.reviewer_user_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY lr.created_at DESC, lr.id DESC LIMIT ?"
        params.append(max(1, min(300, int(limit or 80))))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [item for row in rows if (item := self._clean_learning_review_row(row))]

    def _clean_learning_release_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["reviewer_user_id"] = int(item.get("reviewer_user_id") or 0)
        item["experiment_id"] = str(item.get("experiment_id") or "").strip()
        item["candidate_id"] = str(item.get("candidate_id") or "").strip()
        item["parameter_family"] = str(item.get("parameter_family") or "").strip()
        item["reviewer_role"] = str(item.get("reviewer_role") or "").strip().lower()
        item["status"] = str(item.get("status") or "").strip().lower()
        item["release_summary"] = str(item.get("release_summary") or "").strip()
        item["test_report"] = str(item.get("test_report") or "").strip()
        item["rollback_plan"] = str(item.get("rollback_plan") or "").strip()
        item["applied"] = bool(item.get("applied"))
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        try:
            snapshot = json.loads(str(item.get("experiment_snapshot_json") or "{}"))
        except Exception:
            snapshot = {}
        item["experiment_snapshot"] = snapshot if isinstance(snapshot, dict) else {}
        item.pop("experiment_snapshot_json", None)
        item["reviewer_username"] = str(item.get("reviewer_username") or "").strip()
        item["reviewer_display_name"] = str(item.get("reviewer_display_name") or "").strip()
        return item

    def create_practitioner_learning_release(
        self,
        *,
        reviewer_user_id: int,
        reviewer_role: str,
        experiment_id: str,
        candidate_id: str,
        parameter_family: str,
        status: str,
        release_summary: str,
        test_report: str,
        rollback_plan: str,
        experiment_snapshot: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        role_clean = str(reviewer_role or "user").strip().lower() or "user"
        if role_clean != "admin":
            raise ValueError("只有 admin 可以记录学习发布审批。")
        status_clean = str(status or "").strip().lower()
        if status_clean not in LEARNING_RELEASE_STATUS_VALUES:
            raise ValueError("无效学习发布状态。")
        experiment_clean = str(experiment_id or "").strip()[:240]
        candidate_clean = str(candidate_id or "").strip()[:240]
        family_clean = str(parameter_family or "").strip()[:160]
        summary_clean = str(release_summary or "").strip()
        test_clean = str(test_report or "").strip()
        rollback_clean = str(rollback_plan or "").strip()
        if not experiment_clean or not candidate_clean or not family_clean:
            raise ValueError("实验 ID、候选 ID 与参数族不能为空。")
        if status_clean == "approved" and (not test_clean or not rollback_clean):
            raise ValueError("批准发布必须包含测试报告和回滚方案。")
        if len(summary_clean) > 1200 or len(test_clean) > 2000 or len(rollback_clean) > 1600:
            raise ValueError("发布记录字段过长。")
        snapshot_obj = experiment_snapshot if isinstance(experiment_snapshot, dict) else {}
        snapshot_json = json.dumps(snapshot_obj, ensure_ascii=False, sort_keys=True, default=str)
        if len(snapshot_json) > 18000:
            snapshot_json = json.dumps(
                {"truncated": True, "experiment_id": experiment_clean, "candidate_id": candidate_clean},
                ensure_ascii=False,
                sort_keys=True,
            )
        now = _iso(_now_utc())
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO practitioner_learning_releases (
                    experiment_id,
                    candidate_id,
                    parameter_family,
                    reviewer_user_id,
                    reviewer_role,
                    status,
                    release_summary,
                    test_report,
                    rollback_plan,
                    experiment_snapshot_json,
                    applied,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    experiment_clean,
                    candidate_clean,
                    family_clean,
                    int(reviewer_user_id),
                    role_clean,
                    status_clean,
                    summary_clean,
                    test_clean,
                    rollback_clean,
                    snapshot_json,
                    now,
                    now,
                ),
            )
            release_id = int(cursor.lastrowid)
            row = conn.execute(
                """
                SELECT lr.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name
                FROM practitioner_learning_releases lr
                JOIN auth_users u ON u.id = lr.reviewer_user_id
                WHERE lr.id = ?
                """,
                (release_id,),
            ).fetchone()
            conn.commit()
        release = self._clean_learning_release_row(row)
        if not release:
            raise ValueError("学习发布记录失败。")
        return release

    def list_practitioner_learning_releases(
        self,
        *,
        experiment_id: str = "",
        status: str = "",
        limit: int = 80,
    ) -> List[Dict[str, Any]]:
        where: List[str] = []
        params: List[Any] = []
        experiment_clean = str(experiment_id or "").strip()
        status_clean = str(status or "").strip().lower()
        if experiment_clean:
            where.append("lr.experiment_id = ?")
            params.append(experiment_clean)
        if status_clean:
            where.append("lr.status = ?")
            params.append(status_clean)
        sql = """
            SELECT lr.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name
            FROM practitioner_learning_releases lr
            JOIN auth_users u ON u.id = lr.reviewer_user_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY lr.created_at DESC, lr.id DESC LIMIT ?"
        params.append(max(1, min(300, int(limit or 80))))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [item for row in rows if (item := self._clean_learning_release_row(row))]

    def _clean_learning_scorecard_row(self, row: sqlite3.Row | Dict[str, Any] | None) -> Dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["id"] = int(item.get("id") or 0)
        item["reviewer_user_id"] = int(item.get("reviewer_user_id") or 0)
        item["experiment_id"] = str(item.get("experiment_id") or "").strip()
        item["candidate_id"] = str(item.get("candidate_id") or "").strip()
        item["parameter_family"] = str(item.get("parameter_family") or "").strip()
        item["reviewer_role"] = str(item.get("reviewer_role") or "").strip().lower()
        item["synthetic_passed"] = bool(item.get("synthetic_passed"))
        item["practitioner_passed"] = bool(item.get("practitioner_passed"))
        item["improvement_count"] = int(item.get("improvement_count") or 0)
        item["regression_count"] = int(item.get("regression_count") or 0)
        item["verdict"] = str(item.get("verdict") or "").strip().lower()
        item["summary"] = str(item.get("summary") or "").strip()
        item["created_at"] = str(item.get("created_at") or "").strip()
        item["updated_at"] = str(item.get("updated_at") or "").strip()
        try:
            payload = json.loads(str(item.get("payload_json") or "{}"))
        except Exception:
            payload = {}
        item["payload"] = payload if isinstance(payload, dict) else {}
        item.pop("payload_json", None)
        item["reviewer_username"] = str(item.get("reviewer_username") or "").strip()
        item["reviewer_display_name"] = str(item.get("reviewer_display_name") or "").strip()
        return item

    def create_practitioner_learning_scorecard(
        self,
        *,
        reviewer_user_id: int,
        reviewer_role: str,
        experiment_id: str,
        candidate_id: str,
        parameter_family: str,
        synthetic_passed: bool,
        practitioner_passed: bool,
        improvement_count: int = 0,
        regression_count: int = 0,
        verdict: str,
        summary: str,
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        role_clean = str(reviewer_role or "user").strip().lower() or "user"
        if role_clean not in {"manager", "admin"}:
            raise ValueError("只有 manager/admin 可以记录学习实验评分。")
        verdict_clean = str(verdict or "").strip().lower()
        if verdict_clean not in LEARNING_SCORECARD_VERDICT_VALUES:
            raise ValueError("无效学习实验结论。")
        experiment_clean = str(experiment_id or "").strip()[:240]
        candidate_clean = str(candidate_id or "").strip()[:240]
        family_clean = str(parameter_family or "").strip()[:160]
        summary_clean = str(summary or "").strip()
        if not experiment_clean or not candidate_clean or not family_clean:
            raise ValueError("实验 ID、候选 ID 与参数族不能为空。")
        if not summary_clean:
            raise ValueError("评分摘要不能为空。")
        if verdict_clean == "promote" and (not synthetic_passed or not practitioner_passed or int(regression_count or 0) > 0):
            raise ValueError("建议发布必须同时通过 synthetic/practitioner benchmark 且无退化。")
        payload_obj = payload if isinstance(payload, dict) else {}
        payload_json = json.dumps(payload_obj, ensure_ascii=False, sort_keys=True, default=str)
        if len(payload_json) > 16000:
            payload_json = json.dumps({"truncated": True, "experiment_id": experiment_clean}, ensure_ascii=False)
        now = _iso(_now_utc())
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO practitioner_learning_scorecards (
                    experiment_id,
                    candidate_id,
                    parameter_family,
                    reviewer_user_id,
                    reviewer_role,
                    synthetic_passed,
                    practitioner_passed,
                    improvement_count,
                    regression_count,
                    verdict,
                    summary,
                    payload_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_clean,
                    candidate_clean,
                    family_clean,
                    int(reviewer_user_id),
                    role_clean,
                    1 if synthetic_passed else 0,
                    1 if practitioner_passed else 0,
                    max(0, int(improvement_count or 0)),
                    max(0, int(regression_count or 0)),
                    verdict_clean,
                    summary_clean[:1600],
                    payload_json,
                    now,
                    now,
                ),
            )
            scorecard_id = int(cursor.lastrowid)
            row = conn.execute(
                """
                SELECT sc.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name
                FROM practitioner_learning_scorecards sc
                JOIN auth_users u ON u.id = sc.reviewer_user_id
                WHERE sc.id = ?
                """,
                (scorecard_id,),
            ).fetchone()
            conn.commit()
        scorecard = self._clean_learning_scorecard_row(row)
        if not scorecard:
            raise ValueError("学习实验评分记录失败。")
        return scorecard

    def list_practitioner_learning_scorecards(
        self,
        *,
        experiment_id: str = "",
        verdict: str = "",
        limit: int = 80,
    ) -> List[Dict[str, Any]]:
        where: List[str] = []
        params: List[Any] = []
        experiment_clean = str(experiment_id or "").strip()
        verdict_clean = str(verdict or "").strip().lower()
        if experiment_clean:
            where.append("sc.experiment_id = ?")
            params.append(experiment_clean)
        if verdict_clean:
            where.append("sc.verdict = ?")
            params.append(verdict_clean)
        sql = """
            SELECT sc.*, u.username AS reviewer_username, u.display_name AS reviewer_display_name
            FROM practitioner_learning_scorecards sc
            JOIN auth_users u ON u.id = sc.reviewer_user_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY sc.created_at DESC, sc.id DESC LIMIT ?"
        params.append(max(1, min(300, int(limit or 80))))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [item for row in rows if (item := self._clean_learning_scorecard_row(row))]

    def has_promote_learning_scorecard(self, *, experiment_id: str) -> bool:
        experiment_clean = str(experiment_id or "").strip()
        if not experiment_clean:
            return False
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM practitioner_learning_scorecards
                WHERE experiment_id = ?
                  AND verdict = 'promote'
                  AND synthetic_passed = 1
                  AND practitioner_passed = 1
                  AND regression_count = 0
                """,
                (experiment_clean,),
            ).fetchone()
        return int(row["c"] if row else 0) > 0


auth_storage = V17AuthDB()
