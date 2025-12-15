"""
scripts/init_production_monitors.py
-----------------------------------
V9.6 部署前置脚本：初始化日志、记录性能基线、清空缓存。
"""

import logging
import logging.config
import os
import time

from controllers.bazi_controller import BaziController


def ensure_log_dir(path: str = "logs") -> str:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


def setup_structured_logging(log_path: str) -> None:
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "json": {
                "format": (
                    '{"level":"%(levelname)s","ts":"%(asctime)s",'
                    '"name":"%(name)s","msg":"%(message)s"}'
                )
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": log_path,
                "formatter": "json",
                "encoding": "utf-8",
                "mode": "a",
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["file", "console"],
        },
    })


def clear_controller_cache(controller: BaziController) -> None:
    # 直接访问内部缓存进行清理（部署前清零计数）
    controller._timeline_cache.clear()
    controller._cache_stats = {"hits": 0, "misses": 0, "invalidations": 0}


def run_performance_baseline(controller: BaziController) -> float:
    """
    运行一次基线预测（含 GEO），记录耗时（秒）。
    使用固定的示例输入，作为生产性能基线（目标 ~3.6ms 每次）。
    """
    try:
        controller.set_user_input(
            name="baseline_user",
            gender="男",
            date_obj=time.localtime().__getattribute__("tm_year") and __import__("datetime").date(1990, 1, 1),
            time_int=12,
            city="Beijing",
            enable_solar=True,
            longitude=116.46,
        )

        start = time.perf_counter()
        controller.run_geo_predictive_timeline(
            start_year=2024,
            duration=12,
            geo_correction_city="Beijing",
        )
        elapsed = time.perf_counter() - start
        return elapsed
    except Exception as e:
        logging.warning(f"Baseline run failed: {e}")
        return -1.0


def main():
    log_dir = ensure_log_dir()
    log_path = os.path.join(log_dir, "production.log")
    setup_structured_logging(log_path)

    logging.info("V9.6 monitor init: starting structured logging.")

    controller = BaziController()

    # 清空缓存
    clear_controller_cache(controller)
    logging.info("Timeline cache cleared for production start.")

    # 基线测试
    elapsed = run_performance_baseline(controller)
    if elapsed >= 0:
        logging.info(f"Baseline predictive timeline elapsed: {elapsed*1000:.3f} ms")
    else:
        logging.warning("Baseline predictive timeline not recorded.")

    logging.info("V9.6 monitor init completed.")


if __name__ == "__main__":
    main()

