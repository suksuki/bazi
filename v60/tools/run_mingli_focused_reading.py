from __future__ import annotations

import argparse
import time

from abu_v60.db import engine
from abu_v60.mingli.focused_pass_service import MingliFocusedPassService
from abu_v60.mingli.focused_reading_contracts import MINGLI_FOCUS_ORDER
from abu_v60.mingli.focused_reading_service import MingliFocusedReadingService
from abu_v60.provenance import canonical_json
from sqlalchemy import text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the product focused-reading path on synthetic data only."
    )
    parser.add_argument("--case-ref")
    parser.add_argument("--focus", choices=MINGLI_FOCUS_ORDER)
    args = parser.parse_args()
    fixture = _synthetic_fixture(case_ref=args.case_ref)
    if args.focus is not None:
        started = time.monotonic()
        record = MingliFocusedPassService(engine).generate(
            requester_account_ref=fixture["owner_account_ref"],
            case_ref=fixture["case_ref"],
            expected_reading_ref=fixture["reading_ref"],
            expected_reading_hash=fixture["reading_hash"],
            focus=args.focus,
        )
        wall_duration_ms = round((time.monotonic() - started) * 1000)
        result = record.pass_result
        print(
            canonical_json(
                {
                    "case_ref": fixture["case_ref"],
                    "record_ref": record.record_ref,
                    "focus": result.focus,
                    "provider_profile_hash": record.provider_profile_hash,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "duration_ms": result.duration_ms,
                    "wall_duration_ms": wall_duration_ms,
                    "cache_replay": wall_duration_ms < 1000,
                    "normalization_codes": result.normalization_codes,
                    "normalized_text": result.normalized_text,
                }
            )
        )
        return
    started = time.monotonic()
    reading = MingliFocusedReadingService(engine).generate(
        requester_account_ref=fixture["owner_account_ref"],
        case_ref=fixture["case_ref"],
        expected_reading_ref=fixture["reading_ref"],
        expected_reading_hash=fixture["reading_hash"],
    )
    wall_duration_ms = round((time.monotonic() - started) * 1000)
    print(
        canonical_json(
            {
                "case_ref": fixture["case_ref"],
                "focused_reading_ref": reading.focused_reading_ref,
                "model_ref": reading.model_ref,
                "provider_profile_hash": reading.provider_profile_hash,
                "input_tokens": reading.input_tokens,
                "output_tokens": reading.output_tokens,
                "total_tokens": reading.total_tokens,
                "model_duration_ms": reading.duration_ms,
                "wall_duration_ms": wall_duration_ms,
                "cache_replay": wall_duration_ms < 1000,
                "passes": [
                    {
                        "focus": item.focus,
                        "duration_ms": item.duration_ms,
                        "input_tokens": item.input_tokens,
                        "output_tokens": item.output_tokens,
                        "normalization_codes": item.normalization_codes,
                        "normalized_text": item.normalized_text,
                    }
                    for item in reading.passes
                ],
            }
        )
    )


def _synthetic_fixture(*, case_ref: str | None) -> dict[str, str]:
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT c.owner_account_ref, c.case_ref,
                           r.reading_ref, r.reading_hash
                    FROM mingli.cases AS c
                    JOIN LATERAL (
                        SELECT reading_ref, reading_hash
                        FROM mingli.readings
                        WHERE case_ref = c.case_ref
                        ORDER BY created_at DESC, reading_ref DESC
                        LIMIT 1
                    ) AS r ON true
                    WHERE c.subject_kind = 'CANONICAL_SYNTHETIC'
                      AND c.status = 'ACTIVE'
                      AND (
                          CAST(:case_ref AS varchar) IS NULL
                          OR c.case_ref = CAST(:case_ref AS varchar)
                      )
                    ORDER BY EXISTS (
                        SELECT 1 FROM mingli.focused_readings AS f
                        WHERE f.case_ref = c.case_ref
                          AND f.reading_ref = r.reading_ref
                    ), c.case_ref
                    LIMIT 1
                    """
                ),
                {"case_ref": case_ref},
            )
            .mappings()
            .one_or_none()
        )
    if row is None:
        raise SystemExit("synthetic_focused_reading_fixture_not_found")
    return {key: str(value) for key, value in row.items()}


if __name__ == "__main__":
    main()
