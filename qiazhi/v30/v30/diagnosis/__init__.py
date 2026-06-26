"""V30 real Bazi diagnosis engine contracts and runtime modules."""

from v30.diagnosis.contracts import (
    DIAGNOSIS_CONTRACT_VERSION,
    DiagnosisClaim,
    DiagnosisClaimLevel,
    DiagnosisConfidenceBand,
    DiagnosisContext,
    DiagnosisDomain,
    DiagnosisFeature,
    DiagnosisGraph,
    DiagnosisGraphEdge,
    DiagnosisGraphEdgeKind,
    DiagnosisGraphNode,
    DiagnosisGraphNodeKind,
    DiagnosisMode,
    DiagnosisPath,
    DiagnosisPortrait,
    DiagnosisRouteDecision,
    MatchedRule,
    RealBaziDiagnosis,
)
from v30.diagnosis.rule_matcher import RULE_MATCHER_VERSION, match_real_bazi_rules, summarize_rule_matches
from v30.diagnosis.path_engine import PATH_ENGINE_VERSION, summarize_diagnosis_paths, translate_dynamic_paths
from v30.diagnosis.feature_engine import (
    FEATURE_ENGINE_VERSION,
    extract_diagnosis_features,
    summarize_diagnosis_features,
)
from v30.diagnosis.portrait_engine import (
    PORTRAIT_ENGINE_VERSION,
    extract_diagnosis_portraits,
    summarize_diagnosis_portraits,
)
from v30.diagnosis.claim_generator import (
    CLAIM_GENERATOR_VERSION,
    generate_diagnosis_claims,
    summarize_diagnosis_claims,
)
from v30.diagnosis.graph import DIAGNOSIS_GRAPH_VERSION, build_diagnosis_graph, summarize_diagnosis_graph

__all__ = [
    "CLAIM_GENERATOR_VERSION",
    "DIAGNOSIS_CONTRACT_VERSION",
    "DIAGNOSIS_GRAPH_VERSION",
    "FEATURE_ENGINE_VERSION",
    "PATH_ENGINE_VERSION",
    "PORTRAIT_ENGINE_VERSION",
    "RULE_MATCHER_VERSION",
    "DiagnosisClaim",
    "DiagnosisClaimLevel",
    "DiagnosisConfidenceBand",
    "DiagnosisContext",
    "DiagnosisDomain",
    "DiagnosisFeature",
    "DiagnosisGraph",
    "DiagnosisGraphEdge",
    "DiagnosisGraphEdgeKind",
    "DiagnosisGraphNode",
    "DiagnosisGraphNodeKind",
    "DiagnosisMode",
    "DiagnosisPath",
    "DiagnosisPortrait",
    "DiagnosisRouteDecision",
    "MatchedRule",
    "RealBaziDiagnosis",
    "extract_diagnosis_features",
    "extract_diagnosis_portraits",
    "generate_diagnosis_claims",
    "build_diagnosis_graph",
    "match_real_bazi_rules",
    "summarize_diagnosis_claims",
    "summarize_diagnosis_graph",
    "summarize_diagnosis_features",
    "summarize_diagnosis_portraits",
    "summarize_rule_matches",
    "summarize_diagnosis_paths",
    "translate_dynamic_paths",
]
