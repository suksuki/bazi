class DreamStateError(ValueError):
    """The requested dream transition is not valid for the current state."""


class DreamConflictError(ValueError):
    """A concurrent or conflicting dream write was rejected."""
