import json
import os

def create_golden_v4():
    """
    创建 Golden Dataset V4.0 - 真实名人高难度案例集
    专注于测试：
    1. 假从格 (Fake Follower)
    2. 调候局 (Climate Dependency)
    3. 通关局 (Mediation)
    4. 库根局 (Vault Roots)
    """
    data = [
        # --- 组 1: 根气陷阱 (看似无根，实则库中有根) ---
        {
            "id": "REAL_V4_001",
            "name": "Bill Gates (比尔·盖茨)",
            "bazi": ["乙未", "丙戌", "壬戌", "辛亥"],
            "gender": "男",
            "day_master": "壬",
            "true_label": "Strong",
            "description": "【印比帮身】壬水生于戌月（七杀/财库）失令。但时支亥水为归禄强根，天干辛金正印贴身相生。虽月令不帮，但党众极多。身旺。"
        },
        {
            "id": "REAL_V4_002",
            "name": "Barack Obama (奥巴马)",
            "bazi": ["辛丑", "乙未", "己巳", "癸酉"],
            "day_master": "己",
            "gender": "男",
            "true_label": "Balanced",
            "description": "【中和偏旺】己土生于未月得令，坐下巳火帝旺。身极强。但地支巳酉丑三合金局（食伤），天干透癸水（财）。身旺有强泄，达成完美平衡。"
        },

        # --- 组 2: 专旺与假从 (极值的判断) ---
        {
            "id": "REAL_V4_003",
            "name": "Donald Trump (特朗普)",
            "bazi": ["丙戌", "甲午", "己未", "己巳"],
            "day_master": "己",
            "gender": "男",
            "true_label": "Special_Vibrant",
            "description": "【火土专旺】己土生于午月（建禄），地支巳午未三会火局。全盘火土，甲木无根被火焚。这是经典的专旺格（从强）。"
        },
        {
            "id": "REAL_V4_004",
            "name": "Adolf Hitler (希特勒)",
            "bazi": ["己丑", "戊辰", "丙寅", "丁酉"],
            "day_master": "丙",
            "gender": "男",
            "true_label": "Strong",
            "description": "【身强食伤泄】丙火生于辰月（食伤），看似泄气。但坐下寅木长生，且丙丁火透干帮身，土虽重但有木疏。身旺，食伤生财为用。"
        },

        # --- 组 3: 通关局 (测试 V54 的 Mediation 逻辑) ---
        {
            "id": "REAL_V4_005",
            "name": "Mao Zedong (毛泽东)",
            "bazi": ["癸巳", "甲子", "丁酉", "甲辰"],
            "day_master": "丁",
            "gender": "男",
            "true_label": "Strong",
            "description": "【杀印相生】丁火生于子月（七杀），水克火。但天干双甲木高透（正印），地支子辰合水生木。杀（水）生印（木），印生身（火）。经典的通关成就大业。"
        },
        {
            "id": "REAL_V4_006",
            "name": "Emperor Taizong (李世民)",
            "bazi": ["戊午", "乙丑", "戊午", "乙卯"], 
            "day_master": "戊",
            "gender": "男",
            "true_label": "Strong",
            "description": "【官杀混杂但身强】地支双午（阳刃），身极旺。天干双乙木官杀克身。身强足以抗杀，无需通关，直接抗。测试阳刃对克制的抵御力。"
        },

        # --- 组 4: 调候局 (为 V58 气候层做准备) ---
        {
            "id": "REAL_V4_007",
            "name": "Jackie Chan (成龙)",
            "bazi": ["甲午", "戊辰", "癸巳", "癸亥"], # 此时辰一般推测
            "day_master": "癸",
            "gender": "男",
            "true_label": "Balanced",
            "description": "【身财两停】癸水生于辰月（水库），时支亥水帮身。身不弱。但坐下巳火财星，年支午火。水火既济，身财两停。"
        },
        {
            "id": "REAL_V4_008",
            "name": "Stephen Hawking (霍金)",
            "bazi": ["辛巳", "辛丑", "辛酉", "丙申"], # 丙申时为推测
            "day_master": "辛",
            "gender": "男",
            "true_label": "Special_Vibrant",
            "description": "【金神格/润下?】地支巳酉丑三合金局。全盘皆金。丙火被辛合化水（或合化金）。极强之格。"
        },

        # --- 组 5: 自刑与冲战 (测试 V57.4 的逻辑) ---
        {
            "id": "REAL_V4_009",
            "name": "Empress Wu Zetian (武则天)",
            "bazi": ["甲申", "丙寅", "甲午", "甲子"],
            "day_master": "甲",
            "gender": "女",
            "true_label": "Strong",
            "description": "【全冲格】寅申冲，子午冲。地支全动。但甲木生于寅月（建禄），身极旺。测试'阳刃/建禄逢冲'是否依然算强。"
        },
        {
            "id": "REAL_V4_010",
            "name": "Bruce Lee (李小龙)",
            "bazi": ["庚辰", "戊子", "甲戌", "戊辰"],
            "day_master": "甲",
            "gender": "男",
            "true_label": "Strong",
            "description": "【印旺】甲木生于子月（正印）。地支申子辰（虽无申，但子辰半合水局）。水极其旺。身强。"
        },

        # --- 补充案例 ---
        {
            "id": "REAL_V4_011", 
            "name": "Warren Buffett (巴菲特)", 
            "bazi": ["庚午", "甲申", "壬子", "戊申"], 
            "gender": "男", 
            "day_master": "壬", 
            "true_label": "Strong", 
            "description": "印比极强"
        },
        {
            "id": "REAL_V4_012", 
            "name": "Steve Jobs (乔布斯)", 
            "bazi": ["乙未", "戊寅", "丙辰", "丙申"], 
            "gender": "男", 
            "day_master": "丙", 
            "true_label": "Weak", 
            "description": "印虽有但泄耗重，偏弱"
        },
        {
            "id": "REAL_V4_013", 
            "name": "Lionel Messi (梅西)", 
            "bazi": ["丁卯", "丙午", "甲辰", "庚午"], 
            "gender": "男", 
            "day_master": "甲", 
            "true_label": "Weak", 
            "description": "木生火泄气太过"
        },
        {
            "id": "REAL_V4_014", 
            "name": "Michael Jackson", 
            "bazi": ["戊戌", "庚申", "戊寅", "甲寅"], 
            "gender": "男", 
            "day_master": "戊", 
            "true_label": "Weak", 
            "description": "食伤泄身，官杀克身"
        },
        {
            "id": "REAL_V4_015", 
            "name": "Putin", 
            "bazi": ["壬辰", "己酉", "丙戌", "癸巳"], 
            "gender": "男", 
            "day_master": "丙", 
            "true_label": "Weak", 
            "description": "财生官杀，身弱"
        }
    ]

    os.makedirs('data', exist_ok=True)
    file_path = 'data/golden_cases_v4.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Golden Dataset V4.0 已生成: {file_path} (共 {len(data)} 个案例)")

if __name__ == "__main__":
    create_golden_v4()

