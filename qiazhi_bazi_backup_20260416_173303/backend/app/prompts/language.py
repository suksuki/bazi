"""统一语言输出指令（LanguageEngine）。各 LLM 链路禁止再手写 lang_hint。"""

from __future__ import annotations


class LanguageEngine:
    """
    全仓唯一「自然语言输出语言」指令入口。

    - ``output_directive_for_structured_flow``：与历史 ``lang_output_instruction`` 对齐，
      用于物理审计、通用聊天等「推理语境为中文命理、终稿可为 EN/KO」的场景。
    - ``strict_assistant_output_language``：仅约束助手最终输出语种（终判 system、首轮观察 user 尾部等）。
    """

    @staticmethod
    def output_directive_for_structured_flow(lang: str) -> str:
        upper = (lang or "ZH").upper()
        if upper == "EN":
            return (
                "请基于中文命理逻辑推演，但最终只用英文输出。"
                "若术语无直接对等词，使用标准学术拼音并保留术语一致性。"
            )
        if upper == "KO":
            return "请基于中文命理逻辑推演，但最终只用韩语输出，并使用韩语术语。请务必以“최종 결론:”开头。"
        return "请基于中文命理逻辑推演，并只用中文输出。"

    @staticmethod
    def strict_assistant_output_language(lang: str) -> str:
        """助手回复只允许指定自然语言（不含「推理用中文」子句）。"""
        upper = (lang or "ZH").upper()
        if upper == "EN":
            return "Please output strictly in English."
        if upper == "KO":
            return "최종 출력은 반드시 한국어로만 작성하세요."
        return "请仅使用中文输出。"

    @staticmethod
    def first_observation_output_hint(lang: str) -> str:
        """首轮观察 user 尾部：与历史 build_first_observation_messages 对齐。"""
        hints = {
            "ZH": "请仅使用中文输出。",
            "EN": (
                "Please output strictly in English. Use standard academic Pinyin for specific Chinese metaphysics "
                "terms if no direct English equivalent exists."
            ),
            "KO": "최종 출력은 반드시 한국어로만 작성하세요.",
        }
        return hints.get((lang or "ZH").upper(), hints["ZH"])
