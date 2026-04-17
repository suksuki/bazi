"""
回归：钉住 physics SNAPSHOT 时须保留环形缓冲尾部 N 帧。

前端 `useV17WebStream` 曾误用 `slice(0, cap-1)` 丢掉最新 NARRATOR；
正确为 `slice(-(NDJSON_TAIL_CAP - 1))`。此处用纯 Python 复刻该不变量。
"""
from __future__ import annotations

import pytest

NDJSON_TAIL_CAP = 120


def _pin_reconcile(local_frames: list[int], pinned: int | None) -> list[int]:
    if pinned is not None and pinned not in local_frames:
        return [pinned, *local_frames[-(NDJSON_TAIL_CAP - 1) :]]
    return local_frames


@pytest.mark.regression
def test_pin_keeps_latest_tail_not_prefix_slice() -> None:
    """错误实现会丢掉列表最后一项（最新增量）。"""
    pinned = 0
    # 已满 cap，且 pinned 被挤出
    local = [1] * (NDJSON_TAIL_CAP - 1) + [999]
    assert pinned not in local
    fixed = _pin_reconcile(local, pinned)
    assert fixed[0] == pinned
    assert fixed[-1] == 999
    wrong = [pinned, *local[: NDJSON_TAIL_CAP - 1]]
    assert wrong[-1] != 999
