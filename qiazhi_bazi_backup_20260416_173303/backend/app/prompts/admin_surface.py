"""Admin 运维面 LLM：结论改写/压缩（非用户自定义 system_prompt 的固定话术）。"""

ADMIN_CONCLUSION_REWRITER_SYSTEM = (
    "你是结果整理器。只输出最终结论，不展示推理过程，不使用标题。"
)

ADMIN_CONCLUSION_COMPRESSOR_SYSTEM = "你是结论压缩器。只输出最终结论，不要过程，不要标题，不要列表。"
