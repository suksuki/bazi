from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs
from core.state.foundation_contracts import UncertaintyProfile


class ThemeType(str, Enum):
    CREATION = "creation"
    ACCUMULATION = "accumulation"
    PRESSURE_TRANSFORMATION = "pressure_transformation"
    MANAGEMENT = "management"
    MOBILITY = "mobility"
    COMPETITION = "competition"
    STABILITY = "stability"
    RISK_CONTROL = "risk_control"
    RESOURCE_SUPPORT = "resource_support"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ThemeStability(str, Enum):
    STABLE = "stable"
    TIMING_SENSITIVE = "timing_sensitive"
    UNSTABLE = "unstable"
    UNKNOWN = "unknown"


class ThemeSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThemeCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    WEAK = "weak"
    UNKNOWN = "unknown"


class ThemeActivationSource(str, Enum):
    LUCK = "luck"
    YEAR = "year"
    MONTH = "month"
    TIMING_STATE = "timing_state"
    STATE_DELTA = "state_delta"
    UNKNOWN = "unknown"


class ThemeTransitionType(str, Enum):
    STABLE = "stable"
    TIMING_ACTIVATED = "timing_activated"
    RISK_SHIFT = "risk_shift"
    OPPORTUNITY_SHIFT = "opportunity_shift"
    CONFLICT_SHIFT = "conflict_shift"
    UNKNOWN = "unknown"


class ThemeCandidate(V50Model):
    version: str = "v50.theme_candidate.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_name: str
    theme_type: ThemeType = ThemeType.UNKNOWN
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    stability: ThemeStability = ThemeStability.UNKNOWN
    timing_sensitivity: ThemeSensitivity = ThemeSensitivity.MEDIUM
    active_now: bool | None = None
    opportunity_link: list[str] = Field(default_factory=list)
    risk_link: list[str] = Field(default_factory=list)
    strategy_link: str = "unknown"
    source_mechanism_refs: list[str] = Field(default_factory=list)
    source_state_dimension_refs: list[str] = Field(default_factory=list)
    source_timing_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    counter_theme: str = ""
    uncertainty: UncertaintyProfile
    completeness: ThemeCompleteness = ThemeCompleteness.UNKNOWN
    label_is_presentation_only: bool = True
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "theme_candidate_is_structural_life_theme_not_judgment_or_copy"

    @model_validator(mode="after")
    def _boundary(self) -> "ThemeCandidate":
        require_non_empty(self.theme_id, "theme_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.theme_name, "theme_name")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("ThemeCandidate requires a concrete or supported general domain")
        if self.theme_type != ThemeType.UNKNOWN:
            require_refs(self.source_mechanism_refs, "theme_candidate source_mechanism_refs")
            require_refs(self.source_state_dimension_refs, "theme_candidate source_state_dimension_refs")
            require_refs(self.evidence_refs, "theme_candidate evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "theme_candidate theory_refs")
        if not self.label_is_presentation_only:
            raise ValueError("ThemeCandidate label must remain presentation-only")
        if self.creates_judgment:
            raise ValueError("ThemeCandidate cannot create judgment")
        if self.calls_brain:
            raise ValueError("ThemeCandidate cannot call Brain")
        if self.calls_llm:
            raise ValueError("ThemeCandidate cannot call LLM")
        return self


class BaseTheme(V50Model):
    version: str = "v50.base_theme.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_type: ThemeType = ThemeType.UNKNOWN
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    stability: ThemeStability = ThemeStability.UNKNOWN
    source_mechanism_refs: list[str] = Field(default_factory=list)
    source_state_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    timing_can_mutate: bool = False
    boundary: str = "base_theme_is_natal_structural_theme_and_cannot_be_rewritten_by_timing"

    @model_validator(mode="after")
    def _boundary(self) -> "BaseTheme":
        require_non_empty(self.theme_id, "base_theme theme_id")
        require_non_empty(self.reading_id, "base_theme reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("BaseTheme requires a concrete or supported general domain")
        if self.theme_type != ThemeType.UNKNOWN:
            require_refs(self.source_mechanism_refs, "base_theme source_mechanism_refs")
            require_refs(self.source_state_refs, "base_theme source_state_refs")
            require_refs(self.evidence_refs, "base_theme evidence_refs")
        if self.timing_can_mutate:
            raise ValueError("Timing cannot mutate BaseTheme")
        if self.creates_judgment or self.calls_brain or self.calls_llm:
            raise ValueError("BaseTheme cannot create judgment or call Brain/LLM")
        return self


class ActiveTheme(V50Model):
    version: str = "v50.active_theme.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_type: ThemeType = ThemeType.UNKNOWN
    activation_source: ThemeActivationSource = ThemeActivationSource.UNKNOWN
    activation_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    active_now: bool = False
    opportunity_link: list[str] = Field(default_factory=list)
    risk_link: list[str] = Field(default_factory=list)
    strategy_link: str = "unknown"
    source_timing_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    mutates_base_theme: bool = False
    boundary: str = "active_theme_is_timing_activation_and_cannot_rewrite_base_theme"

    @model_validator(mode="after")
    def _boundary(self) -> "ActiveTheme":
        require_non_empty(self.theme_id, "active_theme theme_id")
        require_non_empty(self.reading_id, "active_theme reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("ActiveTheme requires a concrete or supported general domain")
        if self.theme_type != ThemeType.UNKNOWN:
            if self.activation_source == ThemeActivationSource.UNKNOWN:
                raise ValueError("concrete ActiveTheme requires activation_source")
            require_refs(self.source_timing_refs, "active_theme source_timing_refs")
            require_refs(self.evidence_refs, "active_theme evidence_refs")
        if self.mutates_base_theme:
            raise ValueError("ActiveTheme cannot mutate BaseTheme")
        if self.creates_judgment or self.calls_brain or self.calls_llm:
            raise ValueError("ActiveTheme cannot create judgment or call Brain/LLM")
        return self


class ThemeTransition(V50Model):
    version: str = "v50.theme_transition.v1"
    transition_id: str
    reading_id: str
    domain: Topic
    base_theme: BaseTheme
    active_theme: ActiveTheme
    transition_type: ThemeTransitionType = ThemeTransitionType.UNKNOWN
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    timing_changed_base_theme: bool = False
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "theme_transition_explains_timing_activation_without_rewriting_natal_theme"

    @model_validator(mode="after")
    def _boundary(self) -> "ThemeTransition":
        require_non_empty(self.transition_id, "theme_transition transition_id")
        require_non_empty(self.reading_id, "theme_transition reading_id")
        require_non_empty(self.reason, "theme_transition reason")
        if self.base_theme.reading_id != self.reading_id or self.active_theme.reading_id != self.reading_id:
            raise ValueError("ThemeTransition cannot mix readings")
        if self.base_theme.domain != self.domain or self.active_theme.domain != self.domain:
            raise ValueError("ThemeTransition cannot mix domains")
        if self.timing_changed_base_theme:
            raise ValueError("ThemeTransition cannot change BaseTheme")
        require_refs(self.evidence_refs, "theme_transition evidence_refs")
        if self.creates_judgment or self.calls_brain or self.calls_llm:
            raise ValueError("ThemeTransition cannot create judgment or call Brain/LLM")
        return self


class UnifiedThemeBundle(V50Model):
    version: str = "v50.unified_theme_bundle.v2"
    bundle_id: str
    reading_id: str
    domain: Topic
    domain_supported: bool = True
    domain_gap: bool = False
    base_theme: BaseTheme
    active_theme: ActiveTheme
    theme_transition: ThemeTransition
    primary_theme: ThemeCandidate
    primary_theme_legacy_derived: bool = True
    secondary_themes: list[ThemeCandidate] = Field(default_factory=list)
    counter_themes: list[ThemeCandidate] = Field(default_factory=list)
    theme_conflicts: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    missing_theme_inputs: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "unified_theme_bundle_collects_theme_candidates_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "UnifiedThemeBundle":
        require_non_empty(self.bundle_id, "bundle_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("UnifiedThemeBundle requires a concrete or supported general domain")
        if self.primary_theme.reading_id != self.reading_id or self.primary_theme.domain != self.domain:
            raise ValueError("UnifiedThemeBundle primary_theme must match reading/domain")
        if self.base_theme.reading_id != self.reading_id or self.active_theme.reading_id != self.reading_id:
            raise ValueError("UnifiedThemeBundle base/active themes must match reading")
        if self.base_theme.domain != self.domain or self.active_theme.domain != self.domain:
            raise ValueError("UnifiedThemeBundle base/active themes must match domain")
        if self.theme_transition.reading_id != self.reading_id or self.theme_transition.domain != self.domain:
            raise ValueError("UnifiedThemeBundle transition must match reading/domain")
        if not self.primary_theme_legacy_derived:
            raise ValueError("UnifiedThemeBundle primary_theme must remain legacy/derived")
        for theme in [*self.secondary_themes, *self.counter_themes]:
            if theme.reading_id != self.reading_id or theme.domain != self.domain:
                raise ValueError("UnifiedThemeBundle cannot mix theme readings or domains")
        if not self.domain_supported and not self.domain_gap:
            raise ValueError("unsupported UnifiedThemeBundle must set domain_gap")
        require_refs(self.evidence_refs, "unified_theme_bundle evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "unified_theme_bundle theory_refs")
        if self.creates_judgment:
            raise ValueError("UnifiedThemeBundle cannot create judgment")
        if self.calls_brain:
            raise ValueError("UnifiedThemeBundle cannot call Brain")
        if self.calls_llm:
            raise ValueError("UnifiedThemeBundle cannot call LLM")
        return self



