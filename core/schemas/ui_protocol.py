"""
Antigravity V8.8 UI Protocol
=============================
Server-Driven UI: Backend decides how frontend renders.

This module defines the contract between backend engine and frontend UI.
All analysis results MUST be wrapped in AnalysisResponse.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class VisualTheme(str, Enum):
    """Visual themes for different states"""
    NORMAL = "normal"           # Standard display
    WARNING = "warning"         # Caution needed (e.g., scorched earth)
    DANGER = "danger"           # High risk (e.g., extreme weakness)
    FROZEN = "frozen"           # Cold/blocked state
    PROSPERITY = "prosperity"   # Strong/favorable state


class UIElement(BaseModel):
    """Atomic UI rendering instruction"""
    display_text: str               # Display text, e.g., "身强 (得令)"
    color_hex: str                  # Color code, e.g., "#E74C3C"
    icon_name: str                  # Icon ID, e.g., "fire-flame"
    css_class: Optional[str] = None # Frontend CSS class
    tooltip: Optional[str] = None   # Hover tooltip text


class ChartConfig(BaseModel):
    """Chart visualization configuration"""
    highlight_elements: List[str] = []  # Elements to highlight, e.g., ['fire', 'earth']
    suggested_theme: VisualTheme = VisualTheme.NORMAL
    animation: Optional[str] = None     # Special animation, e.g., "scorched_earth"


class PhaseChangeInfo(BaseModel):
    """V8.0 Phase Change Protocol information"""
    is_active: bool = False
    phase_type: Optional[str] = None    # "scorched_earth", "frozen_water", "humid_rescue"
    damping_factor: float = 1.0         # 0.15 scorched, 0.30 frozen, 0.80 rescue
    description: str = ""


class StrengthResult(BaseModel):
    """Day Master strength analysis result"""
    verdict: str                    # "Strong", "Weak", "Moderate", "Follower"
    raw_score: float                # Pre-adjustment score
    adjusted_score: float           # Post-adjustment final score
    confidence: float = 0.8         # Confidence level 0.0-1.0
    
    # Breakdown (for debugging/UI display)
    in_command_bonus: float = 0.0   # 得令加分
    resource_month_bonus: float = 0.0  # 印绶月加分
    root_bonus: float = 0.0         # 通根加分
    stem_support_bonus: float = 0.0 # 天干支援加分


class AnalysisResponse(BaseModel):
    """
    V8.8 Standard Analysis Output Protocol
    =======================================
    This is the ONLY format that should be returned from the engine.
    Frontend MUST render based on this structure.
    """
    
    # === Core Results (Data Layer) ===
    strength: StrengthResult
    favorable_elements: List[str] = []      # Favorable elements
    unfavorable_elements: List[str] = []    # Unfavorable elements
    
    # === Detailed Breakdown (Logic Layer) ===
    energy_distribution: Dict[str, float] = {}  # Five element energy map
    phase_change: PhaseChangeInfo = PhaseChangeInfo()
    
    # === UI Instructions (Presentation Layer) ===
    ui: UIElement
    chart_config: ChartConfig = ChartConfig()
    
    # === Algorithm Trace (Debug Layer) ===
    messages: List[str] = []        # Algorithm decision log
    debug: Optional[Dict[str, Any]] = None  # Raw debug data
    
    # === Metadata ===
    engine_version: str = "V8.8"
    
    class Config:
        """Pydantic config"""
        json_encoders = {
            VisualTheme: lambda v: v.value
        }


# === Convenience Constructors ===

def create_strong_response(score: float, reason: str) -> AnalysisResponse:
    """Factory for Strong verdict responses"""
    return AnalysisResponse(
        strength=StrengthResult(
            verdict="Strong",
            raw_score=score,
            adjusted_score=score,
            confidence=0.85
        ),
        ui=UIElement(
            display_text=f"身强 ({reason})",
            color_hex="#27AE60",  # Green
            icon_name="shield-check"
        ),
        chart_config=ChartConfig(
            suggested_theme=VisualTheme.PROSPERITY
        ),
        messages=[f"Verdict: Strong - {reason}"]
    )


def create_weak_response(score: float, reason: str, phase_info: PhaseChangeInfo = None) -> AnalysisResponse:
    """Factory for Weak verdict responses"""
    theme = VisualTheme.WARNING if phase_info and phase_info.is_active else VisualTheme.NORMAL
    return AnalysisResponse(
        strength=StrengthResult(
            verdict="Weak",
            raw_score=score,
            adjusted_score=score,
            confidence=0.85
        ),
        phase_change=phase_info or PhaseChangeInfo(),
        ui=UIElement(
            display_text=f"身弱 ({reason})",
            color_hex="#E74C3C",  # Red
            icon_name="alert-triangle"
        ),
        chart_config=ChartConfig(
            suggested_theme=theme
        ),
        messages=[f"Verdict: Weak - {reason}"]
    )
