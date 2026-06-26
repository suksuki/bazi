"""V30 hidden factor discovery."""

from v30.hidden_factor.attributes import (
    LATENT_BAZI_ATTRIBUTES_VERSION,
    LatentAttributeScore,
    LatentBaziAttributes,
    LatentModifierScore,
    build_individualized_model_projection,
    build_latent_bazi_attributes,
    summarize_individualized_model_projection,
    summarize_latent_bazi_attributes,
)
from v30.hidden_factor.calibration import HiddenFactorCalibration, calibrate_hidden_factors
from v30.hidden_factor.discovery import HiddenFactorProbe, build_hidden_factor_probes
from v30.hidden_factor.latent_profile import (
    LATENT_BAZI_PROFILE_VERSION,
    LatentBaziProfile,
    LatentBaziProfileDimension,
    build_latent_bazi_profile,
    summarize_latent_bazi_profile,
)
from v30.hidden_factor.question_strategy import LATENT_QUESTION_STRATEGY_VERSION, build_latent_question_need_strategy
from v30.hidden_factor.state import (
    EventYearSignal,
    HiddenFactorFeedback,
    HiddenFactorState,
    RepeatedStateSignal,
    build_hidden_factor_state,
    hidden_factor_feedback_from_payload,
    merge_hidden_factor_state,
    normalize_hidden_factor_state_payload,
)

__all__ = [
    "EventYearSignal",
    "HiddenFactorFeedback",
    "HiddenFactorCalibration",
    "HiddenFactorProbe",
    "HiddenFactorState",
    "LATENT_BAZI_ATTRIBUTES_VERSION",
    "LATENT_BAZI_PROFILE_VERSION",
    "LATENT_QUESTION_STRATEGY_VERSION",
    "LatentAttributeScore",
    "LatentBaziAttributes",
    "LatentBaziProfile",
    "LatentBaziProfileDimension",
    "LatentModifierScore",
    "RepeatedStateSignal",
    "build_individualized_model_projection",
    "build_latent_bazi_attributes",
    "build_latent_bazi_profile",
    "build_hidden_factor_probes",
    "build_hidden_factor_state",
    "build_latent_question_need_strategy",
    "calibrate_hidden_factors",
    "hidden_factor_feedback_from_payload",
    "merge_hidden_factor_state",
    "normalize_hidden_factor_state_payload",
    "summarize_individualized_model_projection",
    "summarize_latent_bazi_attributes",
    "summarize_latent_bazi_profile",
]
