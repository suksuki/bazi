
import pandas as pd
import numpy as np

class InsightGenerator:
    """
    Analyzes the Quantum Trajectory DataFrame and generates
    human-readable narrative, identifying peaks, valleys, and golden ages.
    """
    
    def generate_narrative(self, df: pd.DataFrame):
        """
        Input: DataFrame with columns like 'age', 'year', 'Total_mean', 'Career_mean'...
        Output: Dictionary { "Total": "Summary text...", "Career": "..." }
        """
        insights = {}
        
        # Identify aspect columns
        aspect_cols = [c for c in df.columns if c.endswith('_mean')]
        
        for col in aspect_cols:
            aspect_name = col.replace("_mean", "")
            series = df[col]
            ages = df['age']
            years = df['year']
            
            # 1. Basic Stats
            avg_score = series.mean()
            max_score = series.max()
            min_score = series.min()
            max_idx = series.idxmax()
            min_idx = series.idxmin()
            
            peak_age = int(ages[max_idx])
            peak_year = int(years[max_idx])
            low_age = int(ages[min_idx])
            low_year = int(years[min_idx])
            
            # 2. Identify "Golden Periods" (Consecutive years > 70 or > Mean + 0.5 Std)
            threshold = max(60, avg_score + 5)
            golden_periods = self._find_periods(series, threshold)
            
            # 3. Identify "Challenge Periods" (Consecutive years < 40 or < Mean - 10)
            low_threshold = min(40, avg_score - 10)
            challenge_periods = self._find_periods(series, low_threshold, condition="below")

            # 4. Construct Narrative
            # Intro
            if avg_score > 65:
                tone = "非常强劲 (Very Strong)"
            elif avg_score > 55:
                tone = "稳健向好 (Stable)"
            elif avg_score > 45:
                tone = "平稳波动 (Average)"
            else:
                tone = "挑战较多 (Challenging)"
                
            text = f"**{aspect_name}** 总评：{tone} (均分 {avg_score:.1f})。\n\n"
            
            # Peak Info
            text += f"🚀 **高光时刻**：您在 **{peak_year}年 ({peak_age}岁)** 达到巅峰，能量指数高达 **{max_score:.1f}**。\n"
            
            # Golden Periods
            if golden_periods:
                periods_str = ", ".join([f"{years[s]}~{years[e]} ({ages[s]:.0f}-{ages[e]:.0f}岁)" for s, e in golden_periods])
                text += f"🌟 **黄金周期**：{periods_str} 是您运势最旺盛的时间段，建议大胆进取。\n"
            else:
                text += "🌟 **黄金周期**：运势较为平均，需把握每年的流月机会。\n"
                
            # Valley Info
            text += f"⚠️ **低谷警示**：**{low_year}年 ({low_age}岁)** 附近可能面临压力 (指数 {min_score:.1f})，建议保守行事。\n"
            
            if challenge_periods:
                 periods_str = ", ".join([f"{years[s]}~{years[e]}" for s, e in challenge_periods])
                 text += f"🛡️ **守成期**：{periods_str} 期间建议韬光养晦，积累沉淀。"
            
            insights[aspect_name] = text
            
        return insights

    def _find_periods(self, series, threshold, condition="above"):
        """
        Returns list of tuples (start_idx, end_idx) where condition holds.
        """
        periods = []
        in_period = False
        start_idx = 0
        
        for i, val in enumerate(series):
            is_met = (val >= threshold) if condition == "above" else (val <= threshold)
            
            if is_met:
                if not in_period:
                    start_idx = i
                    in_period = True
            else:
                if in_period:
                    # Period ended
                    if i - start_idx >= 3: # Ignore blips < 3 units
                        periods.append((start_idx, i-1))
                    in_period = False
        
        # Close trailing
        if in_period and (len(series) - start_idx >= 3):
            periods.append((start_idx, len(series)-1))
            
        return periods
