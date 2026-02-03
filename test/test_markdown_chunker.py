import os
import sys
from typing import List, Dict, Any

# 将项目根目录添加到 python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphrag_agent.pipelines.ingestion.markdown_chunker import MarkdownTextChunker
from graphrag_agent.pipelines.ingestion.document_processor import DocumentProcessor

def test_markdown_chunker_directly():
    print("\n" + "="*50)
    print("测试 MarkdownTextChunker 直接分块")
    print("="*50)
    
    test_file = "test_md_files/KKS-系统代码.md"
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 {test_file} 不存在")
        return

    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 设置较小的 chunk_size 以便触发细分逻辑
    chunker = MarkdownTextChunker(chunk_size=500, overlap=100)
    chunks = chunker.chunk_text(content)

    print(f"总分块数: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):  # 打印所有分块
        print(f"\n--- 分块 {i+1} ---")
        print(f"标题路径: {chunk['header_path']}")
        print(f"内容:\n{chunk['text']}")
        print(f"内容长度: {len(chunk['text'])}")
        
        # 验证是否包含标题前缀
        if chunk['header_path'] and chunk['header_path'] not in chunk['text']:
            print("警告: 分块内容中未发现标题路径前缀")
        
        # 验证回溯逻辑：寻找分块结尾是否为标点或换行
        last_char = chunk['text'].strip()[-1]
        if last_char in ['。', '\n', '！', '？', '；', '.', '!', '?', ';']:
            print(f"边界检查: 成功 (结尾字符: '{last_char}')")
        else:
            print(f"边界检查: 警告 (结尾字符: '{last_char}'，可能为强制截断)")

def test_document_processor_routing():
    print("\n" + "="*50)
    print("测试 DocumentProcessor 自动路由与统一格式")
    print("="*50)
    
    processor = DocumentProcessor(directory_path="test_md_files", chunk_size=500, overlap=100)
    results = processor.process_directory(file_extensions=['.md'])
    
    for result in results:
        print(f"\n文件: {result['filename']}")
        print(f"分块数量: {result['chunk_count']}")
        
        if result['chunks']:
            first_chunk = result['chunks'][0]
            print(f"分块格式检查: {'成功' if isinstance(first_chunk, dict) else '失败'}")
            if isinstance(first_chunk, dict):
                print(f"包含 metadata: {'成功' if 'metadata' in first_chunk else '失败'}")
                print(f"包含 text: {'成功' if 'text' in first_chunk else '失败'}")

if __name__ == "__main__":
    try:
        test_markdown_chunker_directly()
        test_document_processor_routing()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
