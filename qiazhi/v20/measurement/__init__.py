from __future__ import annotations

__all__ = ["MeasurementReport", "MeasurementTopic", "bazi_alignment_manifest", "build_measurement_report"]


def __getattr__(name: str):  # noqa: ANN201
    if name == "bazi_alignment_manifest":
        from v20.measurement.domain_alignment import bazi_alignment_manifest

        return bazi_alignment_manifest
    if name == "build_measurement_report":
        from v20.measurement.report import build_measurement_report

        return build_measurement_report
    if name in {"MeasurementReport", "MeasurementTopic"}:
        from v20.measurement.schema import MeasurementReport, MeasurementTopic

        return {"MeasurementReport": MeasurementReport, "MeasurementTopic": MeasurementTopic}[name]
    raise AttributeError(name)
