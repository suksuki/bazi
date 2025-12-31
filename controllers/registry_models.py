"""
🎛️ Registry Data Models
========================
Data models for the Quantum Registry Management System.
Defines the structure of modules, patterns, and themes.

MVC: Model Layer
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ModuleStatus(Enum):
    """Module status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"
    CALIBRATING = "CALIBRATING"


class PatternCategory(Enum):
    """Pattern category enumeration."""
    POWER = "POWER"
    WEALTH = "WEALTH"
    RELATIONSHIP = "RELATIONSHIP"
    CAREER = "CAREER"
    HEALTH = "HEALTH"
    GENERAL = "GENERAL"


class ComplianceLevel(Enum):
    """FDS compliance level enumeration."""
    FDS_V1_5_1 = "FDS-V1.5.1"
    FDS_V1_6 = "FDS-V1.6"
    FDS_V1_7 = "FDS-V1.7"
    FDS_V2_0 = "FDS-V2.0"
    NON_COMPLIANT = "NON-COMPLIANT"


@dataclass
class PhysicsKernel:
    """Physics kernel configuration for patterns."""
    version: str = "1.0"
    integrity_threshold: float = 0.5
    transfer_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    axiom_mask: Optional[str] = None
    tensor_dynamics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ManifoldData:
    """Manifold data for pattern matching."""
    mean_vector: Dict[str, float] = field(default_factory=dict)
    covariance_matrix: Optional[List[List[float]]] = None
    thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class SubPattern:
    """Sub-pattern definition."""
    id: str
    name: str
    name_cn: Optional[str] = None
    risk_level: str = "NORMAL"
    description: Optional[str] = None
    special_instruction: Optional[str] = None
    population_priority: Optional[str] = None
    matrix_override: Dict[str, Any] = field(default_factory=dict)
    manifold_data: Optional[ManifoldData] = None


@dataclass
class MatchingStrategy:
    """Pattern matching strategy."""
    priority: int
    target: str
    logic: str


@dataclass 
class MatchingRouter:
    """Routing configuration for sub-pattern matching."""
    strategies: List[MatchingStrategy] = field(default_factory=list)


@dataclass
class PatternMetaInfo:
    """Meta information for patterns."""
    physics_prototype: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0.0"
    compliance: str = "FDS-V1.5.1"


@dataclass
class HolographicPattern:
    """Holographic pattern definition."""
    id: str
    name: str
    name_cn: Optional[str] = None
    icon: str = "🌌"
    category: str = "GENERAL"
    subject_id: Optional[str] = None
    version: str = "1.0.0"
    active: bool = True
    meta_info: Optional[PatternMetaInfo] = None
    physics_kernel: Optional[PhysicsKernel] = None
    matching_router: Optional[MatchingRouter] = None
    sub_patterns_registry: List[SubPattern] = field(default_factory=list)

    def is_compliant(self) -> bool:
        """Check if pattern is FDS-V1.5.1+ compliant."""
        if self.meta_info and self.meta_info.compliance:
            compliance = self.meta_info.compliance
            return (
                compliance.startswith("FDS-V1.5") or
                compliance.startswith("FDS-V1.6") or
                compliance.startswith("FDS-V1.7") or
                compliance.startswith("FDS-V2")
            )
        return False


@dataclass
class SystemModule:
    """System module definition."""
    id: str
    name: str
    icon: str = "🔧"
    type: str = "DETAIL"
    description: str = ""
    active: bool = True
    layer: str = "FUNDAMENTAL"
    priority: int = 100
    status: str = "ACTIVE"
    theme: Optional[str] = None
    goal: Optional[str] = None
    outcome: Optional[str] = None
    linked_rules: List[str] = field(default_factory=list)
    linked_metrics: List[str] = field(default_factory=list)
    used_algorithms: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    origin_trace: List[str] = field(default_factory=list)
    fusion_type: str = "CORE_MODULE"
    scenario_affinity: List[str] = field(default_factory=list)
    class_path: Optional[str] = None


@dataclass
class Theme:
    """Theme definition for module organization."""
    id: str
    name: str
    description: str = ""
    registry_path: Optional[str] = None
    registry_standard: Optional[str] = None


@dataclass
class SystemManifest:
    """Complete system manifest."""
    version: str
    description: str
    system_id: str
    themes: Dict[str, Theme] = field(default_factory=dict)
    modules: Dict[str, SystemModule] = field(default_factory=dict)


@dataclass
class PatternRegistry:
    """Complete pattern registry."""
    meta: Dict[str, Any] = field(default_factory=dict)
    patterns: Dict[str, HolographicPattern] = field(default_factory=dict)


# ==================== Factory Functions ====================

def create_module_from_dict(mod_id: str, data: Dict[str, Any]) -> SystemModule:
    """Create a SystemModule from dictionary data."""
    return SystemModule(
        id=mod_id,
        name=data.get('name', ''),
        icon=data.get('icon', '🔧'),
        type=data.get('type', 'DETAIL'),
        description=data.get('description', ''),
        active=data.get('active', True),
        layer=data.get('layer', 'FUNDAMENTAL'),
        priority=data.get('priority', 100),
        status=data.get('status', 'ACTIVE'),
        theme=data.get('theme'),
        goal=data.get('goal'),
        outcome=data.get('outcome'),
        linked_rules=data.get('linked_rules', []),
        linked_metrics=data.get('linked_metrics', []),
        used_algorithms=data.get('used_algorithms', []),
        dependencies=data.get('dependencies', []),
        origin_trace=data.get('origin_trace', []),
        fusion_type=data.get('fusion_type', 'CORE_MODULE'),
        scenario_affinity=data.get('scenario_affinity', []),
        class_path=data.get('class')
    )


def create_pattern_from_dict(pat_id: str, data: Dict[str, Any]) -> HolographicPattern:
    """Create a HolographicPattern from dictionary data."""
    meta_data = data.get('meta_info', {})
    meta_info = PatternMetaInfo(
        physics_prototype=meta_data.get('physics_prototype'),
        description=meta_data.get('description'),
        version=meta_data.get('version', '1.0.0'),
        compliance=meta_data.get('compliance', 'N/A')
    )
    
    kernel_data = data.get('physics_kernel', {})
    physics_kernel = PhysicsKernel(
        version=kernel_data.get('version', '1.0'),
        integrity_threshold=kernel_data.get('integrity_threshold', 0.5),
        transfer_matrix=kernel_data.get('transfer_matrix', {}),
        axiom_mask=kernel_data.get('axiom_mask'),
        tensor_dynamics=kernel_data.get('tensor_dynamics', {})
    ) if kernel_data else None
    
    router_data = data.get('matching_router', {})
    matching_router = None
    if router_data:
        strategies = [
            MatchingStrategy(
                priority=s.get('priority', 0),
                target=s.get('target', ''),
                logic=s.get('logic', '')
            )
            for s in router_data.get('strategies', [])
        ]
        matching_router = MatchingRouter(strategies=strategies)
    
    sub_patterns = []
    for sp_data in data.get('sub_patterns_registry', []):
        manifold = None
        if 'manifold_data' in sp_data:
            manifold = ManifoldData(
                mean_vector=sp_data['manifold_data'].get('mean_vector', {}),
                thresholds=sp_data['manifold_data'].get('thresholds', {})
            )
        
        sub_patterns.append(SubPattern(
            id=sp_data.get('id', ''),
            name=sp_data.get('name', ''),
            name_cn=sp_data.get('name_cn'),
            risk_level=sp_data.get('risk_level', 'NORMAL'),
            description=sp_data.get('description'),
            special_instruction=sp_data.get('special_instruction'),
            population_priority=sp_data.get('population_priority'),
            matrix_override=sp_data.get('matrix_override', {}),
            manifold_data=manifold
        ))
    
    return HolographicPattern(
        id=pat_id,
        name=data.get('name', ''),
        name_cn=data.get('name_cn'),
        icon=data.get('icon', '🌌'),
        category=data.get('category', 'GENERAL'),
        subject_id=data.get('subject_id'),
        version=data.get('version', '1.0.0'),
        active=data.get('active', True),
        meta_info=meta_info,
        physics_kernel=physics_kernel,
        matching_router=matching_router,
        sub_patterns_registry=sub_patterns
    )


def create_theme_from_dict(theme_id: str, data: Dict[str, Any]) -> Theme:
    """Create a Theme from dictionary data."""
    return Theme(
        id=theme_id,
        name=data.get('name', ''),
        description=data.get('description', ''),
        registry_path=data.get('registry_path'),
        registry_standard=data.get('registry_standard')
    )
