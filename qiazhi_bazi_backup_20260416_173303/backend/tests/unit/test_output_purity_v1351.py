from __future__ import annotations

from app.skills.final_verdict_parts.terminal_purity import TERMINAL_TECH_RE, terminal_semantic_purge


def test_terminal_semantic_purge_zero_tech_terms_under_pressure() -> None:
    payloads = []
    for i in range(50):
        payloads.append(
            (
                f"【裁断】局势待定 v13.{i}\n"
                f"【证据】Fact_ID=liuchong_{i} 与 VF_tag_{i} 交错，"
                f"sys.core.physics 已登记 metadata.trace.logic\n"
                "【行】先守后攻\n"
                "【禁】勿盲动"
            )
        )

    for text in payloads:
        cleaned, hits = terminal_semantic_purge(text)
        assert hits, "应命中并清洗技术残留"
        assert cleaned.strip()
        assert TERMINAL_TECH_RE.search(cleaned) is None
