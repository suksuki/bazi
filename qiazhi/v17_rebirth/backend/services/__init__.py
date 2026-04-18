__all__ = ["VerdictOrchestrator"]


def __getattr__(name: str):
    if name == "VerdictOrchestrator":
        from .verdict_orchestrator import VerdictOrchestrator

        return VerdictOrchestrator
    raise AttributeError(name)
