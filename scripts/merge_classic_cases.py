#!/usr/bin/env python3
"""
合并和清洗经典案例脚本
====================

功能：
1. 合并新案例到classic_cases.json
2. 数据清洗（检查重复、格式、补全字段）
3. 验证数据完整性

使用方法：
    python3 scripts/merge_classic_cases.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 新案例数据
NEW_CLASSIC_CASES = [
    {
        "id": "CLASSIC_001",
        "name": "乾隆皇帝 (Emperor Qianlong)",
        "birth_date": "1711-09-25",
        "birth_time": "00:00",
        "geo_city": "Beijing",
        "geo_country": "China",
        "geo_longitude": 116.407,
        "geo_latitude": 39.904,
        "day_master": "庚",
        "gender": "男",
        "bazi": ["辛卯", "丁酉", "庚午", "丙子"],
        "target_focus": "STRENGTH",
        "characteristics": "【阳刃格/身强抗杀】子午冲、卯酉冲（四冲）。庚金生于酉月（帝旺/阳刃），天干透辛金帮身。虽然地支全冲，但月令提纲（酉）力量最大。此造用于校准'月令权重'必须高于'地支冲克折损'。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，阳刃驾杀，帝王之命"
        }
    },
    {
        "id": "CLASSIC_002",
        "name": "袁世凯 (Yuan Shikai)",
        "birth_date": "1859-09-16",
        "birth_time": "14:00",
        "geo_city": "Xiangcheng",
        "geo_country": "China",
        "geo_longitude": 114.65,
        "geo_latitude": 33.85,
        "day_master": "丁",
        "gender": "男",
        "bazi": ["己未", "癸酉", "丁巳", "丁未"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强/食神制杀】丁火生于酉月（偏财），看似弱。但自坐巳火（帝旺/强根），时支未土有余气，时干丁火帮身。此造用于校准'日主自坐强根'与'时柱帮身'的权重（Structure Layer）。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，食神制杀，权倾天下"
        }
    },
    {
        "id": "CLASSIC_003",
        "name": "慈禧太后 (Empress Cixi)",
        "birth_date": "1835-11-29",
        "birth_time": "08:00",
        "geo_city": "Beijing",
        "geo_country": "China",
        "geo_longitude": 116.40,
        "geo_latitude": 39.90,
        "day_master": "乙",
        "gender": "女",
        "bazi": ["乙未", "丁亥", "乙丑", "庚辰"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强/印绶格】乙木生于亥月（正印/长生），印星当令。虽坐丑土衰地，但得月令强生。此造用于验证'月令印星'对日主的决定性支撑作用（Physics Layer）。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，印旺身旺，贪权"
        }
    },
    {
        "id": "CLASSIC_004",
        "name": "孙中山 (Sun Yat-sen)",
        "birth_date": "1866-11-12",
        "birth_time": "04:00",
        "geo_city": "Zhongshan",
        "geo_country": "China",
        "geo_longitude": 113.39,
        "geo_latitude": 22.52,
        "day_master": "丁",
        "gender": "男",
        "bazi": ["丙寅", "己亥", "丁酉", "壬寅"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强/杀印相生】丁火生于亥月（正官），地支寅亥合木（印局），年时双寅（长生）。印星极旺化官杀。此造用于测试'地支六合化印'的能量转化逻辑（Flow Layer）。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，印旺化杀，革命领袖"
        }
    },
    {
        "id": "CLASSIC_005",
        "name": "溥仪 (Emperor Puyi)",
        "birth_date": "1906-02-07",
        "birth_time": "12:00",
        "geo_city": "Beijing",
        "geo_country": "China",
        "geo_longitude": 116.40,
        "geo_latitude": 39.90,
        "day_master": "壬",
        "gender": "男",
        "bazi": ["丙午", "庚寅", "壬午", "丙午"],
        "target_focus": "STRENGTH",
        "characteristics": "【从财格/极弱】壬水生于寅月（泄气），地支寅午半合火局，三午火旺，天干透丙火。满盘皆火（财）。庚金无根被火克，无法生水。此造用于校准'真从格'的阈值（Follower Threshold）。",
        "ground_truth": {
            "strength": "Follower",
            "note": "真从财格，弃命从财，富贵但无权"
        }
    },
    {
        "id": "CLASSIC_006",
        "name": "李鸿章 (Li Hongzhang)",
        "birth_date": "1823-02-15",
        "birth_time": "06:00",
        "geo_city": "Hefei",
        "geo_country": "China",
        "geo_longitude": 117.28,
        "geo_latitude": 31.86,
        "day_master": "乙",
        "gender": "男",
        "bazi": ["癸未", "甲寅", "乙亥", "己卯"],
        "target_focus": "STRENGTH",
        "characteristics": "【曲直仁寿格/专旺】乙木生于寅月（帝旺），地支亥卯未三合木局。满盘皆木，无金克制。此造用于测试'专旺格'（Special Strong）的判定逻辑。",
        "ground_truth": {
            "strength": "Special_Strong",
            "note": "曲直仁寿格，专旺，权臣"
        }
    },
    {
        "id": "CLASSIC_007",
        "name": "蒋介石 (Chiang Kai-shek)",
        "birth_date": "1887-10-31",
        "birth_time": "12:00",
        "geo_city": "Ningbo",
        "geo_country": "China",
        "geo_longitude": 121.55,
        "geo_latitude": 29.87,
        "day_master": "己",
        "gender": "男",
        "bazi": ["丁亥", "庚戌", "己巳", "庚午"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强】己土生于戌月（劫财/库），坐巳火（印/强根），时支午火（禄）。火土极旺。用于校准'得令得地'的标准身强模型。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，火土燥热，喜金水"
        }
    },
    {
        "id": "CLASSIC_008",
        "name": "曾国藩 (Zeng Guofan)",
        "birth_date": "1811-11-26",
        "birth_time": "22:00",
        "geo_city": "Loudi",
        "geo_country": "China",
        "geo_longitude": 111.99,
        "geo_latitude": 27.73,
        "day_master": "丙",
        "gender": "男",
        "bazi": ["辛未", "己亥", "丙辰", "己亥"],
        "target_focus": "STRENGTH",
        "characteristics": "【身弱/杀重】丙火生于亥月（七杀/绝地），地支双亥水克身，辰土泄气。仅靠未中一点丁火微根。此造用于校准'身弱'与'从格'的边界（因有微根，不能从，为身弱）。",
        "ground_truth": {
            "strength": "Weak",
            "note": "身弱杀重，需印化杀"
        }
    },
    {
        "id": "CLASSIC_009",
        "name": "王十万 (Wang Shiwan - 教科书案例)",
        "birth_date": "1800-01-01",
        "birth_time": "00:00",
        "geo_city": "Unknown",
        "geo_country": "China",
        "geo_longitude": 116.0,
        "geo_latitude": 39.0,
        "day_master": "丙",
        "gender": "男",
        "bazi": ["庚申", "乙酉", "丙申", "己丑"],
        "target_focus": "STRENGTH",
        "characteristics": "【真从财格】《滴天髓》经典案例。丙火生于酉月，地支全金（申酉丑合金局），天干透庚。乙木被庚合化。丙火无根，弃命从财。用于强制校准'乔丹'类型的从格。",
        "ground_truth": {
            "strength": "Follower",
            "note": "教科书级真从财格，富甲一方"
        }
    },
    {
        "id": "CLASSIC_010",
        "name": "朱元璋 (Hongwu Emperor)",
        "birth_date": "1328-10-21",
        "birth_time": "20:00",
        "geo_city": "Fengyang",
        "geo_country": "China",
        "geo_longitude": 117.56,
        "geo_latitude": 32.86,
        "day_master": "丁",
        "gender": "男",
        "bazi": ["戊辰", "壬戌", "丁丑", "丁未"],
        "target_focus": "STRENGTH",
        "characteristics": "【从儿格/极弱】丁火生于戌月（伤官），地支辰戌丑未四库全冲（土局），食伤极旺。天干透戊土。丁火微弱，顺土之势。用于校准'食伤旺导致的从格'。",
        "ground_truth": {
            "strength": "Follower",
            "note": "从儿格（从食伤），地支四库全"
        }
    },
    {
        "id": "CLASSIC_011",
        "name": "康熙皇帝 (Emperor Kangxi)",
        "birth_date": "1654-05-04",
        "birth_time": "10:00",
        "geo_city": "Beijing",
        "geo_country": "China",
        "geo_longitude": 116.40,
        "geo_latitude": 39.90,
        "day_master": "戊",
        "gender": "男",
        "bazi": ["甲午", "戊辰", "戊申", "丁巳"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强】戊土生于辰月（比肩），年时见午巳火（印），天干透丁戊。身极强。用于测试土重埋金/火土燥热的强旺判定。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强印旺，帝王之命"
        }
    },
    {
        "id": "CLASSIC_012",
        "name": "岳飞 (Yue Fei)",
        "birth_date": "1103-03-24",
        "birth_time": "10:00",
        "geo_city": "Anyang",
        "geo_country": "China",
        "geo_longitude": 114.35,
        "geo_latitude": 36.10,
        "day_master": "甲",
        "gender": "男",
        "bazi": ["癸未", "乙卯", "甲子", "己巳"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强/阳刃】甲木生于卯月（帝旺/阳刃），坐子水（印），天干透乙癸。身强无疑。用于测试阳刃格的能量计算。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，阳刃格，武贵"
        }
    },
    {
        "id": "CLASSIC_013",
        "name": "杜月笙 (Du Yuesheng)",
        "birth_date": "1888-08-22",
        "birth_time": "12:00",
        "geo_city": "Shanghai",
        "geo_country": "China",
        "geo_longitude": 121.47,
        "geo_latitude": 31.23,
        "day_master": "乙",
        "gender": "男",
        "bazi": ["戊子", "庚申", "乙丑", "壬午"],
        "target_focus": "STRENGTH",
        "characteristics": "【身弱】乙木生于申月（正官/死地），天干透庚金合克。虽有年支子水（印）和时干壬水（印）帮身，但官杀当令且旺。身弱用印。用于校准'官杀格身弱'。",
        "ground_truth": {
            "strength": "Weak",
            "note": "身弱，官杀旺，用印化杀"
        }
    },
    {
        "id": "CLASSIC_014",
        "name": "梅兰芳 (Mei Lanfang)",
        "birth_date": "1894-10-22",
        "birth_time": "08:00",
        "geo_city": "Beijing",
        "geo_country": "China",
        "geo_longitude": 116.40,
        "geo_latitude": 39.90,
        "day_master": "丁",
        "gender": "男",
        "bazi": ["甲午", "甲戌", "丁酉", "乙巳"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强/印比】丁火生于戌月（伤官），但地支午戌合火，时支巳火，天干透双甲乙木（印）。满盘木火。身强。测试食伤月但局合成势的变格。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，木火通明，食伤吐秀"
        }
    },
    {
        "id": "CLASSIC_015",
        "name": "张大千 (Zhang Daqian)",
        "birth_date": "1899-05-10",
        "birth_time": "16:00",
        "geo_city": "Neijiang",
        "geo_country": "China",
        "geo_longitude": 105.05,
        "geo_latitude": 29.58,
        "day_master": "戊",
        "gender": "男",
        "bazi": ["己亥", "己巳", "戊寅", "庚申"],
        "target_focus": "STRENGTH",
        "characteristics": "【身强】戊土生于巳月（禄），天干双己帮身。虽地支寅申巳亥四冲，但得令得助。用于测试'四冲'对旺衰的折损程度（得令者旺，冲不败）。",
        "ground_truth": {
            "strength": "Strong",
            "note": "身强，四冲不败，艺术大师"
        }
    }
]


def clean_and_validate_case(case: Dict) -> Dict:
    """
    清洗和验证单个案例
    
    Args:
        case: 案例字典
        
    Returns:
        清洗后的案例字典
    """
    # 确保必需字段存在
    required_fields = ['id', 'name', 'birth_date', 'day_master', 'bazi', 'target_focus', 'ground_truth']
    for field in required_fields:
        if field not in case:
            raise ValueError(f"案例 {case.get('id', 'Unknown')} 缺少必需字段: {field}")
    
    # 确保bazi是4个元素
    bazi = case.get('bazi', [])
    if len(bazi) != 4:
        raise ValueError(f"案例 {case.get('id')} 的八字必须是4个元素，当前: {len(bazi)}")
    
    # 确保ground_truth中有strength
    if 'strength' not in case.get('ground_truth', {}):
        raise ValueError(f"案例 {case.get('id')} 的ground_truth中缺少strength字段")
    
    # 设置默认权重和类别
    if 'weight' not in case:
        case['weight'] = 3.0
    if 'category' not in case:
        case['category'] = 'classic'
    if 'verified' not in case:
        case['verified'] = True
    
    # 修复康熙案例的八字错误（丁Si应该是丁巳）
    if case.get('id') == 'CLASSIC_011':
        bazi = case.get('bazi', [])
        if len(bazi) == 4 and bazi[3] == '丁Si':
            bazi[3] = '丁巳'
            case['bazi'] = bazi
    
    return case


def merge_classic_cases(existing_file: str, new_cases: List[Dict], output_file: str = None) -> List[Dict]:
    """
    合并经典案例（去重、清洗）
    
    Args:
        existing_file: 现有文件路径
        new_cases: 新案例列表
        output_file: 输出文件路径（如果为None，则覆盖原文件）
    
    Returns:
        合并后的案例列表
    """
    if output_file is None:
        output_file = existing_file
    
    # 1. 加载现有案例
    existing_cases = []
    if Path(existing_file).exists():
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing_cases = json.load(f)
        print(f"✅ 加载了 {len(existing_cases)} 个现有经典案例")
    else:
        print(f"⚠️  现有文件不存在，将创建新文件")
    
    # 2. 建立ID和名称索引（用于去重）
    existing_ids: Set[str] = {c.get('id') for c in existing_cases}
    existing_names: Set[str] = {c.get('name') for c in existing_cases if c.get('name')}
    
    # 3. 清洗新案例
    cleaned_new_cases = []
    for case in new_cases:
        try:
            cleaned_case = clean_and_validate_case(case)
            case_id = cleaned_case.get('id')
            case_name = cleaned_case.get('name')
            
            # 检查重复
            if case_id in existing_ids:
                print(f"⚠️  跳过重复案例（ID）: {case_id} - {case_name}")
                continue
            if case_name in existing_names:
                print(f"⚠️  跳过重复案例（名称）: {case_id} - {case_name}")
                continue
            
            cleaned_new_cases.append(cleaned_case)
            existing_ids.add(case_id)
            existing_names.add(case_name)
        except Exception as e:
            print(f"❌ 案例 {case.get('id', 'Unknown')} 清洗失败: {e}")
            continue
    
    # 4. 合并
    merged_cases = existing_cases + cleaned_new_cases
    
    # 5. 按ID排序
    merged_cases.sort(key=lambda x: x.get('id', ''))
    
    # 6. 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 合并完成:")
    print(f"   现有案例: {len(existing_cases)}")
    print(f"   新增案例: {len(cleaned_new_cases)}")
    print(f"   总计: {len(merged_cases)}")
    print(f"   已保存到: {output_file}")
    
    return merged_cases


if __name__ == '__main__':
    classic_file = project_root / "data" / "classic_cases.json"
    merged = merge_classic_cases(str(classic_file), NEW_CLASSIC_CASES)
    
    print(f"\n📋 合并后的经典案例列表:")
    print('=' * 80)
    for i, case in enumerate(merged, 1):
        print(f"{i:2d}. {case.get('id'):20s} | {case.get('name'):40s} | {case.get('ground_truth', {}).get('strength', 'Unknown')}")

