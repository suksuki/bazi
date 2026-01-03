
"""
FDS Physics Kernel (v3.0)
=========================
FDS 物理内核宪法 (Static Sign Matrix)

This module defines the Immutable "Sovereign Constitution" for FDS fitting.
It maps Classical Ten Gods to 5D Tensor Directions (Sign Constraints).

Compliance: FDS_PHYSICS_KERNEL_v3.0.md
"""

from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# Dimension Indices
# E, O, M, S, R
DIM_E = 0
DIM_O = 1
DIM_M = 2
DIM_S = 3
DIM_R = 4

# Direction Constants
POS = 1.0   # Positive Correlation (+)
NEG = -1.0  # Negative Correlation (-)
NUT = 0.0   # Neutral/Weak Correlation (~)
STR_POS = 2.0 # Strong Positive (++)
STR_NEG = -2.0 # Strong Negative (--)

# ============================================================
# 3. 静态符号矩阵 (Static Sign Matrix)
# ============================================================
# Mapping: Ten God -> [E, O, M, S, R] Signs
# Values indicate EXPECTED direction of contribution.
STATIC_SIGN_MATRIX = {
    # 比肩 (Bi Jian): E++, O~, M-, S+, R++
    "bi_jian":      [STR_POS, NUT, NEG, POS, STR_POS],
    
    # 劫财 (Jie Cai): E++, O-, M--, S++, R+++
    "jie_cai":      [STR_POS, NEG, STR_NEG, STR_POS, 3.0], 
    
    # 食神 (Shi Shen): E-, O~, M+, S++, R+
    "shi_shen":     [NEG, NUT, POS, STR_POS, POS],
    
    # 伤官 (Shang Guan): E--, O--, M++, S+++, R++
    "shang_guan":   [STR_NEG, STR_NEG, STR_POS, 3.0, STR_POS],
    
    # 偏财 (Pian Cai): E-, O~, M+++, S+, R+
    "pian_cai":     [NEG, NUT, 3.0, POS, POS],
    
    # 正财 (Zheng Cai): E-, O+, M++, S-, R~
    "zheng_cai":    [NEG, POS, STR_POS, NEG, NUT],
    
    # 七杀 (Qi Sha): E--, O+++, M~, S++, R--
    "qi_sha":       [STR_NEG, 3.0, NUT, STR_POS, STR_NEG],
    
    # 正官 (Zheng Guan): E-, O++, M~, S-, R-
    "zheng_guan":   [NEG, STR_POS, NUT, NEG, NEG],
    
    # 偏印 (Pian Yin): E++, O~, M-, S++, R-
    "pian_yin":     [STR_POS, NUT, NEG, STR_POS, NEG],
    
    # 正印 (Zheng Yin): E+++, O+, M-, S-, R~
    "zheng_yin":    [3.0, POS, NEG, NEG, NUT]
}

def validate_tensor_signs(
    pattern_id: str,
    fitted_mean: List[float],
    dominant_gods: List[str]
) -> Dict[str, Any]:
    """
    Validation function to check if Fitted Mean Tensor obeys the Static Sign Matrix.
    
    Args:
        pattern_id: Pattern ID being fitted
        fitted_mean: The 5D mean vector [E, O, M, S, R] calculated from FDS
        dominant_gods: List of Ten Gods that define this pattern (e.g. ['qi_sha'] for A-02)
        
    Returns:
        Validation result with Drift Score
    """
    drift_score = 0.0
    details = []
    
    # Normalize fitted mean to avoid magnitude bias? 
    # Actually we just care about signs for now, but strictly speaking 
    # we want to ensure high values align with ++.
    
    # For A-03 (Yang Ren), check if it behaves like Jie Cai (Rob Wealth) ?
    # Typically Yang Ren = Strong Jie Cai energy.
    # So we expect high E and high R.
    
    # Simplified Logic:
    # 1. Identify expected signs based on dominant gods
    expected_vector = [0.0] * 5
    for god in dominant_gods:
        signs = STATIC_SIGN_MATRIX.get(god, [0,0,0,0,0])
        for i in range(5):
            expected_vector[i] += signs[i]
            
    # 2. Compare signs
    violations = 0
    total_checks = 0
    
    dims = ['E', 'O', 'M', 'S', 'R']
    
    for i in range(5):
        exp = expected_vector[i]
        act = fitted_mean[i]
        
        # If Expected is Strongly Positive (>= 2.0), Actual MUST be > 0.2 (Threshold)
        if exp >= 2.0:
            total_checks += 1
            if act < 0.2:
                violations += 1
                drift_score += 0.2
                details.append(f"❌ Dim {dims[i]}: Expected ++ (>{0.2}), Got {act:.2f}")
                
        # If Expected is Strongly Negative (<= -2.0), Actual MUST be < -0.2
        elif exp <= -2.0:
            total_checks += 1
            if act > -0.2:
                violations += 1
                drift_score += 0.2
                details.append(f"❌ Dim {dims[i]}: Expected -- (<{-0.2}), Got {act:.2f}")
                
        # If Expected is Positive (> 0), Actual should be > 0 (Soft check)
        elif exp > 0:
            if act < 0:
                drift_score += 0.05 # Smaller penalty
                
        # If Expected is Negative (< 0), Actual should be < 0 (Soft check)
        elif exp < 0:
            if act > 0:
                drift_score += 0.05
    
    passed = drift_score < 0.3
    
    return {
        "passed": passed,
        "drift_score": drift_score,
        "details": details,
        "expected_trend": expected_vector
    }

