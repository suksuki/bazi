from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from v17_rebirth.paths import RUNTIME_DIR

ROLE_VALUES = {"admin", "manager", "user"}
GENDER_VALUES = {"male", "female"}
CALENDAR_VALUES = {"solar", "lunar"}
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
        final_role = requested_role if requested_role in {"manager", "user"} else "user"
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
                    ) AS latest_seen_at
                FROM auth_users u
                ORDER BY id ASC
                """
            ).fetchall()
        return [self._clean_user_row(row) or {} for row in rows]

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
                    city_name,
                    city_code,
                    city_group,
                    city_longitude,
                    created_at,
                    updated_at,
                    last_used_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    profile_name_clean,
                    birth_time_clean,
                    gender_clean,
                    calendar_clean,
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
            row = conn.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
            conn.commit()
        updated = self._clean_user_row(row)
        if not updated:
            raise ValueError("角色更新失败。")
        return updated


auth_storage = V17AuthDB()
