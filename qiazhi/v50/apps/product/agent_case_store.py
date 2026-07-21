from __future__ import annotations

import os

from product.agent_case_store_contracts import AgentCaseStore, LegacyFormalWriteBlocked
from product.agent_case_store_memory import MemoryAgentCaseStore
from product.agent_case_store_postgres import PostgresAgentCaseStore


def build_agent_case_store() -> AgentCaseStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return PostgresAgentCaseStore(database_url) if database_url else MemoryAgentCaseStore()


__all__ = [
    "AgentCaseStore",
    "LegacyFormalWriteBlocked",
    "MemoryAgentCaseStore",
    "PostgresAgentCaseStore",
    "build_agent_case_store",
]
