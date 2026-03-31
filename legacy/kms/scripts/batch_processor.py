"""
批量处理脚本 (Batch Processor)
读取原始文本，批量进行语义蒸馏和索引

流水线: Read → Split → Distill → Index → Aggregate
"""

import json
import sys
import os
import re
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️  警告: ollama未安装，将跳过LLM调用")
    print("   安装命令: pip install ollama")

# 尝试使用修复版，如果不存在则使用V2
try:
    from kms.core.semantic_distiller_v2_fixed import SemanticDistillerV2Fixed as SemanticDistillerV2
except ImportError:
    from kms.core.semantic_distiller_v2 import SemanticDistillerV2


# 配置
MODEL_NAME = "qwen2.5:3b"
RAW_TEXTS_DIR = os.path.join(os.path.dirname(__file__), '../data/raw_texts')
OUTPUT_CODEX_PATH = os.path.join(os.path.dirname(__file__), '../data/classical_codex.jsonl')
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), '../data/vector_db')


def read_raw_text(file_path: str) -> str:
    """读取原始文本文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return ""


def split_text_into_segments(text: str, max_length: int = 50) -> List[str]:
    """
    将文本切分为段落
    
    Args:
        text: 原始文本
        max_length: 最大段落长度（字符数），默认50以确保每个句子单独处理
        
    Returns:
        段落列表
    """
    # 按句号、问号、感叹号、换行符切分
    sentences = re.split(r'[。！？\n]', text)
    
    segments = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 3:  # 跳过空句子或过短片段
            continue
        
        # 如果句子本身超过最大长度，强制切分
        if len(sentence) > max_length:
            # 按逗号进一步切分
            sub_sentences = re.split(r'[，,]', sentence)
            for sub in sub_sentences:
                sub = sub.strip()
                if sub and len(sub) >= 3:
                    segments.append(sub)
        else:
            # 单独成段，确保每个句子独立处理
            segments.append(sentence)
    
    return segments if segments else [text.strip()]  # 如果切分失败，返回原文本


def call_llm_distill(text: str, source_book: str, topic: str) -> Optional[Dict[str, Any]]:
    """调用LLM进行语义蒸馏"""
    if not OLLAMA_AVAILABLE:
        return None
    
    distiller = SemanticDistillerV2()
    system_prompt = distiller.get_system_prompt(source_book, topic)
    
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"分析以下文本并输出JSON:\n\n{text}"}
            ],
            format='json',
            options={
                'temperature': 0.1,      # 保持低创造性，保证逻辑稳定
                'num_predict': 1024,      # 增加输出上限至1024 tokens，避免JSON截断
                'num_ctx': 2048           # 确保上下文窗口足够大
            }
        )
        
        llm_response = response['message']['content']
        output = distiller.parse_llm_response(llm_response)
        
        # 确保original_text字段存在
        if "original_text" not in output:
            output["original_text"] = text
        
        # 验证输出
        is_valid, error = distiller.validate_output(output)
        if not is_valid:
            print(f"   ⚠️  验证失败: {error}")
            print(f"   响应内容预览: {llm_response[:300]}...")
            return None
        
        # 补全字段
        codex_entry = {
            "canon_id": f"AUTO-{abs(hash(text)) % 10000:04d}",
            "source_book": source_book,
            "chapter": topic,
            "tags": ["批量生成", topic],
            "relevance_score": 0.9,
            **output
        }
        
        # 确保original_text使用原始文本
        codex_entry["original_text"] = text
        
        return codex_entry
        
    except Exception as e:
        print(f"   ❌ LLM调用失败: {e}")
        return None


def save_codex_entry(entry: Dict[str, Any], file_path: str):
    """保存codex条目到JSONL文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def process_batch(input_file: str, 
                  source_book: str = "子平真诠",
                  topic: str = "食神格",
                  enable_indexing: bool = False):
    """
    批量处理文本文件
    
    Args:
        input_file: 输入文本文件路径
        source_book: 典籍名称
        topic: 主题/格局名称
        enable_indexing: 是否启用向量索引
    """
    print("=" * 60)
    print("FDS-KMS 批量处理流水线")
    print("=" * 60)
    print()
    
    # Step 1: Read
    print("📖 步骤1: 读取原始文本...")
    text = read_raw_text(input_file)
    if not text:
        return
    
    print(f"   ✅ 已读取 {len(text)} 字符")
    print()
    
    # Step 2: Split
    print("✂️  步骤2: 切分文本段落...")
    segments = split_text_into_segments(text, max_length=200)
    print(f"   ✅ 切分为 {len(segments)} 个段落")
    print()
    
    # Step 3: Distill & Index
    print("🧠 步骤3: 批量语义蒸馏...")
    print()
    
    # 尝试导入tqdm用于进度条
    try:
        from tqdm import tqdm
        USE_TQDM = True
    except ImportError:
        USE_TQDM = False
        print("💡 提示: 安装tqdm可显示进度条: pip install tqdm")
        print()
    
    success_count = 0
    failed_count = 0
    
    # 初始化向量索引器（如果需要）
    collection = None
    if enable_indexing:
        try:
            from kms.scripts.vector_indexer_setup import init_vector_db, index_entry
            collection, _, emb_fn = init_vector_db()
            print("   ✅ 向量索引器已初始化")
        except Exception as e:
            print(f"   ⚠️  向量索引器初始化失败: {e}")
            enable_indexing = False
            emb_fn = None
    
    # 使用tqdm进度条（如果可用）
    iterator = tqdm(enumerate(segments, 1), total=len(segments), desc="处理中") if USE_TQDM else enumerate(segments, 1)
    
    for i, segment in iterator:
        if not USE_TQDM:
            print(f"   [{i}/{len(segments)}] 处理段落: {segment[:30]}...")
        
        # Distill
        entry = call_llm_distill(segment, source_book, topic)
        
        if entry:
            # 保存到JSONL
            save_codex_entry(entry, OUTPUT_CODEX_PATH)
            success_count += 1
            
            # Index (如果需要)
            if enable_indexing and collection:
                try:
                    index_entry(collection, entry, emb_fn)
                except Exception as e:
                    if not USE_TQDM:
                        print(f"      ⚠️  索引失败: {e}")
            
            if not USE_TQDM:
                print(f"      ✅ 成功")
            elif USE_TQDM:
                iterator.set_postfix({"成功": success_count, "失败": failed_count})
        else:
            failed_count += 1
            if not USE_TQDM:
                print(f"      ❌ 失败")
            elif USE_TQDM:
                iterator.set_postfix({"成功": success_count, "失败": failed_count})
    
    print()
    print("=" * 60)
    print("📊 处理结果统计")
    print("=" * 60)
    print(f"   总段落数: {len(segments)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {failed_count}")
    print(f"   成功率: {success_count/len(segments)*100:.1f}%")
    print()
    print(f"   Codex文件: {OUTPUT_CODEX_PATH}")
    if enable_indexing:
        print(f"   向量数据库: {VECTOR_DB_PATH}")
    print()
    print("✅ 批量处理完成！")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FDS-KMS 批量处理脚本")
    parser.add_argument("input_file", help="输入文本文件路径")
    parser.add_argument("--book", default="子平真诠", help="典籍名称")
    parser.add_argument("--topic", default="食神格", help="主题/格局名称")
    parser.add_argument("--index", action="store_true", help="启用向量索引")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ 文件不存在: {args.input_file}")
        print()
        print("💡 使用示例:")
        print(f"   python {sys.argv[0]} raw_texts/子平真诠_论食神.txt --book 子平真诠 --topic 食神格 --index")
        return
    
    process_batch(
        input_file=args.input_file,
        source_book=args.book,
        topic=args.topic,
        enable_indexing=args.index
    )


if __name__ == "__main__":
    # 如果没有命令行参数，显示使用说明
    if len(sys.argv) == 1:
        print("=" * 60)
        print("FDS-KMS 批量处理脚本")
        print("=" * 60)
        print()
        print("使用方法:")
        print(f"   python {sys.argv[0]} <输入文件> [选项]")
        print()
        print("选项:")
        print("   --book <名称>    典籍名称 (默认: 子平真诠)")
        print("   --topic <名称>   主题/格局名称 (默认: 食神格)")
        print("   --index          启用向量索引")
        print()
        print("示例:")
        print(f"   python {sys.argv[0]} raw_texts/子平真诠_论食神.txt --book 子平真诠 --topic 食神格 --index")
        print()
        print("💡 提示:")
        print("   1. 准备原始文本文件（UTF-8编码）")
        print("   2. 文本将被自动切分为段落")
        print("   3. 每个段落将被LLM处理生成codex条目")
        print("   4. 结果保存到 classical_codex.jsonl")
    else:
        main()

