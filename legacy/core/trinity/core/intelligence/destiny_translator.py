
"""
Destiny Translator (Multi-Style Unified Tool)
=============================================
A tool-class module for translating physical metrics into human narratives.
Supports multiple styles: Stephen Chow (Mo Lei Tau), Wong Kar-wai (Poetic).
"""

import random
from enum import Enum
from typing import Dict, Any, List, Optional

class TranslationStyle(Enum):
    STEPHEN_CHOW = "chow"
    WONG_KAR_WAI = "wkw"
    PLAIN = "plain"

class DestinyTranslator:
    """
    Standardized tool for destiny translation.
    """
    
    DICTIONARIES = {
        TranslationStyle.WONG_KAR_WAI: {
            "SAI": [
                "这一年，原本平静的湖底裂开了一道缝，那是光照进来的地方，也是惊雷炸响的瞬间。",
                "有些东西在彻底破碎之后，才露出了它最昂贵的内核。所有的秩序都将被重构。",
                "你站在时间的断层，听见结构崩塌的声音，那是命运在为你推倒旧墙。"
            ],
            "SIGNAL_LOSS": [
                "有些年份，你觉得自己是在和整个时空玩捉迷藏。你说话，世界不听；你伸手，空气散开。",
                "这是最孤独的共振，所有的‘落地’感都消失了。不要试图在浓雾里狂奔。",
                "你试图抓住风的形状，却发现手心只剩下一片虚无。"
            ],
            "COHERENCE": [
                "世界正在对你低语，而你恰好听懂了每一个字符。这是灵魂最完美的同步点。",
                "所有的碎片都在此刻归位，你甚至能听见齿轮严丝合缝转动的声音。",
                "你不需要大声呼喊，因为时空已经在你的脉搏里跳动。"
            ],
            "SINGULARITY": [
                "你走进了一段没有影子的时间。所有的过去都在这里坍缩，而未来还未被命名。",
                "这是因果的奇点，任何一个微小的念头，都会被重力放大成余生无法摆脱的引力。",
                "你站在时间的尽头，往回看是已燃尽的星云，往前看是尚未诞生的晨曦。"
            ],
            "WEALTH_STAGNANT": ["财富像是一场未曾察觉的深呼吸，在静默中蓄积。"],
            "WEALTH_TURBULENT": ["黄金在湍流中起舞，你必须学会在这场危险的华尔兹中，保持呼吸的频率。"],
            "REL_BOUND": ["你们的轨道被一种不可见的重力锁死，从此所有的自由，都是在对方半径里的起舞。"],
            "REL_UNBOUND": ["有些关系，就像是平行飞行的两颗流星，擦肩而过的瞬间，就是一辈子的距离。"]
        },
        TranslationStyle.STEPHEN_CHOW: {
            "SAI": [
                "做人如果没有梦想，跟咸鱼有什么分别？这一年，命运决定把你直接晒成咸鱼！",
                "想不到你的排骨这么硬！结构应力爆表，你是不是练过‘如来神掌’？",
                "好大的火气啊！SAI爆棚，这一波稳住，不然连火星人都救不了你。"
            ],
            "SIGNAL_LOSS": [
                "地球是很危险的，你快回火星吧！信号全无，大家完全不在一个频道上。",
                "凭你的智慧，我很难跟你解释。这是信号断层，连‘如花’都嫌弃你没共鸣。",
                "喂！你怎么搞的？IC掉进阴沟里了，现在就像在没有光的电影院里找眼镜。"
            ],
            "COHERENCE": [
                "正所谓位高权重责任轻，睡觉睡到自然醒！你现在的运气好到连酱爆都要跳舞。",
                "这种感觉，就像吃了‘黯然销魂饭’，全身毛孔都张开了！神交感应，无懈可击。",
                "大吉大利！你的频率和世界完全对齐，简直是万里挑一的武林奇才。"
            ],
            "SINGULARITY": [
                "这一波是宿命的交汇，就像月光宝盒带你穿越，可惜你忘了喊‘般若波罗蜜’。",
                "曾经有一份真诚的运气摆在我面前... 奇点到了，再不决定就只能等一万年了。",
                "火云邪神说：‘天下武功，唯快不破’。在这种因果坍缩的关头，你磨磨唧唧干什么？"
            ],
            "WEALTH_STAGNANT": ["现在的财富状态就像‘如花’的初恋，虽然很安静，但让人心里发毛。"],
            "WEALTH_TURBULENT": ["财源滚滚！像‘功夫’里的斧头帮出场，虽然气势很足，但小心被踢馆。"],
            "REL_BOUND": ["你们的轨道被锁死了，就像紧箍咒扣在猴子头上。除非你喊：‘爱你一万年’！"],
            "REL_UNBOUND": ["没眼缘就是没眼缘。现在的感情状态就像跑龙套的没剧本，各走各路。"]
        }
    }

    def __init__(self, style: TranslationStyle = TranslationStyle.STEPHEN_CHOW):
        self.style = style

    def set_style(self, style: TranslationStyle):
        self.style = style

    def translate_state(self, state: Dict[str, Any]) -> str:
        """
        Synthesizes a master narrative from the Unified State metrics.
        """
        physics = state.get("physics", {})
        entropy = physics.get("entropy", 0.0)
        stress = physics.get("stress", {})
        sai = stress.get("SAI", 0.0)
        ic = stress.get("IC", 1.0)
        
        wealth = physics.get("wealth", {})
        rel = physics.get("relationship", {})
        
        verdicts = []
        d = self.DICTIONARIES.get(self.style, self.DICTIONARIES[TranslationStyle.STEPHEN_CHOW])
        
        # Core Logic
        if sai > 2.26:
            verdicts.append(random.choice(d["SAI"]))
        elif ic < 0.2:
            verdicts.append(random.choice(d["SIGNAL_LOSS"]))
        elif entropy > 1.5:
            verdicts.append(random.choice(d["SINGULARITY"]))
        elif ic > 0.8:
            verdicts.append(random.choice(d["COHERENCE"]))
            
        # Optional Context injection
        if wealth.get("State") == "TURBULENT":
            verdicts.append(random.choice(d["WEALTH_TURBULENT"]))
        elif rel.get("State") == "BOUND":
            verdicts.append(random.choice(d["REL_BOUND"]))
            
        if not verdicts:
            fallback = "如果你能预测未来，那未来就不叫未来了。" if self.style == TranslationStyle.WONG_KAR_WAI \
                       else "你以为躲在这里我就找不到你吗？没用的，像你这么拉风的男人，无论在哪里，都像漆黑中的萤火虫一样夺目。"
            verdicts = [fallback]
            
        return " ".join(verdicts)

    def get_event_mantra(self, year_metrics: Dict[str, Any]) -> str:
        """
        Translates a specific year's risk/event node into a narrative.
        """
        metrics = year_metrics.get("metrics", {})
        sai = metrics.get("sai", 0.0)
        ic = metrics.get("ic", 0.0)
        entropy = metrics.get("entropy", 0.0)
        topic = year_metrics.get("topic", "structure")
        
        d = self.DICTIONARIES.get(self.style, self.DICTIONARIES[TranslationStyle.STEPHEN_CHOW])
        
        if topic == "wealth":
            return random.choice(d["WEALTH_TURBULENT"]) if sai > 1.2 else random.choice(d["WEALTH_STAGNANT"])
        
        if topic == "relationship":
            return random.choice(d["REL_BOUND"]) if ic > 0.6 else random.choice(d["REL_UNBOUND"])
            
        if sai > 2.26:
            return random.choice(d["SAI"])
        
        if ic < 0.2:
            return random.choice(d["SIGNAL_LOSS"])
            
        if entropy > 1.8:
            return random.choice(d["SINGULARITY"])
            
        return "“气场正在进行一次长达三年的深呼吸。命运的齿轮还在咬合中。”"
