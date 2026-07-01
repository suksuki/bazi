from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.contracts import (
    ClientContext,
    EngineCapability,
    EngineContext,
    LocaleContext,
    RuntimeRequest,
    SurfaceBundle,
    Topic,
    TrainingLabelEvent,
)
from v40.contracts.base import EngineKey
from v40.contracts.context import RuntimeContext, default_client_context, default_locale_context, default_role_context
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue
from v40.project import build_horizontal_runtime_context_status


def test_runtime_request_builds_horizontal_context_from_legacy_fields() -> None:
    request = RuntimeRequest(
        request_id="req-horizontal",
        reading_id="reading-horizontal",
        role_key="practitioner",
        locale="ko",
        client="mobile",
    )

    assert request.runtime_context.locale_context.locale == "ko-KR"
    assert request.runtime_context.role_context.can_submit_calibration is True
    assert request.runtime_context.client_context.device_type == "mobile"
    assert request.runtime_context.client_context.supports_side_panel is False
    assert EngineKey.BAZI in request.runtime_context.engine_context.enabled_engines


def test_context_boundaries_prevent_ui_and_engine_drift() -> None:
    with pytest.raises(ValueError, match="mobile ClientContext cannot require side panel"):
        ClientContext(client="mobile", device_type="mobile", viewport="narrow", supports_side_panel=True)

    with pytest.raises(ValueError, match="cannot directly generate verdict"):
        EngineCapability(engine=EngineKey.BAZI, can_directly_generate_verdict=True)

    with pytest.raises(ValueError, match="Ziwei engine weight must remain sidecar"):
        EngineContext(
            enabled_engines=[EngineKey.BAZI, EngineKey.ZIWEI],
            engine_weights={EngineKey.BAZI: 1.0, EngineKey.ZIWEI: 0.3},
        )

    with pytest.raises(ValueError, match="hidden_admin_refs require admin or lab role"):
        SurfaceBundle(
            reading_id="r1",
            role_key="user",
            hidden_admin_refs={"trace": "policy_key"},
        )


def test_training_label_records_locale_role_client_and_engine_source() -> None:
    label = TrainingLabelEvent(
        event_id="label-horizontal",
        reading_id="r1",
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.BRANCH,
        target_ids=["branch-wealth"],
        label=LabelValue.SUPPORTS,
        created_by_role="practitioner",
        locale="en-US",
        client="desktop",
        engine_source=EngineKey.BAZI,
        locale_context=LocaleContext(locale="en-US", user_language="en-US", output_language="en-US"),
        role_context=default_role_context("practitioner"),
        client_context=default_client_context("desktop"),
        engine_context=EngineContext(enabled_engines=[EngineKey.BAZI]),
        local_only=False,
        requires_batch_review=True,
    )

    assert label.locale == "en-US"
    assert label.role_context is not None
    assert label.role_context.can_submit_calibration is True
    assert label.client_context is not None
    assert label.client_context.device_type == "desktop"
    assert label.engine_source == EngineKey.BAZI


def test_horizontal_runtime_context_status_api_and_docs() -> None:
    status = build_horizontal_runtime_context_status()

    assert status["boundary"] == "horizontal_runtime_contexts_are_system_dimensions_not_ui_afterthoughts"
    assert len(status["contexts"]) == 4
    assert "locale" in status["training_dimensions"]
    assert "engine_source" in status["training_dimensions"]
    assert status["term_dictionary"]["entries"][0]["canonical_key"] == "shi_shang"
    assert all(row["can_directly_generate_verdict"] is False for row in status["engine_capabilities"])

    response = TestClient(create_app()).get(f"{API_PREFIX}/project/horizontal-runtime-context")
    assert response.status_code == 200
    body = response.json()
    assert body["status"]["version"] == "v40.horizontal_runtime_context_status.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False

    doc = Path("qiazhi/v40/docs/V40_RC2_HORIZONTAL_RUNTIME_CONTEXT.md").read_text(encoding="utf-8")
    assert "V40 是一个多语言、多角色、多终端、多引擎的可训练命理运行时" in doc
    assert "Admin 已经独立为新的前台服务和端口" in doc


def test_admin_console_exposes_horizontal_runtime_context_panel() -> None:
    page = TestClient(create_admin_app()).get(ADMIN_PREFIX)

    assert page.status_code == 200
    assert "Runtime Context" in page.text
    assert "/admin/v40/api/horizontal-runtime-context" in page.text
