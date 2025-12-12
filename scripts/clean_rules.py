#!/usr/bin/env python3
"""
规则清洗脚本 - 将英文和拼音翻译成中文
"""

from learning.db import LearningDB
import json

# 拼音到中文映射
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

# 英文术语映射
TERM_MAP = {
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
    
    # 十神
    'day master': '日主',
    'daymaster': '日主',
    
    # 状态
    'strong': '强',
    'weak': '弱',
    'good': '好',
    'excellent': '优秀',
    'powerful': '强大',
    
    # 格局和模式
    'san he bureau': '三合局',
    'sun he bureau': '三合局',  # 可能是拼写错误
    'pattern': '格局',
    'seasonal': '季节',
    'society': '社会',
    'untitled': '未命名',
    
    # 其他
    'life condition': '生活状况',
    'astrological sign': '星座',
    'element': '五行',
    'and': '和',
    'or': '或',
}

def clean_text(text):
    """清洗文本中的英文和拼音"""
    if not text or not isinstance(text, str):
        return text
    
    import re
    cleaned = text
    
    # Step 1: 替换多词组合（必须先于单词替换）
    multi_word_terms = {
        'san he bureau': '三合局',
        'sun he bureau': '三合局',
        'life condition': '生活状况',
        'astrological sign': '星座',
        'day master': '日主',
    }
    
    for eng, cn in multi_word_terms.items():
        # 使用正则表达式进行大小写不敏感替换
        pattern = re.compile(re.escape(eng), re.IGNORECASE)
        cleaned = pattern.sub(cn, cleaned)
    
    # Step 2: 替换拼音
    for pinyin, cn in PINYIN_MAP.items():
        # 使用单词边界确保完整匹配
        pattern = re.compile(r'\b' + re.escape(pinyin) + r'\b', re.IGNORECASE)
        cleaned = pattern.sub(cn, cleaned)
    
    # Step 3: 替换单个英文术语
    single_word_terms = {
        'branches': '地支',
        'branch': '地支',
        'stems': '天干',
        'stem': '天干',
        'contains': '包含',
        'contain': '包含',
        'wood': '木',
        'fire': '火',
        'earth': '土',
        'metal': '金',
        'water': '水',
        'strong': '强',
        'weak': '弱',
        'good': '好',
        'excellent': '优秀',
        'powerful': '强大',
        'pattern': '格局',
        'seasonal': '季节',
        'society': '社会',
        'untitled': '未命名',
        'element': '五行',
        'name': '名称',
        'bureau': '局',
        'and': '和',
        'or': '或',
    }
    
    for eng, cn in single_word_terms.items():
        pattern = re.compile(r'\b' + re.escape(eng) + r'\b', re.IGNORECASE)
        cleaned = pattern.sub(cn, cleaned)
    
    # Step 4: 清理多余空格
    cleaned = ' '.join(cleaned.split())
    
    return cleaned

def clean_rule(rule):
    """清洗单条规则"""
    cleaned_rule = {}
    
    for key, value in rule.items():
        if key == 'rule_name':
            cleaned_rule[key] = clean_text(value)
        elif key == 'description':
            cleaned_rule[key] = clean_text(value)
        elif key == 'trigger_conditions' and isinstance(value, list):
            cleaned_rule[key] = [clean_text(cond) for cond in value]
        else:
            cleaned_rule[key] = value
    
    return cleaned_rule

def main():
    db = LearningDB()
    
    # 获取所有规则
    all_rules = db.get_all_rules()
    print(f"📊 总共 {len(all_rules)} 条规则需要清洗")
    
    cleaned_count = 0
    
    for rule in all_rules:
        rule_id = rule.get('id')
        
        # 清洗规则
        cleaned = clean_rule(rule)
        
        # 检查是否有变化
        if cleaned != rule:
            # 更新数据库
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            c = conn.cursor()
            
            c.execute("""
                UPDATE rules 
                SET rule_name = ?, rule_json = ?
                WHERE id = ?
            """, (cleaned['rule_name'], json.dumps(cleaned, ensure_ascii=False), rule_id))
            
            conn.commit()
            conn.close()
            
            cleaned_count += 1
            
            if cleaned_count <= 5:
                print(f"\n✅ 清洗规则 #{rule_id}:")
                print(f"   原名称: {rule.get('rule_name')}")
                print(f"   新名称: {cleaned['rule_name']}")
    
    print(f"\n🎉 完成！共清洗了 {cleaned_count} 条规则")

if __name__ == "__main__":
    main()
