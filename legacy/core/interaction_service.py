from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TreasuryStatus:
    is_open: bool
    pillar_location: str  # 'year', 'month', 'day', 'hour'
    treasury_element: str # '辰', '戌', '丑', '未'
    key_element: str      # 流年地支 (The Key)
    action: str           # 'clash' (冲)

class InteractionService:
    # Defining clash rules: Bidirectional mapping
    CLASH_PAIRS = {
        '辰': '戌', '戌': '辰',
        '丑': '未', '未': '丑'
    }

    def detect_treasury_openings(self, current_year_branch: str, chart_branches: Dict[str, str]) -> List[TreasuryStatus]:
        """
        Detect if the annual branch clashes open any treasuries in the birth chart.
        :param current_year_branch: Annual Branch (e.g., '辰')
        :param chart_branches: Chart Branches {'year': '戌', 'month': '卯', ...}
        """
        results = []
        
        # 1. Check if the annual branch is a "Key" (Must be one of the four Earths)
        if current_year_branch not in self.CLASH_PAIRS:
            return [] # Current year is not Earth, cannot clash open a treasury (Simplified V3.0 logic)

        target_treasury = self.CLASH_PAIRS[current_year_branch]

        # 2. Scan every pillar in the chart
        for pillar, branch in chart_branches.items():
            # If the chart contains the target treasury, and it is clashed by the year -> OPEN
            if branch == target_treasury:
                status = TreasuryStatus(
                    is_open=True,
                    pillar_location=pillar,
                    treasury_element=branch, # e.g., '戌'
                    key_element=current_year_branch, # e.g., '辰'
                    action='clash'
                )
                results.append(status)
                
        return results
