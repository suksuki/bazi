"""核心术语三语映射（ZH/EN/KO）。"""

STEMS = {
    "甲": {"ZH": "甲", "EN": "Jia", "KO": "갑"},
    "乙": {"ZH": "乙", "EN": "Yi", "KO": "을"},
    "丙": {"ZH": "丙", "EN": "Bing", "KO": "병"},
    "丁": {"ZH": "丁", "EN": "Ding", "KO": "정"},
    "戊": {"ZH": "戊", "EN": "Wu", "KO": "무"},
    "己": {"ZH": "己", "EN": "Ji", "KO": "기"},
    "庚": {"ZH": "庚", "EN": "Geng", "KO": "경"},
    "辛": {"ZH": "辛", "EN": "Xin", "KO": "신"},
    "壬": {"ZH": "壬", "EN": "Ren", "KO": "임"},
    "癸": {"ZH": "癸", "EN": "Gui", "KO": "계"},
}

BRANCHES = {
    "子": {"ZH": "子", "EN": "Zi", "KO": "자"},
    "丑": {"ZH": "丑", "EN": "Chou", "KO": "축"},
    "寅": {"ZH": "寅", "EN": "Yin", "KO": "인"},
    "卯": {"ZH": "卯", "EN": "Mao", "KO": "묘"},
    "辰": {"ZH": "辰", "EN": "Chen", "KO": "진"},
    "巳": {"ZH": "巳", "EN": "Si", "KO": "사"},
    "午": {"ZH": "午", "EN": "Wu", "KO": "오"},
    "未": {"ZH": "未", "EN": "Wei", "KO": "미"},
    "申": {"ZH": "申", "EN": "Shen", "KO": "신"},
    "酉": {"ZH": "酉", "EN": "You", "KO": "유"},
    "戌": {"ZH": "戌", "EN": "Xu", "KO": "술"},
    "亥": {"ZH": "亥", "EN": "Hai", "KO": "해"},
}

CONFLICT_WORD = {"ZH": "冲", "EN": "Clash", "KO": "충"}
COMBINE_WORD = {"ZH": "合", "EN": "Combine", "KO": "합"}

FIVE_ELEMENTS = {
    "木": {"ZH": "木", "EN": "Wood", "KO": "목"},
    "火": {"ZH": "火", "EN": "Fire", "KO": "화"},
    "土": {"ZH": "土", "EN": "Earth", "KO": "토"},
    "金": {"ZH": "金", "EN": "Metal", "KO": "금"},
    "水": {"ZH": "水", "EN": "Water", "KO": "수"},
}

TEN_GODS = {
    "比肩": {"ZH": "比肩", "EN": "Bi Jian (Peer)", "KO": "비견"},
    "劫财": {"ZH": "劫财", "EN": "Jie Cai (Rival Wealth)", "KO": "겁재"},
    "食神": {"ZH": "食神", "EN": "Shi Shen (Eating God)", "KO": "식신"},
    "伤官": {"ZH": "伤官", "EN": "Shang Guan (Hurting Officer)", "KO": "상관"},
    "偏财": {"ZH": "偏财", "EN": "Pian Cai (Indirect Wealth)", "KO": "편재"},
    "正财": {"ZH": "正财", "EN": "Zheng Cai (Direct Wealth)", "KO": "정재"},
    "七杀": {"ZH": "七杀", "EN": "Qi Sha (Seven Killings)", "KO": "칠살"},
    "正官": {"ZH": "正官", "EN": "Zheng Guan (Direct Officer)", "KO": "정관"},
    "偏印": {"ZH": "偏印", "EN": "Pian Yin (Indirect Resource)", "KO": "편인"},
    "正印": {"ZH": "正印", "EN": "Zheng Yin (Direct Resource)", "KO": "정인"},
}

RELATIONS = {
    "刑": {"ZH": "刑", "EN": "Punishment", "KO": "형"},
    "害": {"ZH": "害", "EN": "Harm", "KO": "해"},
    "破": {"ZH": "破", "EN": "Destruction", "KO": "파"},
    "冲": {"ZH": "冲", "EN": "Clash", "KO": "충"},
    "合": {"ZH": "合", "EN": "Combine", "KO": "합"},
}
