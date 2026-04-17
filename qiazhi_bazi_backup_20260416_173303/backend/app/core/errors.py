"""领域级可观测异常（供 API 层选择性拦截）。"""


class DatabaseFetchError(Exception):
    """读取持久化层失败（如共识历史）；不应被静默吞掉。"""


class V12SchemaViolationError(ValueError):
    """V12 schema 断裂（禁止前后端静默回退）。"""

    def __init__(self, message: str, pulse_id: str = "pulse-unknown") -> None:
        super().__init__(message)
        self.pulse_id = str(pulse_id or "pulse-unknown")
