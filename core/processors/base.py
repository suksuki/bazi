"""
Antigravity V8.8 Processor Base
================================
Abstract base class for all processors in the pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProcessor(ABC):
    """
    Base class for all V8.8 processors.
    
    Each processor:
    - Receives a context dict
    - Performs one specific calculation
    - Returns a result dict
    
    Processors should NOT depend on each other directly.
    The engine orchestrates the data flow.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable processor name"""
        pass
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the context and return results.
        
        Args:
            context: Dictionary containing:
                - bazi: List of 4 pillars ['甲子', '乙丑', ...]
                - day_master: Day Master character, e.g., '甲'
                - dm_element: Day Master element, e.g., 'wood'
                - month_branch: Month branch character, e.g., '午'
                - (other processors may add more keys)
        
        Returns:
            Dictionary with processor-specific results
        """
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
