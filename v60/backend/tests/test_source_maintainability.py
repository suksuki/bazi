from __future__ import annotations

import inspect
from pathlib import Path

from abu_v60.architecture.source_budget import (
    audit_runtime_source_budgets,
    format_source_budget_violations,
)
from abu_v60.dream.outcomes import DreamOutcomeCoordinator
from abu_v60.dream.persistence import DreamRepository
from abu_v60.dream.projection import DreamSnapshotProjector
from abu_v60.dream.service import DreamService


def test_runtime_source_files_respect_maintainability_budget() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    violations = audit_runtime_source_budgets(repository_root)

    assert not violations, format_source_budget_violations(violations)


def test_dream_runtime_uses_separate_command_read_and_persistence_owners() -> None:
    service_methods = DreamService.__dict__
    snapshot_source = inspect.getsource(DreamService.snapshot)

    assert "_current_encounter" not in service_methods
    assert "_write_encounter_state" not in service_methods
    assert "_build_reveal" not in service_methods
    assert "_snapshot_projector.snapshot" in snapshot_source
    assert DreamSnapshotProjector.__module__.endswith(".dream.projection")
    assert DreamRepository.__module__.endswith(".dream.persistence")
    assert DreamOutcomeCoordinator.__module__.endswith(".dream.outcomes")
