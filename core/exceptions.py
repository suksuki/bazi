"""
V9.5 Custom Exceptions
=====================
User-friendly exception classes for Bazi prediction system.
"""


class BaziError(Exception):
    """Base exception for all Bazi-related errors."""
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize Bazi error.
        
        Args:
            message: User-friendly error message
            details: Technical details for debugging
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class BaziCalculationError(BaziError):
    """Raised when calculation fails."""
    pass


class BaziInputError(BaziError):
    """Raised when user input is invalid."""
    pass


class BaziDataError(BaziError):
    """Raised when data is missing or corrupted."""
    pass


class BaziEngineError(BaziError):
    """Raised when engine initialization or execution fails."""
    pass


class BaziCacheError(BaziError):
    """Raised when cache operations fail."""
    pass

