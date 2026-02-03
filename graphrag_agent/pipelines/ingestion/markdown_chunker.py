import re
import os
from typing import List, Dict, Any, Optional
from langchain_text_splitters import MarkdownHeaderTextSplitter
from graphrag_agent.config.settings import CHUNK_SIZE, OVERLAP

class MarkdownTextChunker:
    """
    Markdown 文本分块器，专门处理 MD 格式文档。
    支持按标题切分、层级上下文保留、连续标题合并以及基于 Token (字符) 的智能边界回溯细分。
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP):
        """
        初始化 Markdown 分块器
        
        Args:
            chunk_size: 每个文本块的最大字符数 (作为 Token 数的近似)
            overlap: 回溯搜索的最大范围
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # 定义需要切分的标题层级
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        对 Markdown 文本进行分块
        
        Args:
            text: 原始 Markdown 文本内容
            
        Returns:
            List[Dict]: 分块结果列表，每个字典包含：
                - text: 分块内容（含标题前缀）
                - metadata: 原始标题层级元数据
                - header_path: 格式化后的标题路径
        """
        if not text:
            return []

        # 阶段一：按标题进行初步切分
        initial_splits = self.header_splitter.split_text(text)
        
        processed_chunks = []
        
        for split in initial_splits:
            content = split.page_content.strip()
            metadata = split.metadata
            
            # 标题合并 (Header Consolidation): 如果内容为空，说明是连续标题
            # MarkdownHeaderTextSplitter 会将后续内容归入下一个标题块
            # 我们只需要处理非空内容的块
            if not content:
                continue
            
            # 构建标题前缀，增强语义上下文
            header_path = self._build_header_path(metadata)
            header_prefix = f"{header_path}\n\n" if header_path else ""
            
            # 检查是否需要进一步细分
            if len(content) <= self.chunk_size:
                processed_chunks.append({
                    "text": header_prefix + content,
                    "metadata": metadata,
                    "header_path": header_path
                })
            else:
                # 阶段二：基于长度的智能边界回溯细分
                sub_chunks = self._split_by_length_with_backtracking(content)
                for sub_content in sub_chunks:
                    processed_chunks.append({
                        "text": header_prefix + sub_content,
                        "metadata": metadata,
                        "header_path": header_path
                    })
                    
        return processed_chunks

    def _build_header_path(self, metadata: Dict[str, str]) -> str:
        """根据 metadata 构建标题路径前缀 (例如: # 标题1 > ## 标题2)"""
        path_parts = []
        # 按定义的顺序（H1->H4）检查元数据
        for symbol, level_name in self.headers_to_split_on:
            if level_name in metadata:
                path_parts.append(f"{symbol} {metadata[level_name]}")
        
        return " > ".join(path_parts) if path_parts else ""

    def _split_by_length_with_backtracking(self, text: str) -> List[str]:
        """
        按长度细分文本，并使用优先级回溯搜索最佳边界
        优先级：句号 (。) > 换行 (\n) > 其他标点
        """
        chunks = []
        start_pos = 0
        text_len = len(text)

        while start_pos < text_len:
            # 目标结束位置
            end_pos = start_pos + self.chunk_size
            
            if end_pos >= text_len:
                remaining_text = text[start_pos:].strip()
                if remaining_text:
                    chunks.append(remaining_text)
                break
            
            # 在 [end_pos - overlap, end_pos] 范围内寻找最佳切分点
            search_range_start = max(start_pos, end_pos - self.overlap)
            search_text = text[search_range_start:end_pos]
            
            # 优先级 1: 句号 (。)
            found_pos = self._find_last_occurrence(search_text, r'[。]')
            if found_pos != -1:
                actual_end = search_range_start + found_pos + 1
            else:
                # 优先级 2: 换行符 (\n)
                found_pos = self._find_last_occurrence(search_text, r'\n')
                if found_pos != -1:
                    actual_end = search_range_start + found_pos + 1
                else:
                    # 优先级 3: 其他常见标点 (！ ？ ； . ! ? ;)
                    found_pos = self._find_last_occurrence(search_text, r'[！？；.!?;]')
                    if found_pos != -1:
                        actual_end = search_range_start + found_pos + 1
                    else:
                        # 兜底：在 CHUNK_SIZE 处强制截断
                        actual_end = end_pos
            
            chunk_to_add = text[start_pos:actual_end].strip()
            if chunk_to_add:
                chunks.append(chunk_to_add)
            
            # 更新起始位置为实际切分点
            start_pos = actual_end
            
        return chunks

    def _find_last_occurrence(self, text: str, pattern: str) -> int:
        """在文本中寻找正则表达式模式最后一次出现的位置"""
        matches = list(re.finditer(pattern, text))
        if matches:
            return matches[-1].start()
        return -1
