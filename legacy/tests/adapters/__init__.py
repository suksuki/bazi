"""
Test Adapters - Legacy Test Compatibility Layer
===============================================
V9.5 MVC Architecture Migration Support

This module provides adapter classes that allow legacy tests to work
through the BaziController while maintaining backward compatibility.
"""

from .test_engine_adapter import (
    BaziCalculatorAdapter,
    QuantumEngineAdapter,
    FluxEngineAdapter,
    get_controller_for_test
)

__all__ = [
    'BaziCalculatorAdapter',
    'QuantumEngineAdapter', 
    'FluxEngineAdapter',
    'get_controller_for_test'
]

