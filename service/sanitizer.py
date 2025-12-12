# service/sanitizer.py
"""
Sanitizer Module
Project Crimson Vein - Pre-processing Layer

Responsible for cleaning, normalizing, and translating raw text 
BEFORE it enters the LLM extraction pipeline.
"""

import re
from typing import Dict

class Sanitizer:
    # Rodden Rating to Quality Tier
    RODDEN_MAP = {
        "AA": "A", # Birth Certificate
        "A": "B",  # Memory
        "B": "B",  # Bio/Autobiography
        "C": "C",  # Caution (no source)
        "DD": "C", # Dirty Data (conflicting)
        "X": "C"   # No time
    }

    # Event Type Translation (English -> Standard Type)
    EVENT_MAP = {
        "marriage": "Marriage",
        "wedding": "Marriage",
        "divorce": "Divorce",
        "death": "Death",
        "died": "Death",
        "birth of child": "ChildBirth",
        "career start": "Career_Start",
        "career promotion": "Career_Promotion",
        "bankruptcy": "Wealth_Loss",
        "acquisition": "Wealth_Windfall",
        "illness": "Health_Issue",
        "surgery": "Health_Issue",
        "accident": "Accident",
        "award": "Achievement"
    }

    # Stem/Branch Translation (English/Pinyin -> Chinese)
    # 扩展了现有的 cleaner 逻辑
    TERM_MAP = {
        # Stems
        'jia': '甲', 'wood yang': '甲', 'yang wood': '甲',
        'yi': '乙', 'wood yin': '乙', 'yin wood': '乙',
        'bing': '丙', 'fire yang': '丙', 'yang fire': '丙',
        'ding': '丁', 'fire yin': '丁', 'yin fire': '丁',
        'wu': '戊', 'earth yang': '戊', 'yang earth': '戊',
        'ji': '己', 'earth yin': '己', 'yin earth': '己',
        'geng': '庚', 'metal yang': '庚', 'yang metal': '庚',
        'xin': '辛', 'metal yin': '辛', 'yin metal': '辛',
        'ren': '壬', 'water yang': '壬', 'yang water': '壬',
        'gui': '癸', 'water yin': '癸', 'yin water': '癸',
        
        # Branches
        'zi': '子', 'rat': '子',
        'chou': '丑', 'ox': '丑',
        'yin': '寅', 'tiger': '寅',
        'mao': '卯', 'rabbit': '卯',
        'chen': '辰', 'dragon': '辰',
        'si': '巳', 'snake': '巳',
        'wu': '午', 'horse': '午',
        'wei': '未', 'goat': '未', 'sheep': '未',
        'shen': '申', 'monkey': '申',
        'you': '酉', 'rooster': '酉',
        'xu': '戌', 'dog': '戌',
        'hai': '亥', 'pig': '亥',

        # Ten Gods (English -> Chinese)
        'seven killings': '七杀', '7 killings': '七杀',
        'direct officer': '正官', 'officer': '正官',
        'direct wealth': '正财', 'indirect wealth': '偏财',
        'hurting officer': '伤官', 'eating god': '食神',
        'direct resource': '正印', 'indirect resource': '偏印',
        'friend': '比肩', 'rob wealth': '劫财'
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Main cleaning function.
        """
        if not text:
            return ""

        # 1. Lowercase for matching
        clean_text = text # Keep original casing for extraction? No, LLM handles it.
        # Actually, let's keep case for names, but lower for keywords.
        # For simple regex replacement, we use ignorecase flag.

        # 2. Translate Terms (Pinyin/English -> Chinese)
        # Sort by length desc to avoid partial matches (e.g. 'yin wood' before 'yin')
        sorted_keys = sorted(Sanitizer.TERM_MAP.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            val = Sanitizer.TERM_MAP[key]
            pattern = re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE)
            clean_text = pattern.sub(val, clean_text)

        # 3. Clean format artifacts
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text

    @staticmethod
    def map_quality(rodden: str) -> str:
        """Map Rodden Rating to our Tier system"""
        return Sanitizer.RODDEN_MAP.get(rodden.upper(), "C")

if __name__ == "__main__":
    # Test
    raw = "Elon Musk born in 1971. Day Master is Yang Wood. Born in the year of Metal Pig."
    print(f"Original: {raw}")
    print(f"Cleaned:  {Sanitizer.clean_text(raw)}")
