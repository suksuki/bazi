from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleViewPolicy:
    role_key: str
    portrait_depth: str
    question_style: str
    explanation_style: str
    visibility_level: str
    question_limit: int
    portrait_limit: int

    def to_dict(self) -> dict[str, object]:
        return {
            "role_key": self.role_key,
            "portrait_depth": self.portrait_depth,
            "question_style": self.question_style,
            "explanation_style": self.explanation_style,
            "visibility_level": self.visibility_level,
            "question_limit": self.question_limit,
            "portrait_limit": self.portrait_limit,
        }
