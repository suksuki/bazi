"""
Antigravity V3.5+ - Unified Data Protocol
DestinyContext: The universal currency for Prediction, Verification, and Cinema
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DestinyContext:
    """
    命运上下文对象 - 三位一体架构的核心数据协议
    
    This is the ONLY object that flows between:
    - QuantumEngine (Producer)
    - Verification (Consumer for testing)
    - Cinema (Consumer for narrative)
    - Dashboard (Consumer for UI)
    """
    
    # === 基础时空信息 ===
    year: int                      # 流年年份, e.g. 2024
    pillar: str                    # 天干地支, e.g. "甲辰"
    luck_pillar: Optional[str] = None  # 大运干支, e.g. "癸卯"
    
    # === 量子状态 (From QuantumEngine V3.5) ===
    score: float = 0.0             # 综合分数, e.g. -36.0 or +20.0
    raw_score: float = 0.0         # 未处理的原始分数
    energy_level: str = "Neutral"  # "Extreme Risk" / "High Opportunity" / "Neutral" / "Moderate"
    
    # === V3.5 核心特征 ===
    is_treasury_open: bool = False       # 是否有墓库开启
    treasury_type: Optional[str] = None  # "Wealth" / "Power" / "Resource" / "Output"
    treasury_element: Optional[str] = None  # 地支, e.g. "戌"
    
    day_master_strength: str = "Medium"  # "Strong" / "Medium" / "Weak"
    dm_energy: float = 0.0               # 日主能量值
    
    # === 风险评估 ===
    risk_level: str = "none"       # "none" / "opportunity" / "warning" / "danger"
    risk_factors: List[str] = field(default_factory=list)  # ["财多身弱", "截脚"]
    
    # === 表现层 (UI/Cinema 需要) ===
    icon: Optional[str] = None     # "🏆" / "⚠️" / "🗝️" / "💀"
    display_color: str = "#FFD700" # Gold / Orange / Red / Green
    tags: List[str] = field(default_factory=list)  # ["身弱", "破财风险", "财库冲开"]
    
    # === 详细信息 ===
    details: List[str] = field(default_factory=list)  # V2.0 compatible details list
    description: str = ""          # 一句话总结
    
    # === 三维度分数 (Legacy Support) ===
    career: float = 0.0
    wealth: float = 0.0
    relationship: float = 0.0
    
    # === 叙事层 (LLM 生成用) ===
    narrative_prompt: str = ""     # 给LLM看的结构化提示词
    narrative_events: List[Dict[str, Any]] = field(default_factory=list)  # 事件卡片
    
    # === 元数据 ===
    version: str = "V3.5"          # 算法版本
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'year': self.year,
            'pillar': self.pillar,
            'luck_pillar': self.luck_pillar,
            'score': self.score,
            'energy_level': self.energy_level,
            'is_treasury_open': self.is_treasury_open,
            'treasury_type': self.treasury_type,
            'day_master_strength': self.day_master_strength,
            'risk_level': self.risk_level,
            'icon': self.icon,
            'display_color': self.display_color,
            'tags': self.tags,
            'details': self.details,
            'description': self.description,
            'career': self.career,
            'wealth': self.wealth,
            'relationship': self.relationship,
            'narrative_prompt': self.narrative_prompt,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DestinyContext':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def get_energy_category(self) -> str:
        """Categorize energy level based on score"""
        if self.score >= 8:
            return "Extreme Opportunity"
        elif self.score >= 4:
            return "High Opportunity"
        elif self.score >= 0:
            return "Moderate Positive"
        elif self.score >= -4:
            return "Moderate Negative"
        elif self.score >= -8:
            return "High Risk"
        else:
            return "Extreme Risk"
    
    def get_display_style(self) -> Dict[str, str]:
        """Get display styling based on risk level"""
        styles = {
            'opportunity': {'color': '#FFD700', 'bg': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'},
            'warning': {'color': '#FF6B35', 'bg': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'},
            'danger': {'color': '#DC2626', 'bg': 'linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)'},
            'none': {'color': '#94A3B8', 'bg': 'linear-gradient(135deg, #334155 0%, #1e293b 100%)'}
        }
        return styles.get(self.risk_level, styles['none'])
    
    def build_narrative_prompt(self) -> str:
        """Auto-generate narrative prompt for LLM"""
        if self.narrative_prompt:
            return self.narrative_prompt
        
        # Auto-construct
        strength_desc = {
            'Strong': '身强',
            'Medium': '中和',
            'Weak': '身弱'
        }
        
        prompt_parts = []
        prompt_parts.append(f"流年{self.year}年({self.pillar})")
        prompt_parts.append(f"日主{strength_desc.get(self.day_master_strength, '中和')}")
        
        if self.is_treasury_open:
            action = "冲开" if self.risk_level == "warning" else "开启"
            prompt_parts.append(f"{self.treasury_type}库{action}")
        
        if self.risk_level == "warning":
            prompt_parts.append(f"触发风险警告")
        elif self.risk_level == "opportunity":
            prompt_parts.append(f"机遇显现")
        
        prompt_parts.append(f"综合评分{self.score:.1f}")
        
        return "，".join(prompt_parts) + "。"


# === Factory Functions ===

def create_context_from_v35_result(
    year: int,
    pillar: str,
    v35_result: Dict[str, Any],
    career: float = 0.0,
    wealth: float = 0.0,
    relationship: float = 0.0
) -> DestinyContext:
    """
    Create DestinyContext from V3.5 calculate_year_score result
    
    Args:
        year: Year number
        pillar: Year pillar string
        v35_result: Result dict from calculate_year_score
        career/wealth/relationship: Dimension scores
    """
    score = v35_result.get('score', 0.0)
    icon = v35_result.get('treasury_icon')
    risk = v35_result.get('treasury_risk', 'none')
    details = v35_result.get('details', [])
    
    # Determine display color
    color_map = {
        'opportunity': '#FFD700',
        'warning': '#FF6B35',
        'danger': '#DC2626',
        'none': '#94A3B8'
    }
    
    # Extract tags from details
    tags = []
    is_treasury = False
    treasury_type = None
    treasury_elem = None
    
    for detail in details:
        if '身强' in detail:
            tags.append('身强胜财')
        elif '身弱' in detail:
            tags.append('身弱不胜财')
        
        if '财库' in detail:
            is_treasury = True
            treasury_type = 'Wealth'
            # Extract element from detail
            if '库[' in detail:
                start = detail.find('[') + 1
                end = detail.find(']')
                if start > 0 and end > start:
                    treasury_elem = detail[start:end]
        elif '库' in detail:
            is_treasury = True
    
    ctx = DestinyContext(
        year=year,
        pillar=pillar,
        score=score,
        raw_score=score,
        is_treasury_open=is_treasury,
        treasury_type=treasury_type,
        treasury_element=treasury_elem,
        risk_level=risk,
        icon=icon,
        display_color=color_map.get(risk, '#94A3B8'),
        tags=tags,
        details=details,
        description='; '.join(details[:2]) if details else "",
        career=career,
        wealth=wealth,
        relationship=relationship,
        version="V3.5"
    )
    
    # Auto-build narrative prompt
    ctx.narrative_prompt = ctx.build_narrative_prompt()
    ctx.energy_level = ctx.get_energy_category()
    
    return ctx
