"""领域级可观测异常（供 API 层选择性拦截）。"""


class DatabaseFetchError(Exception):
    """读取持久化层失败（如共识历史）；不应被静默吞掉。"""
