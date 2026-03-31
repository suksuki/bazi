"""
Antigravity V8.8 Schemas Package
=================================
Contains all Pydantic models and protocols.
"""

from core.schemas.ui_protocol import (
    VisualTheme,
    UIElement,
    ChartConfig,
    PhaseChangeInfo,
    StrengthResult,
    AnalysisResponse,
    create_strong_response,
    create_weak_response
)

__all__ = [
    'VisualTheme',
    'UIElement',
    'ChartConfig',
    'PhaseChangeInfo',
    'StrengthResult',
    'AnalysisResponse',
    'create_strong_response',
    'create_weak_response'
]
