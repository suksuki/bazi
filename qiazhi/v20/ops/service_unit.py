from __future__ import annotations

from pathlib import Path

from v20.ops.config import load_runtime_config_from_env
from v20.ops.schema import ServerProfile

QIAZHI_ROOT = Path(__file__).resolve().parents[2]


def service_unit_manifest(profile_name: str = "") -> dict[str, object]:
    config = load_runtime_config_from_env()
    profile = config.profile(profile_name or config.active_profile)
    unit = _systemd_unit(profile) if profile.platform == "linux" else _macos_launchd_plist(profile)
    service_script = "./v20/scripts/service_linux.sh" if profile.platform == "linux" else "./v20/scripts/service_macos.sh"
    foreground_script = "./v20/scripts/start_linux.sh" if profile.platform == "linux" else "./v20/scripts/start_macos.sh"
    return {
        "version": "v20.service_unit_manifest.v1",
        "profile": profile.to_dict(),
        "unit_type": "systemd" if profile.platform == "linux" else "launchd",
        "unit": unit,
        "service_script": service_script,
        "foreground_script": foreground_script,
        "background_commands": {
            "start": f"{service_script} start",
            "stop": f"{service_script} stop",
            "restart": f"{service_script} restart",
            "status": f"{service_script} status",
            "logs": f"{service_script} logs",
        },
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
            f"WorkingDirectory={QIAZHI_ROOT}",
            f"Environment=V20_ENV={profile.name}",
            f"Environment=V20_HOST={profile.bind_host}",
            f"Environment=V20_PORT={profile.port}",
            f"Environment=PYTHONPATH={QIAZHI_ROOT}",
            f"ExecStart={QIAZHI_ROOT}/v20/scripts/start_linux.sh",
            "Restart=on-failure",
            "RestartSec=3",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
        ]
    )


def _macos_launchd_plist(profile: ServerProfile) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
            '<plist version="1.0">',
            "<dict>",
            "  <key>Label</key><string>com.qiazhi.v20.local</string>",
            f"  <key>WorkingDirectory</key><string>{QIAZHI_ROOT}</string>",
            "  <key>ProgramArguments</key>",
            "  <array>",
            f"    <string>{QIAZHI_ROOT}/v20/scripts/start_macos.sh</string>",
            "  </array>",
            "  <key>EnvironmentVariables</key>",
            "  <dict>",
            f"    <key>V20_ENV</key><string>{profile.name}</string>",
            f"    <key>V20_HOST</key><string>{profile.bind_host}</string>",
            f"    <key>V20_PORT</key><string>{profile.port}</string>",
            "  </dict>",
            f"  <key>StandardOutPath</key><string>{QIAZHI_ROOT}/v20/.runtime/local/service_9020.log</string>",
            f"  <key>StandardErrorPath</key><string>{QIAZHI_ROOT}/v20/.runtime/local/service_9020.log</string>",
            "  <key>RunAtLoad</key><true/>",
            "  <key>KeepAlive</key><true/>",
            "</dict>",
            "</plist>",
        ]
    )
