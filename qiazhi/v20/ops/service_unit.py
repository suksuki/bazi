from __future__ import annotations

from v20.ops.config import load_runtime_config_from_env
from v20.ops.schema import ServerProfile


def service_unit_manifest(profile_name: str = "") -> dict[str, object]:
    config = load_runtime_config_from_env()
    profile = config.profile(profile_name or config.active_profile)
    unit = _systemd_unit(profile) if profile.platform == "linux" else _macos_launch_command(profile)
    return {
        "version": "v20.service_unit_manifest.v1",
        "profile": profile.to_dict(),
        "unit_type": "systemd" if profile.platform == "linux" else "foreground_command",
        "unit": unit,
        "health_check": f"{profile.base_url()}/health",
        "ui_url": f"{profile.base_url()}/v20/ui/",
        "runtime_mutation": False,
        "guardrails": [
            "SERVICE_UNIT_MANIFEST_ONLY",
            "NO_PROCESS_STARTED",
            "NO_SECRET_VALUES_RENDERED",
            "REVIEW_BEFORE_REMOTE_INSTALL",
        ],
    }


def _systemd_unit(profile: ServerProfile) -> str:
    return "\n".join(
        [
            "[Unit]",
            "Description=Qiazhi V20 Bazi Measurement Service",
            "After=network.target",
            "",
            "[Service]",
            "Type=simple",
            f"WorkingDirectory=%h/DEV/AIProjects/bazi/qiazhi",
            f"Environment=V20_ENV={profile.name}",
            f"Environment=V20_HOST={profile.bind_host}",
            f"Environment=V20_PORT={profile.port}",
            "Environment=PYTHONPATH=%h/DEV/AIProjects/bazi/qiazhi",
            "ExecStart=/usr/bin/env python3.12 -m uvicorn v20.server:app --host ${V20_HOST} --port ${V20_PORT}",
            "Restart=on-failure",
            "RestartSec=3",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
        ]
    )


def _macos_launch_command(profile: ServerProfile) -> str:
    return " ".join(
        [
            f"V20_ENV={profile.name}",
            f"V20_HOST={profile.bind_host}",
            f"V20_PORT={profile.port}",
            "./v20/scripts/start_macos.sh",
        ]
    )
