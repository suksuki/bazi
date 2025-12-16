"""
utils/notification_manager.py
-----------------------------
Centralized notification hub for collecting and displaying messages.

Usage:
    from utils.notification_manager import get_notification_manager
    nm = get_notification_manager()
    nm.add_error("title", "detail")
    nm.display_all()  # Typically called once per page render
"""

import threading
from typing import List, Dict
import streamlit as st


class NotificationManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(NotificationManager, cls).__new__(cls)
                    cls._instance._errors: List[Dict] = []
                    cls._instance._warnings: List[Dict] = []
                    cls._instance._infos: List[Dict] = []
        return cls._instance

    def add_error(self, title: str, detail: str = "") -> None:
        self._errors.append({"title": title, "detail": detail})

    def add_warning(self, title: str, detail: str = "") -> None:
        self._warnings.append({"title": title, "detail": detail})

    def add_info(self, title: str, detail: str = "") -> None:
        self._infos.append({"title": title, "detail": detail})

    def display_all(self) -> None:
        if self._errors:
            for item in self._errors:
                st.error(f"{item['title']}" + (f" — {item['detail']}" if item.get('detail') else ""))
        if self._warnings:
            for item in self._warnings:
                st.warning(f"{item['title']}" + (f" — {item['detail']}" if item.get('detail') else ""))
        if self._infos:
            for item in self._infos:
                st.info(f"{item['title']}" + (f" — {item['detail']}" if item.get('detail') else ""))
        self.clear()

    def clear(self) -> None:
        self._errors.clear()
        self._warnings.clear()
        self._infos.clear()


def get_notification_manager() -> NotificationManager:
    return NotificationManager()

