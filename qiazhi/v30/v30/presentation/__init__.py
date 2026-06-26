"""Role, locale, and client presentation for V30."""

from v30.presentation.client_model import build_presentation_model
from v30.presentation.projection_matrix import build_role_locale_client_projection_matrix

__all__ = ["build_presentation_model", "build_role_locale_client_projection_matrix"]
