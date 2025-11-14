import tiktoken
import re
from typing import List, Tuple, Optional
from app.models.schemas import CodeChunk
from app.core.config import settings
import hashlib


class SemanticChunker:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.tokenizer.encode(text))
    
    def split_by_tokens(self, text: str, max_tokens: int) -> List[str]:
        """按token数量分割文本"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
        return chunks
    
    def find_semantic_boundaries(self, code: str, language: str) -> List[int]:
        """找到语义边界位置"""
        boundaries = [0]
        
        if language == "python":
            # Python语义边界：函数、类、主要代码块
            patterns = [
                r'^\s*(def|class|async def)\s+\w+',
                r'^\s*@\w+',  # decorators
                r'^\s*(if|for|while|try|with|except|finally|else|elif)\s+',
                r'^\s*#\s*.*$',  # 注释行
            ]
        elif language in ["javascript", "typescript", "jsx", "tsx"]:
            # JavaScript/TypeScript语义边界
            patterns = [
                r'^\s*(function|const|let|var|class)\s+\w+',
                r'^\s*(if|for|while|try|catch|finally|else)\s+',
                r'^\s*//\s*.*$',  # 单行注释
                r'^\s*/\*.*\*/\s*$',  # 多行注释
            ]
        else:
            # 通用模式
            patterns = [
                r'^\s*\w+\s+\w+\s*[\(\{]',  # 函数定义
                r'^\s*(if|for|while|try|catch)\s+',
                r'^\s*//\s*.*$',
                r'^\s*#\s*.*$',
            ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.match(pattern, line):
                    boundaries.append(i)
                    break
        
        boundaries.append(len(lines))
        return sorted(list(set(boundaries)))
    
    def create_chunk(self, content: str, file_path: str, start_line: int, 
                    end_line: int, language: str, chunk_id: Optional[str] = None) -> CodeChunk:
        """创建代码块"""
        if not chunk_id:
            chunk_id = hashlib.md5(f"{file_path}:{start_line}:{end_line}".encode()).hexdigest()
            
        return CodeChunk(
            id=chunk_id,
            content=content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            language=language,
            token_count=self.count_tokens(content),
            metadata={
                "line_count": end_line - start_line + 1,
                "char_count": len(content),
            }
        )
    
    def chunk_code(self, code: str, file_path: str, language: str, 
                  max_chunk_size: Optional[int] = None) -> List[CodeChunk]:
        """语义分块主方法"""
        if not max_chunk_size:
            max_chunk_size = settings.max_chunk_size
        
        # 找到语义边界
        boundaries = self.find_semantic_boundaries(code, language)
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start_line = boundaries[i]
            end_line = boundaries[i + 1] - 1
            
            # 提取这一段的代码
            lines = code.split('\n')
            chunk_content = '\n'.join(lines[start_line:end_line + 1])
            
            # 检查token数量
            token_count = self.count_tokens(chunk_content)
            
            if token_count <= max_chunk_size:
                # 如果不超过最大大小，直接创建块
                chunk = self.create_chunk(chunk_content, file_path, start_line, end_line, language)
                chunks.append(chunk)
            else:
                # 如果太大，进一步分割
                sub_chunks = self.split_by_tokens(chunk_content, max_chunk_size)
                for j, sub_content in enumerate(sub_chunks):
                    sub_start = start_line + j * (len(lines) // len(sub_chunks))
                    sub_end = min(sub_start + len(lines) // len(sub_chunks), end_line)
                    chunk = self.create_chunk(sub_content, file_path, sub_start, sub_end, language)
                    chunks.append(chunk)
        
        # 添加重叠
        overlap_chunks = self._add_overlap(chunks)
        return overlap_chunks
    
    def _add_overlap(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """为代码块添加重叠"""
        if len(chunks) <= 1:
            return chunks
        
        overlap_size = int(settings.max_chunk_size * settings.chunk_overlap_ratio)
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            
            # 获取前一个块的末尾部分作为重叠
            prev_chunk = chunks[i - 1]
            prev_lines = prev_chunk.content.split('\n')
            
            # 计算重叠的行数
            overlap_lines = max(1, len(prev_lines) // 4)  # 1/4的重叠
            
            if overlap_lines > 0:
                overlap_content = '\n'.join(prev_lines[-overlap_lines:])
                combined_content = overlap_content + '\n' + chunk.content
                
                # 创建新的重叠块
                overlapped_chunk = self.create_chunk(
                    combined_content,
                    chunk.file_path,
                    prev_chunk.end_line - overlap_lines + 1,
                    chunk.end_line,
                    chunk.language,
                    chunk.id + "_overlap"
                )
                overlapped_chunks.append(overlapped_chunk)
            else:
                overlapped_chunks.append(chunk)
        
        return overlapped_chunks