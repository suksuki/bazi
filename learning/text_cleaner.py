import re

class TextCleaner:
    """
    预处理层 (Pre-cleaning Layer)
    在送入 LLM 之前，使用高效的正则规则清洗掉明显的噪音。
    """
    
    # 垃圾词库 (Stop Phrases) - 废话、营销、口头禅
    STOP_PHRASES = [
        r"点赞", r"关注", r"订阅", r"小铃铛", r"直播间", r"粉丝", r"老铁", r"家人们", 
        r"点击下方链接", r"视频最后", r"下期再见", r"大家好", r"我是.*老师",
        r"就是说", r"那么", r"这个这个", r"呃", r"啊", r"其实", r"基本上",
        r"如有侵权", r"版权归", r"仅供参考", r"迷信", r"不信谣", r"不传谣"
    ]
    
    # 命理术语纠错表 (Correction Map) - 基于常见 Whisper 错误
    TERM_MAP = {
        r"四火": "巳火",
        r"深若": "身弱",
        r"深强": "身强",
        r"深望": "身旺",
        r"深坐": "身坐",
        r"才星": "财星",
        r"印行": "印星",
        r"七傻": "七杀",
        r"七杀": "七杀", # Normalize 
        r"商官": "伤官",
        r"比肩": "比肩",
        r"劫才": "劫财",
        r"食神": "食神",
        r"正印": "正印",
        r"偏印": "偏印",
        r"枭神": "枭神",
        r"日园": "日元",
        r"日煮": "日主",
        r"大韵": "大运",
        r"流年": "流年",
        r"八字": "八字", 
        r"五行": "五行",
    }
    
    # 拼音到中文映射 (Pinyin Map) - 用于视频字幕翻译
    PINYIN_MAP = {
        # 天干
        'jia': '甲', 'yi': '乙', 'bing': '丙', 'ding': '丁',
        'wu': '戊', 'ji': '己', 'geng': '庚', 'xin': '辛',
        'ren': '壬', 'gui': '癸',
        
        # 地支
        'zi': '子', 'chou': '丑', 'yin': '寅', 'mao': '卯',
        'chen': '辰', 'si': '巳', 'wu': '午', 'wei': '未',
        'shen': '申', 'you': '酉', 'xu': '戌', 'hai': '亥',
    }
    
    # 英文术语映射 (English Map) - 用于英文字幕翻译
    ENGLISH_MAP = {
        # 多词组合（必须先匹配）
        'san he bureau': '三合局',
        'day master': '日主',
        'life condition': '生活状况',
        
        # 基础术语
        'branches': '地支',
        'branch': '地支',
        'stems': '天干',
        'stem': '天干',
        'contains': '包含',
        'contain': '包含',
        
        # 五行
        'wood': '木',
        'fire': '火',
        'earth': '土',
        'metal': '金',
        'water': '水',
        
        # 格局
        'pattern': '格局',
        'bureau': '局',
        'seasonal': '季节',
        
        # 状态
        'strong': '强',
        'weak': '弱',
        'good': '好',
        'excellent': '优秀',
    }

    @staticmethod
    def clean(text):
        """
        Run the full cleaning pipeline.
        """
        if not text: return ""
        
        # 1. Basic Normalize
        text = text.replace("\n", " ").replace("\r", " ")
        
        # 2. Remove Junk Phrases (aggressive)
        for pattern in TextCleaner.STOP_PHRASES:
            text = re.sub(pattern, "", text)
            
        # 3. Term Correction (Phonetic Fixes)
        for wrong, right in TextCleaner.TERM_MAP.items():
            text = text.replace(wrong, right)
        
        # 3.5. Translate Pinyin and English (New V27.0)
        # Multi-word phrases first
        for eng, cn in TextCleaner.ENGLISH_MAP.items():
            if ' ' in eng:  # Multi-word
                pattern = re.compile(re.escape(eng), re.IGNORECASE)
                text = pattern.sub(cn, text)
        
        # Single words
        for eng, cn in TextCleaner.ENGLISH_MAP.items():
            if ' ' not in eng:  # Single word
                pattern = re.compile(r'\b' + re.escape(eng) + r'\b', re.IGNORECASE)
                text = pattern.sub(cn, text)
        
        # Pinyin
        for pinyin, cn in TextCleaner.PINYIN_MAP.items():
            pattern = re.compile(r'\b' + re.escape(pinyin) + r'\b', re.IGNORECASE)
            text = pattern.sub(cn, text)
            
        # 4. Collapse Whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        # 5. Length Check (if reduced too much, might be garbage)
        return text

    @staticmethod
    def normalize_rule_json(json_str):
        """
        Tries to fix common JSON formatting issues from LLM output.
        """
        # Remove markdown code blocks
        clean = json_str.replace("```json", "").replace("```", "").strip()
        
        return clean
