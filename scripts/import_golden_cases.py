#!/usr/bin/env python3
"""临时脚本：导入33个精选八字案例"""

import json
import os
from pathlib import Path

project_root = Path(__file__).parent.parent

data = [
  {
    "id": "REAL_S_001",
    "bazi": ["辛卯", "丁酉", "庚午", "丙子"],
    "day_master": "庚",
    "gender": "男",
    "true_label": "Strong",
    "description": "乾隆皇帝：子午冲，卯酉冲，但在帝王哲学中，阳刃格身旺抗杀，金神得火炼。此为经典身旺抗杀格。"
  },
  {
    "id": "REAL_S_002",
    "bazi": ["癸亥", "癸亥", "癸亥", "乙卯"],
    "day_master": "癸",
    "gender": "男",
    "true_label": "Strong",
    "description": "专旺格（润下格）：地支亥卯半合木，但在水旺的季节，且三亥自刑，水气滔天。典型专旺。"
  },
  {
    "id": "REAL_S_003",
    "bazi": ["戊戌", "己未", "戊戌", "丙辰"],
    "day_master": "戊",
    "gender": "男",
    "true_label": "Strong",
    "description": "专旺格（稼穑格）：全盘土气，辰戌冲激起土旺，火生土。极强之土。"
  },
  {
    "id": "REAL_S_004",
    "bazi": ["甲寅", "丙寅", "甲子", "甲子"],
    "day_master": "甲",
    "gender": "男",
    "true_label": "Strong",
    "description": "专旺格（曲直格）：木生春月，地支寅木，天干透甲丙。双子水印星生身。极强。"
  },
  {
    "id": "REAL_S_005",
    "bazi": ["辛未", "辛丑", "庚戌", "丁亥"],
    "day_master": "庚",
    "gender": "男",
    "true_label": "Strong",
    "description": "塑胶大亨（验证集）：润局案例。亥水润泽未戌燥土，土生金，印星得用，身由弱转旺。"
  },
  {
    "id": "REAL_S_006",
    "bazi": ["己巳", "辛未", "庚午", "丁亥"],
    "day_master": "庚",
    "gender": "女",
    "true_label": "Strong",
    "description": "润局案例2：生于未月燥土，但在亥时，亥水润土生金，且庚金在巳中有长生，在未中有余气。身旺担官杀。"
  },
  {
    "id": "REAL_S_007",
    "bazi": ["壬申", "壬子", "庚辰", "乙酉"],
    "day_master": "庚",
    "gender": "男",
    "true_label": "Strong",
    "description": "合化案例：申子辰三合水局，乙庚合化金（有争议，但在此局中金水同源）。日主庚金得令得地，身极旺。"
  },
  {
    "id": "REAL_S_008",
    "bazi": ["甲子", "丙寅", "己巳", "戊辰"],
    "day_master": "己",
    "gender": "男",
    "true_label": "Strong",
    "description": "印比帮身：己土生于寅月死地，但坐下巳火帝旺，时柱戊辰强力帮身，丙火高透。身旺。"
  },
  {
    "id": "REAL_S_009",
    "bazi": ["丁酉", "己酉", "辛酉", "己丑"],
    "day_master": "辛",
    "gender": "男",
    "true_label": "Strong",
    "description": "专旺格（从革格）：地支巳酉丑三合金局（虽无巳，但酉丑半合），天干己土生金。极强。"
  },
  {
    "id": "REAL_S_010",
    "bazi": ["壬子", "癸丑", "壬寅", "辛亥"],
    "day_master": "壬",
    "gender": "女",
    "true_label": "Strong",
    "description": "身强案例：亥子丑三会水局，金水相涵。身极旺。"
  },
  {
    "id": "REAL_S_011",
    "bazi": ["戊辰", "戊午", "戊戌", "戊午"],
    "day_master": "戊",
    "gender": "男",
    "true_label": "Strong",
    "description": "专旺格（火土同心）：印比重重，极强。"
  },
  {
    "id": "REAL_W_001",
    "bazi": ["戊辰", "己未", "壬戌", "癸卯"],
    "day_master": "壬",
    "gender": "男",
    "true_label": "Weak",
    "description": "杀重身轻：壬水生于未月，四柱土旺攻身，仅靠时干癸水微弱帮身。极弱（可能从杀，但有微根）。"
  },
  {
    "id": "REAL_W_002",
    "bazi": ["庚寅", "甲申", "甲申", "庚午"],
    "day_master": "甲",
    "gender": "男",
    "true_label": "Weak",
    "description": "杀重身轻：甲木生于申月绝地，七杀庚金双透，地支双申冲寅（禄被冲）。身极弱。"
  },
  {
    "id": "REAL_W_003",
    "bazi": ["丙申", "丙申", "丙申", "丙申"],
    "day_master": "丙",
    "gender": "男",
    "true_label": "Weak",
    "description": "财多身弱：虽然天干四丙，但地支四申金财星极旺，丙火无根（申中只有壬水克火）。典型的身弱财旺。"
  },
  {
    "id": "REAL_W_004",
    "bazi": ["乙酉", "乙酉", "乙酉", "乙酉"],
    "day_master": "乙",
    "gender": "男",
    "true_label": "Weak",
    "description": "从杀格：乙木无根，地支全金，天干全乙也被金克。不得不从杀。在此体系中标记为 Weak (Ratio < 20%)。"
  },
  {
    "id": "REAL_W_005",
    "bazi": ["丁巳", "丁未", "辛卯", "丁酉"],
    "day_master": "辛",
    "gender": "女",
    "true_label": "Weak",
    "description": "七杀攻身：天干三丁火克辛金，地支巳未拱火，卯木生火。辛金虽有酉根但被冲克。身弱。"
  },
  {
    "id": "REAL_W_006",
    "bazi": ["戊戌", "戊午", "壬戌", "戊申"],
    "day_master": "壬",
    "gender": "男",
    "true_label": "Weak",
    "description": "杀重身轻：全盘火土，壬水被戊土围困，仅靠申金生水，但申被午火克。身弱。"
  },
  {
    "id": "REAL_W_007",
    "bazi": ["癸巳", "丁巳", "癸巳", "丁巳"],
    "day_master": "癸",
    "gender": "男",
    "true_label": "Weak",
    "description": "财多身弱：地支四巳火财星，天干双丁火，癸水被蒸发殆尽。身极弱（从财）。"
  },
  {
    "id": "REAL_W_008",
    "bazi": ["甲戌", "甲戌", "甲戌", "甲戌"],
    "day_master": "甲",
    "gender": "男",
    "true_label": "Weak",
    "description": "从财格：地支全土，甲木虽多但无根（戌中辛金克木），且燥土不生木。甲木从土。"
  },
  {
    "id": "REAL_W_009",
    "bazi": ["辛卯", "辛卯", "辛卯", "辛卯"],
    "day_master": "辛",
    "gender": "女",
    "true_label": "Weak",
    "description": "从财格：辛金坐绝地，地支全木，天干虚浮无根。身弱从财。"
  },
  {
    "id": "REAL_W_010",
    "bazi": ["庚午", "壬午", "丙午", "壬辰"],
    "day_master": "丙",
    "gender": "男",
    "true_label": "Weak",
    "description": "变格（极弱）：虽是丙午日柱（羊刃），但生于午月火旺，地支三午自刑，天干双壬水冲克丙火。这是一种特殊的弱（羊刃倒戈）。"
  },
  {
    "id": "REAL_W_011",
    "bazi": ["庚寅", "庚辰", "戊寅", "甲寅"],
    "day_master": "戊",
    "gender": "男",
    "true_label": "Weak",
    "description": "杀重身轻：地支三寅木，甲木透干克戊土。戊土虽在辰有根，但被木克死。弱。"
  },
  {
    "id": "REAL_B_001",
    "bazi": ["甲子", "丙寅", "庚午", "己卯"],
    "day_master": "庚",
    "gender": "男",
    "true_label": "Balanced",
    "description": "中和案例：庚金生寅月弱，但有己土生，日支午火克。天干甲木生丙火克庚。能量流转平衡，不强不弱。"
  },
  {
    "id": "REAL_B_002",
    "bazi": ["癸酉", "甲子", "丁卯", "丙午"],
    "day_master": "丁",
    "gender": "女",
    "true_label": "Balanced",
    "description": "身杀两停：丁生子月弱，但坐卯木印星，时柱丙午强根帮身。癸水七杀有甲木化。平衡。"
  },
  {
    "id": "REAL_B_003",
    "bazi": ["戊辰", "甲寅", "戊辰", "甲寅"],
    "day_master": "戊",
    "gender": "男",
    "true_label": "Balanced",
    "description": "身杀两停：土木交战。戊土坐辰有根，甲木坐寅得令。两强相争，力量相当。"
  },
  {
    "id": "REAL_B_004",
    "bazi": ["乙丑", "己丑", "癸巳", "癸亥"],
    "day_master": "癸",
    "gender": "男",
    "true_label": "Balanced",
    "description": "中和：癸水生丑月有气，时柱癸亥帮身。月干己土透出克水，坐下巳火耗水。比劫与官杀抗衡。"
  },
  {
    "id": "REAL_B_005",
    "bazi": ["丁酉", "乙巳", "己丑", "乙亥"],
    "day_master": "己",
    "gender": "女",
    "true_label": "Balanced",
    "description": "中和：己土生巳月得令，巳酉丑合金局泄土，天干双乙木克土。印旺但被泄被克，达到动态平衡。"
  },
  {
    "id": "REAL_B_006",
    "bazi": ["壬申", "戊申", "壬寅", "戊申"],
    "day_master": "壬",
    "gender": "男",
    "true_label": "Balanced",
    "description": "身杀两停：壬水生申月得长生，但三申冲一寅，天干双戊土克壬水。食神制杀格，能量纠缠平衡。"
  },
  {
    "id": "REAL_B_007",
    "bazi": ["庚辰", "己卯", "甲寅", "庚午"],
    "day_master": "甲",
    "gender": "男",
    "true_label": "Balanced",
    "description": "中和：甲木得令得地，身旺。但双庚金克木，午火泄木，己土耗木。克泄耗并重，拉低了身旺程度。"
  },
  {
    "id": "REAL_B_008",
    "bazi": ["丙戌", "庚子", "辛未", "己丑"],
    "day_master": "辛",
    "gender": "女",
    "true_label": "Balanced",
    "description": "润局平衡：润局案例3。辛金生子月失令，但地支丑未戌三刑土旺生金，子丑合土。寒湿土生金，身转中和。"
  },
  {
    "id": "REAL_B_009",
    "bazi": ["甲午", "庚午", "丙午", "甲午"],
    "day_master": "丙",
    "gender": "男",
    "true_label": "Balanced",
    "description": "特殊中和：地支全火，看似极旺，但天干庚金劈甲引丁（虽弱），且火多木焚。在某些体系中视为炎上格（Strong），但在此处作为极端边界测试，看图网络是否能识别出火土燥烈无泄的隐患（Balanced/Weak boundary）。"
  },
  {
    "id": "REAL_B_010",
    "bazi": ["乙亥", "丁亥", "辛巳", "丙申"],
    "day_master": "辛",
    "gender": "女",
    "true_label": "Balanced",
    "description": "合化平衡：丙辛合化水（在亥月），地支巳申合水。化气是否成功是关键。若化水则从势，若不化则中和偏弱。用于测试合化逻辑。"
  },
  {
    "id": "REAL_B_011",
    "bazi": ["癸亥", "甲子", "丙戌", "戊子"],
    "day_master": "丙",
    "gender": "男",
    "true_label": "Balanced",
    "description": "官印相生：水旺，但甲木透干泄水生火，丙火坐戌有根。身弱有气，官印相生达到平衡。"
  }
]

if __name__ == "__main__":
    data_path = project_root / "data" / "golden_cases.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已写入 {len(data)} 个案例到 {data_path}")

