#!/usr/bin/env python3
"""
测试 TextCleaner 的拼音和英文翻译功能
"""

from learning.text_cleaner import TextCleaner

def test_pinyin_translation():
    """测试拼音翻译"""
    print("=" * 60)
    print("测试拼音翻译")
    print("=" * 60)
    
    test_cases = [
        ("这个八字有 jia 木和 si 火", "这个八字有 甲 木和 巳 火"),
        ("Yin 月出生，you 金很旺", "寅 月出生，酉 金很旺"),
        ("zi chou yin mao chen si", "子 丑 寅 卯 辰 巳"),
    ]
    
    for input_text, expected in test_cases:
        result = TextCleaner.clean(input_text)
        status = "✅" if expected in result else "❌"
        print(f"{status} 输入: {input_text}")
        print(f"   输出: {result}")
        print(f"   期望: {expected}")
        print()

def test_english_translation():
    """测试英文翻译"""
    print("=" * 60)
    print("测试英文翻译")
    print("=" * 60)
    
    test_cases = [
        ("The branches contain Si and You", "地支 包含 巳 和 酉"),
        ("Day Master is Wood element", "日主 是 木 五行"),
        ("San He Bureau pattern is strong", "三合局 格局 是 强"),
        ("Fire is very strong in this chart", "火 是 very 强 in this chart"),  # 部分翻译
    ]
    
    for input_text, expected_contains in test_cases:
        result = TextCleaner.clean(input_text)
        # 检查关键词是否被翻译
        key_words = expected_contains.split()
        matched = all(word in result for word in key_words if len(word) > 1)
        status = "✅" if matched else "⚠️"
        print(f"{status} 输入: {input_text}")
        print(f"   输出: {result}")
        print()

def test_mixed_content():
    """测试混合内容（中文+拼音+英文）"""
    print("=" * 60)
    print("测试混合内容")
    print("=" * 60)
    
    test_text = """
    这个八字是 jia wood day master，月令是 you metal，
    形成了 san he bureau pattern。The branches contain si, you, chou，
    所以 metal element is very strong。
    """
    
    print(f"原文:\n{test_text}\n")
    result = TextCleaner.clean(test_text)
    print(f"清洗后:\n{result}\n")
    
    # 检查关键翻译
    checks = [
        ("甲" in result, "jia -> 甲"),
        ("木" in result, "wood -> 木"),
        ("日主" in result, "day master -> 日主"),
        ("酉" in result, "you -> 酉"),
        ("金" in result, "metal -> 金"),
        ("三合局" in result, "san he bureau -> 三合局"),
        ("地支" in result, "branches -> 地支"),
        ("巳" in result, "si -> 巳"),
        ("丑" in result, "chou -> 丑"),
    ]
    
    print("翻译检查:")
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {desc}")

if __name__ == "__main__":
    test_pinyin_translation()
    test_english_translation()
    test_mixed_content()
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
