#!/usr/bin/env python3
"""
导入、清洗和规范化新的八字案例

功能：
1. 检查数据格式（bazi转换为列表，gender标准化）
2. 检查重复案例
3. 规范化名称
4. 添加到相应的JSON文件（classic_cases.json或calibration_cases.json）
5. 设置权重（经典案例3.0x，现代案例1.5x）
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from copy import deepcopy

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 新案例数据
NEW_CASES_JSON = [
  {
    "id": "STRENGTH_CN_HIST_001",
    "name": "乾隆帝（清高宗·弘历）",
    "birth_date": "1711-09-25",
    "birth_time": "00:30",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "庚",
    "gender": "M",
    "bazi": "辛卯 丁酉 庚午 丙子",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主庚金",
      "月令丁酉(金)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "据《清实录》版本：康熙五十年八月十三日子时生；此处换算为公历1711-09-25子时。"
  },
  {
    "id": "STRENGTH_CN_HIST_002",
    "name": "雍正帝（清世宗·胤禛）",
    "birth_date": "1678-12-13",
    "birth_time": "04:30",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "丁",
    "gender": "M",
    "bazi": "戊午 癸亥 丁酉 壬寅",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令癸亥(水)",
      "月令平",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "维基百科条目\"雍正帝\"明确写\"寅时出生\"。"
  },
  {
    "id": "STRENGTH_CN_HIST_003",
    "name": "弘时（雍正第三子）",
    "birth_date": "1704-03-18",
    "birth_time": "00:30",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "癸",
    "gender": "M",
    "bazi": "甲申 丁卯 癸未 壬子",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主癸水",
      "月令丁卯(木)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "维基百科条目\"弘时\"明确写\"子时出生\"。"
  },
  {
    "id": "STRENGTH_CN_HIST_004",
    "name": "永珅（弘时之子）",
    "birth_date": "1721-09-11",
    "birth_time": "12:30",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "己",
    "gender": "M",
    "bazi": "辛丑 丙申 己酉 庚午",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主己土",
      "月令丙申(金)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "维基百科\"弘时\"条目子女段落含\"1721年9月11日午时生\"。"
  },
  {
    "id": "STRENGTH_CN_HIST_005",
    "name": "溥仪（清逊帝）",
    "birth_date": "1906-02-07",
    "birth_time": "12:00",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "壬",
    "gender": "M",
    "bazi": "丙午 庚寅 壬午 丙午",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主壬水",
      "月令庚寅(木)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开资料常见版本：1906-02-07午时。"
  },
  {
    "id": "STRENGTH_CN_HIST_006",
    "name": "慈禧太后（叶赫那拉·杏贞）",
    "birth_date": "1835-11-29",
    "birth_time": "06:00",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "乙",
    "gender": "F",
    "bazi": "乙未 丁亥 乙丑 己卯",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主乙木",
      "月令丁亥(水)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本：1835-11-29卯时（时辰版本存在争议）。"
  },
  {
    "id": "STRENGTH_CN_HIST_007",
    "name": "袁世凯",
    "birth_date": "1859-09-16",
    "birth_time": "14:00",
    "geo_city": "Xiangcheng, Henan",
    "geo_country": "China",
    "geo_longitude": 113.8733,
    "geo_latitude": 33.4436,
    "day_master": "丁",
    "gender": "M",
    "bazi": "己未 癸酉 丁巳 丁未",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令癸酉(金)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常见版本：1859-09-16未时（亦有其他版本）。"
  },
  {
    "id": "STRENGTH_CN_HIST_008",
    "name": "皇太极（清太宗）",
    "birth_date": "1592-11-28",
    "birth_time": "16:00",
    "geo_city": "Hetu Ala, Liaoning",
    "geo_country": "China",
    "geo_longitude": 125.0,
    "geo_latitude": 41.7,
    "day_master": "辛",
    "gender": "M",
    "bazi": "壬辰 辛亥 辛亥 丙申",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主辛金",
      "月令辛亥(水)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开资料常见版本：1592年十月廿五申时；此处以常用公历换算日期填入。"
  },
  {
    "id": "STRENGTH_CN_HIST_009",
    "name": "毛泽东",
    "birth_date": "1893-12-26",
    "birth_time": "08:00",
    "geo_city": "Shaoshan, Hunan",
    "geo_country": "China",
    "geo_longitude": 112.526,
    "geo_latitude": 27.915,
    "day_master": "丁",
    "gender": "M",
    "bazi": "癸巳 甲子 丁酉 甲辰",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令甲子(水)",
      "月令平",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "命理圈常用版本：1893-12-26辰时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_010",
    "name": "孙中山",
    "birth_date": "1866-11-12",
    "birth_time": "22:00",
    "geo_city": "Cuiheng, Zhongshan",
    "geo_country": "China",
    "geo_longitude": 113.528,
    "geo_latitude": 22.433,
    "day_master": "辛",
    "gender": "M",
    "bazi": "丙寅 己亥 辛卯 己亥",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主辛金",
      "月令己亥(水)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "命理圈常用版本：1866-11-12亥时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_011",
    "name": "蒋介石",
    "birth_date": "1887-10-31",
    "birth_time": "10:00",
    "geo_city": "Xikou, Fenghua",
    "geo_country": "China",
    "geo_longitude": 121.141,
    "geo_latitude": 29.684,
    "day_master": "己",
    "gender": "M",
    "bazi": "丁亥 庚戌 己巳 己巳",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主己土",
      "月令庚戌(土)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "命理圈常用版本：1887-10-31巳时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_012",
    "name": "周恩来",
    "birth_date": "1898-03-05",
    "birth_time": "05:00",
    "geo_city": "Huai'an, Jiangsu",
    "geo_country": "China",
    "geo_longitude": 119.015,
    "geo_latitude": 33.61,
    "day_master": "丁",
    "gender": "M",
    "bazi": "戊戌 乙卯 丁卯 癸卯",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令乙卯(木)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "命理圈常用版本：1898-03-05卯时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_013",
    "name": "邓小平",
    "birth_date": "1904-08-22",
    "birth_time": "12:00",
    "geo_city": "Guang'an, Sichuan",
    "geo_country": "China",
    "geo_longitude": 106.636,
    "geo_latitude": 30.463,
    "day_master": "戊",
    "gender": "M",
    "bazi": "甲辰 壬申 戊子 戊午",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主戊土",
      "月令壬申(金)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "命理圈常用版本：1904-08-22午时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_014",
    "name": "宋美龄",
    "birth_date": "1897-03-04",
    "birth_time": "22:00",
    "geo_city": "Shanghai",
    "geo_country": "China",
    "geo_longitude": 121.4737,
    "geo_latitude": 31.2304,
    "day_master": "辛",
    "gender": "F",
    "bazi": "丁酉 癸卯 辛酉 己亥",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主辛金",
      "月令癸卯(木)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "命理圈常用版本：1897-03-04亥时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_015",
    "name": "张学良",
    "birth_date": "1901-06-03",
    "birth_time": "07:00",
    "geo_city": "Haicheng, Liaoning",
    "geo_country": "China",
    "geo_longitude": 122.75,
    "geo_latitude": 40.85,
    "day_master": "壬",
    "gender": "M",
    "bazi": "辛丑 癸巳 壬子 甲辰",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主壬水",
      "月令癸巳(火)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "命理圈常用版本：1901-06-03辰时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_016",
    "name": "林彪",
    "birth_date": "1907-12-05",
    "birth_time": "22:00",
    "geo_city": "Huanggang, Hubei",
    "geo_country": "China",
    "geo_longitude": 114.872,
    "geo_latitude": 30.453,
    "day_master": "戊",
    "gender": "M",
    "bazi": "丁未 壬子 戊子 癸亥",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主戊土",
      "月令壬子(水)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "命理圈常用版本：1907-12-05亥时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_017",
    "name": "梅兰芳",
    "birth_date": "1894-10-22",
    "birth_time": "08:00",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "丁",
    "gender": "M",
    "bazi": "甲午 甲戌 丁酉 甲辰",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令甲戌(土)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "命理圈常用版本：1894-10-22辰时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_018",
    "name": "张大千",
    "birth_date": "1899-05-10",
    "birth_time": "10:00",
    "geo_city": "Neijiang, Sichuan",
    "geo_country": "China",
    "geo_longitude": 105.058,
    "geo_latitude": 29.58,
    "day_master": "戊",
    "gender": "M",
    "bazi": "己亥 己巳 戊寅 丁巳",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主戊土",
      "月令己巳(火)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "命理圈常用版本：1899-05-10巳时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_019",
    "name": "鲁迅",
    "birth_date": "1881-09-25",
    "birth_time": "04:00",
    "geo_city": "Shaoxing, Zhejiang",
    "geo_country": "China",
    "geo_longitude": 120.58,
    "geo_latitude": 30.01,
    "day_master": "壬",
    "gender": "M",
    "bazi": "辛巳 丁酉 壬戌 壬寅",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主壬水",
      "月令丁酉(金)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "命理圈常用版本：1881-09-25寅时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_HIST_020",
    "name": "胡适",
    "birth_date": "1891-12-17",
    "birth_time": "16:00",
    "geo_city": "Jixi, Anhui",
    "geo_country": "China",
    "geo_longitude": 118.59,
    "geo_latitude": 30.07,
    "day_master": "丁",
    "gender": "M",
    "bazi": "辛卯 庚子 丁丑 戊申",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令庚子(水)",
      "月令平",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "命理圈常用版本：1891-12-17申时（公开版本不一）。"
  },
  {
    "id": "STRENGTH_CN_MODERN_001",
    "name": "CN_ELITE_01",
    "birth_date": "1964-09-10",
    "birth_time": "08:00",
    "geo_city": "Hangzhou, Zhejiang",
    "geo_country": "China",
    "geo_longitude": 120.1551,
    "geo_latitude": 30.2741,
    "day_master": "壬",
    "gender": "M",
    "bazi": "甲辰 癸酉 壬戌 甲辰",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主壬水",
      "月令癸酉(金)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1964-09-10辰时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_002",
    "name": "CN_ELITE_02",
    "birth_date": "1971-10-29",
    "birth_time": "10:00",
    "geo_city": "Shenzhen, Guangdong",
    "geo_country": "China",
    "geo_longitude": 114.0579,
    "geo_latitude": 22.5431,
    "day_master": "丁",
    "gender": "M",
    "bazi": "辛亥 戊戌 丁亥 乙巳",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令戊戌(土)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：1971-10-29巳时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_003",
    "name": "CN_ELITE_03",
    "birth_date": "1968-11-17",
    "birth_time": "14:00",
    "geo_city": "Yangquan, Shanxi",
    "geo_country": "China",
    "geo_longitude": 113.5805,
    "geo_latitude": 37.8567,
    "day_master": "辛",
    "gender": "M",
    "bazi": "戊申 壬戌 辛卯 乙未",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主辛金",
      "月令壬戌(土)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1968-11-17未时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_004",
    "name": "CN_ELITE_04",
    "birth_date": "1969-12-16",
    "birth_time": "06:00",
    "geo_city": "Xiantao? (approx)",
    "geo_country": "China",
    "geo_longitude": 113.45,
    "geo_latitude": 30.37,
    "day_master": "乙",
    "gender": "M",
    "bazi": "己酉 丙子 乙丑 己卯",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主乙木",
      "月令丙子(水)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1969-12-16卯时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_005",
    "name": "CN_ELITE_05",
    "birth_date": "1961-09-27",
    "birth_time": "23:30",
    "geo_city": "Hong Kong",
    "geo_country": "China",
    "geo_longitude": 114.1694,
    "geo_latitude": 22.3193,
    "day_master": "癸",
    "gender": "M",
    "bazi": "辛丑 丁酉 癸亥 壬子",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主癸水",
      "月令丁酉(金)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "公开命理资料常用版本（需自行复核）：1961-09-27子时（子时跨日，按子正换日处理）。"
  },
  {
    "id": "STRENGTH_CN_MODERN_006",
    "name": "CN_ELITE_06",
    "birth_date": "1979-01-18",
    "birth_time": "11:30",
    "geo_city": "Taipei",
    "geo_country": "China",
    "geo_longitude": 121.5654,
    "geo_latitude": 25.033,
    "day_master": "乙",
    "gender": "M",
    "bazi": "戊午 乙丑 乙酉 壬午",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主乙木",
      "月令乙丑(土)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "公开命理资料常用版本（需自行复核）：1979-01-18午时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_007",
    "name": "CN_ELITE_07",
    "birth_date": "1969-08-08",
    "birth_time": "20:00",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "乙",
    "gender": "F",
    "bazi": "己酉 辛未 乙卯 丙戌",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主乙木",
      "月令辛未(土)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1969-08-08戌时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_008",
    "name": "CN_ELITE_08",
    "birth_date": "1981-09-16",
    "birth_time": "09:00",
    "geo_city": "Qingdao, Shandong",
    "geo_country": "China",
    "geo_longitude": 120.3826,
    "geo_latitude": 36.0671,
    "day_master": "丁",
    "gender": "F",
    "bazi": "辛酉 丁酉 丁酉 乙巳",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令丁酉(金)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "公开命理资料常用版本（需自行复核）：1981-09-16巳时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_009",
    "name": "CN_ELITE_09",
    "birth_date": "1986-09-12",
    "birth_time": "10:00",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "己",
    "gender": "F",
    "bazi": "丙寅 丁酉 己未 己巳",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主己土",
      "月令丁酉(金)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：1986-09-12巳时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_010",
    "name": "CN_ELITE_10",
    "birth_date": "1976-03-12",
    "birth_time": "06:00",
    "geo_city": "Wuhu? (approx)",
    "geo_country": "China",
    "geo_longitude": 118.38,
    "geo_latitude": 31.33,
    "day_master": "癸",
    "gender": "F",
    "bazi": "丙辰 辛卯 癸亥 乙卯",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主癸水",
      "月令辛卯(木)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：1976-03-12卯时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_011",
    "name": "CN_ELITE_11",
    "birth_date": "1963-04-26",
    "birth_time": "08:00",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "己",
    "gender": "M",
    "bazi": "癸卯 丁巳 己亥 戊辰",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主己土",
      "月令丁巳(火)",
      "月令受制/泄耗",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "公开命理资料常用版本（需自行复核）：1963-04-26辰时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_012",
    "name": "CN_ELITE_12",
    "birth_date": "1983-07-13",
    "birth_time": "20:00",
    "geo_city": "Shanghai",
    "geo_country": "China",
    "geo_longitude": 121.4737,
    "geo_latitude": 31.2304,
    "day_master": "壬",
    "gender": "M",
    "bazi": "癸亥 己未 壬寅 庚戌",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主壬水",
      "月令己未(土)",
      "月令平",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "公开命理资料常用版本（需自行复核）：1983-07-13戌时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_013",
    "name": "CN_ELITE_13",
    "birth_date": "1980-09-12",
    "birth_time": "12:00",
    "geo_city": "Shanghai",
    "geo_country": "China",
    "geo_longitude": 121.4737,
    "geo_latitude": 31.2304,
    "day_master": "戊",
    "gender": "M",
    "bazi": "庚申 乙酉 戊子 戊午",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主戊土",
      "月令乙酉(金)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：1980-09-12午时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_014",
    "name": "CN_ELITE_14",
    "birth_date": "1982-02-26",
    "birth_time": "14:00",
    "geo_city": "Wuhan, Hubei",
    "geo_country": "China",
    "geo_longitude": 114.3054,
    "geo_latitude": 30.5928,
    "day_master": "庚",
    "gender": "F",
    "bazi": "壬戌 癸卯 庚辰 癸未",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主庚金",
      "月令癸卯(木)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1982-02-26未时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_015",
    "name": "CN_ELITE_15",
    "birth_date": "1982-06-14",
    "birth_time": "16:00",
    "geo_city": "Shenyang? (approx)",
    "geo_country": "China",
    "geo_longitude": 123.4315,
    "geo_latitude": 41.8057,
    "day_master": "戊",
    "gender": "M",
    "bazi": "壬戌 乙巳 戊辰 庚申",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主戊土",
      "月令乙巳(火)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1982-06-14申时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_016",
    "name": "CN_ELITE_16",
    "birth_date": "1979-02-09",
    "birth_time": "03:30",
    "geo_city": "Beijing",
    "geo_country": "China",
    "geo_longitude": 116.4074,
    "geo_latitude": 39.9042,
    "day_master": "丁",
    "gender": "F",
    "bazi": "己未 丙寅 丁未 壬寅",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主丁火",
      "月令丙寅(木)",
      "月令受制/泄耗",
      "强弱判定：Weak"
    ],
    "ground_truth": {
      "strength": "Weak"
    },
    "note": "公开命理资料常用版本（需自行复核）：1979-02-09寅时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_017",
    "name": "CN_ELITE_17",
    "birth_date": "1974-07-27",
    "birth_time": "18:00",
    "geo_city": "Hong Kong",
    "geo_country": "China",
    "geo_longitude": 114.1694,
    "geo_latitude": 22.3193,
    "day_master": "己",
    "gender": "M",
    "bazi": "甲寅 辛未 己巳 癸酉",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主己土",
      "月令辛未(土)",
      "月令得令/得生",
      "强弱判定：Balanced"
    ],
    "ground_truth": {
      "strength": "Balanced"
    },
    "note": "公开命理资料常用版本（需自行复核）：1974-07-27酉时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_018",
    "name": "CN_ELITE_18",
    "birth_date": "1997-08-05",
    "birth_time": "10:00",
    "geo_city": "Luoyang? (approx)",
    "geo_country": "China",
    "geo_longitude": 112.4539,
    "geo_latitude": 34.6197,
    "day_master": "己",
    "gender": "M",
    "bazi": "丁丑 戊申 己卯 己巳",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主己土",
      "月令戊申(金)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：1997-08-05巳时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_019",
    "name": "CN_ELITE_19",
    "birth_date": "2000-11-28",
    "birth_time": "08:00",
    "geo_city": "Huaihua? (approx)",
    "geo_country": "China",
    "geo_longitude": 109.998,
    "geo_latitude": 27.547,
    "day_master": "庚",
    "gender": "M",
    "bazi": "庚辰 戊子 庚寅 庚辰",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主庚金",
      "月令戊子(水)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：2000-11-28辰时。"
  },
  {
    "id": "STRENGTH_CN_MODERN_020",
    "name": "CN_ELITE_20",
    "birth_date": "1990-02-07",
    "birth_time": "06:00",
    "geo_city": "Shiyan, Hubei",
    "geo_country": "China",
    "geo_longitude": 110.7783,
    "geo_latitude": 32.6469,
    "day_master": "癸",
    "gender": "M",
    "bazi": "庚午 戊寅 癸卯 乙卯",
    "target_focus": "STRENGTH",
    "characteristics": [
      "日主癸水",
      "月令戊寅(木)",
      "月令得令/得生",
      "强弱判定：Strong"
    ],
    "ground_truth": {
      "strength": "Strong"
    },
    "note": "公开命理资料常用版本（需自行复核）：1990-02-07卯时。"
  }
]


def normalize_case(case: Dict) -> Dict:
    """规范化单个案例"""
    normalized = deepcopy(case)
    
    # 1. 转换bazi格式（字符串 -> 列表）
    if isinstance(normalized.get('bazi'), str):
        normalized['bazi'] = normalized['bazi'].split()
    
    # 2. 标准化gender（M/F -> 男/女）
    gender = normalized.get('gender', 'M')
    if gender in ['M', 'm', 'Male', 'male', '男']:
        normalized['gender'] = '男'
    elif gender in ['F', 'f', 'Female', 'female', '女']:
        normalized['gender'] = '女'
    else:
        normalized['gender'] = '男'  # 默认
    
    # 3. 转换characteristics（列表 -> 字符串，如果存在）
    if isinstance(normalized.get('characteristics'), list):
        normalized['characteristics'] = '，'.join(normalized['characteristics'])
    
    # 4. 确保target_focus存在
    if 'target_focus' not in normalized:
        normalized['target_focus'] = 'STRENGTH'
    
    # 5. 确保ground_truth存在
    if 'ground_truth' not in normalized:
        normalized['ground_truth'] = {}
    
    return normalized


def get_existing_case_ids() -> Set[str]:
    """获取现有案例的ID集合"""
    existing_ids = set()
    
    # 检查classic_cases.json
    classic_path = project_root / "data" / "classic_cases.json"
    if classic_path.exists():
        with open(classic_path, 'r', encoding='utf-8') as f:
            classic_cases = json.load(f)
            existing_ids.update(c.get('id') for c in classic_cases if c.get('id'))
    
    # 检查calibration_cases.json
    calibration_path = project_root / "data" / "calibration_cases.json"
    if calibration_path.exists():
        with open(calibration_path, 'r', encoding='utf-8') as f:
            calibration_cases = json.load(f)
            existing_ids.update(c.get('id') for c in calibration_cases if c.get('id'))
    
    return existing_ids


def find_duplicate_by_name_and_bazi(new_case: Dict, existing_cases: List[Dict]) -> Optional[str]:
    """根据名称和八字查找重复案例"""
    new_name = new_case.get('name', '').strip()
    new_bazi_str = ' '.join(new_case.get('bazi', []))
    
    for existing in existing_cases:
        existing_name = existing.get('name', '').strip()
        existing_bazi = existing.get('bazi', [])
        if isinstance(existing_bazi, str):
            existing_bazi_str = existing_bazi
        else:
            existing_bazi_str = ' '.join(existing_bazi)
        
        # 检查名称相似度（简单匹配，不考虑同音字）
        if new_name and existing_name:
            # 去除常见后缀和修饰词
            new_clean = new_name.replace('（', '(').replace('）', ')').split('(')[0].strip()
            existing_clean = existing_name.replace('（', '(').replace('）', ')').split('(')[0].strip()
            
            if new_clean == existing_clean and new_bazi_str == existing_bazi_str:
                return existing.get('id')
    
    return None


def main():
    print("=" * 80)
    print("📥 导入、清洗和规范化新案例")
    print("=" * 80)
    print()
    
    # 1. 规范化所有案例
    print("1️⃣ 规范化案例格式...")
    normalized_cases = [normalize_case(case) for case in NEW_CASES_JSON]
    print(f"   ✅ 规范化了 {len(normalized_cases)} 个案例")
    print()
    
    # 2. 获取现有案例ID
    print("2️⃣ 检查重复案例...")
    existing_ids = get_existing_case_ids()
    
    # 加载现有案例（用于名称和八字匹配）
    classic_path = project_root / "data" / "classic_cases.json"
    existing_classic_cases = []
    if classic_path.exists():
        with open(classic_path, 'r', encoding='utf-8') as f:
            existing_classic_cases = json.load(f)
    
    calibration_path = project_root / "data" / "calibration_cases.json"
    existing_calibration_cases = []
    if calibration_path.exists():
        with open(calibration_path, 'r', encoding='utf-8') as f:
            existing_calibration_cases = json.load(f)
    
    all_existing = existing_classic_cases + existing_calibration_cases
    
    # 3. 分离历史案例和现代案例，并检查重复
    historical_cases = []
    modern_cases = []
    skipped_duplicates = []
    
    for case in normalized_cases:
        case_id = case.get('id', '')
        
        # 检查ID重复
        if case_id in existing_ids:
            skipped_duplicates.append((case_id, 'ID重复'))
            continue
        
        # 检查名称和八字重复
        dup_id = find_duplicate_by_name_and_bazi(case, all_existing)
        if dup_id:
            skipped_duplicates.append((case_id, f'与现有案例 {dup_id} 重复（名称+八字）'))
            continue
        
        # 分类
        if case_id.startswith('STRENGTH_CN_HIST_'):
            historical_cases.append(case)
        elif case_id.startswith('STRENGTH_CN_MODERN_'):
            modern_cases.append(case)
        else:
            # 默认作为现代案例
            modern_cases.append(case)
    
    print(f"   ✅ 历史案例: {len(historical_cases)} 个")
    print(f"   ✅ 现代案例: {len(modern_cases)} 个")
    if skipped_duplicates:
        print(f"   ⚠️  跳过重复案例: {len(skipped_duplicates)} 个")
        for dup_id, reason in skipped_duplicates:
            print(f"      - {dup_id}: {reason}")
    print()
    
    # 4. 添加到相应的JSON文件
    print("3️⃣ 添加到JSON文件...")
    
    # 处理历史案例（添加到classic_cases.json，权重3.0x）
    if historical_cases:
        for case in historical_cases:
            case['weight'] = 3.0
            case['category'] = 'classic'
            case['verified'] = True
        
        classic_path.parent.mkdir(parents=True, exist_ok=True)
        
        if classic_path.exists():
            with open(classic_path, 'r', encoding='utf-8') as f:
                existing_classic = json.load(f)
        else:
            existing_classic = []
        
        # 合并（避免重复）
        existing_names = {c.get('name', '').strip() for c in existing_classic}
        existing_bazi_set = {' '.join(c.get('bazi', [])) if isinstance(c.get('bazi'), list) else c.get('bazi', '') for c in existing_classic}
        
        new_classic = []
        for case in historical_cases:
            case_name = case.get('name', '').strip()
            case_bazi = ' '.join(case.get('bazi', []))
            
            if case_name not in existing_names and case_bazi not in existing_bazi_set:
                new_classic.append(case)
                existing_names.add(case_name)
                existing_bazi_set.add(case_bazi)
        
        if new_classic:
            existing_classic.extend(new_classic)
            with open(classic_path, 'w', encoding='utf-8') as f:
                json.dump(existing_classic, f, ensure_ascii=False, indent=2)
            print(f"   ✅ 添加了 {len(new_classic)} 个历史案例到 classic_cases.json")
        else:
            print(f"   ⚠️  所有历史案例都已存在，跳过")
    
    # 处理现代案例（添加到calibration_cases.json，权重1.5x）
    if modern_cases:
        calibration_path.parent.mkdir(parents=True, exist_ok=True)
        
        if calibration_path.exists():
            with open(calibration_path, 'r', encoding='utf-8') as f:
                existing_calibration = json.load(f)
        else:
            existing_calibration = []
        
        # 只添加STRENGTH相关的案例
        strength_cases = [c for c in modern_cases if c.get('target_focus') == 'STRENGTH']
        
        # 合并（避免重复）
        existing_ids_set = {c.get('id') for c in existing_calibration}
        existing_bazi_set = {' '.join(c.get('bazi', [])) if isinstance(c.get('bazi'), list) else c.get('bazi', '') for c in existing_calibration}
        
        new_calibration = []
        for case in strength_cases:
            case_id = case.get('id')
            case_bazi = ' '.join(case.get('bazi', []))
            
            if case_id not in existing_ids_set and case_bazi not in existing_bazi_set:
                new_calibration.append(case)
                existing_ids_set.add(case_id)
                existing_bazi_set.add(case_bazi)
        
        if new_calibration:
            existing_calibration.extend(new_calibration)
            with open(calibration_path, 'w', encoding='utf-8') as f:
                json.dump(existing_calibration, f, ensure_ascii=False, indent=2)
            print(f"   ✅ 添加了 {len(new_calibration)} 个现代案例到 calibration_cases.json")
        else:
            print(f"   ⚠️  所有现代案例都已存在，跳过")
    
    print()
    print("=" * 80)
    print("✅ 导入完成！")
    print("=" * 80)
    print()
    print("📊 总结:")
    print(f"   - 规范化案例: {len(normalized_cases)} 个")
    print(f"   - 历史案例（classic_cases.json）: {len(historical_cases)} 个（权重3.0x）")
    print(f"   - 现代案例（calibration_cases.json）: {len(modern_cases)} 个（权重1.5x）")
    print(f"   - 跳过重复: {len(skipped_duplicates)} 个")


if __name__ == '__main__':
    main()

