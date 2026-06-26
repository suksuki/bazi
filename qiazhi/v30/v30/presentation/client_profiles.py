from __future__ import annotations

from v30.contracts import ClientKey, ClientProfile

CLIENT_PROFILES: dict[ClientKey, ClientProfile] = {
    "web": ClientProfile(
        client="web",
        density="standard",
        max_questions=4,
        show_reasons=True,
        show_diagnostics=False,
        actions=["submit_answer"],
    ),
    "mobile": ClientProfile(
        client="mobile",
        density="compact",
        max_questions=3,
        show_reasons=False,
        show_diagnostics=False,
        actions=["submit_answer"],
    ),
    "admin": ClientProfile(
        client="admin",
        density="diagnostic",
        max_questions=8,
        show_reasons=True,
        show_diagnostics=True,
        actions=["submit_answer", "run_training", "open_trace"],
    ),
    "lab": ClientProfile(
        client="lab",
        density="diagnostic",
        max_questions=8,
        show_reasons=True,
        show_diagnostics=True,
        actions=["submit_answer", "run_training", "open_trace"],
    ),
}


def client_profile(client: str) -> ClientProfile:
    return CLIENT_PROFILES.get(client, CLIENT_PROFILES["web"])  # type: ignore[arg-type]
