"""三语文案键（墓库交互等）；前端可按 locale 取值。"""

STOREHOUSE_UI: dict[str, dict[str, str]] = {
    "zh": {
        "title": "墓库裁决",
        "sealed": "闭库",
        "open": "开库",
        "collapse": "坍塌",
        "confirm": "确认裁决",
        "hint_arbitration": "系统建议需要人工确认，请选择与命理解释一致的相位。",
    },
    "en": {
        "title": "Storehouse arbitration",
        "sealed": "Sealed vault",
        "open": "Open vault",
        "collapse": "Collapse",
        "confirm": "Confirm",
        "hint_arbitration": "Please confirm the phase that matches the classical reading.",
    },
    "ko": {
        "title": "묘고 재판",
        "sealed": "폐고",
        "open": "개고",
        "collapse": "붕괴",
        "confirm": "확인",
        "hint_arbitration": "해석에 맞는 위상을 선택하세요.",
    },
}
