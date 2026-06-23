import re
import jieba
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple


class EmptyTextError(Exception):
    user_message = "无有效中文内容，请输入包含中文的文本"


@dataclass
class AnalysisResult:
    raw_text: str
    cleaned_text: str
    words: List[str]
    filtered_words: List[str]
    top20: List[Tuple[str, int]]
    all_freq: List[Tuple[str, int]]
    total_words: int
    vocabulary_size: int


def clean_text(raw: str) -> str:
    """
    清洗原始文本：去多余空白、保留中文/数字/字母/常用标点。

    Args:
        raw: 原始文本字符串

    Returns:
        清洗后的文本
    """
    text = ' '.join(raw.split())
    text = re.sub(
        r'[^一-龥a-zA-Z0-9，。！？；：""''（）【】《》、·]',
        '', text
    )
    return text


def segment_words(text: str) -> List[str]:
    """
    使用 jieba 精确模式分词。

    Args:
        text: 清洗后的文本

    Returns:
        分词结果列表
    """
    return jieba.lcut(text)


def filter_words(words: List[str]) -> List[str]:
    """
    过滤掉单字和空白词。

    Args:
        words: 分词结果列表

    Returns:
        过滤后的词语列表
    """
    return [w for w in words if len(w) > 1 and w.strip()]


def count_and_rank(words: List[str], min_freq: int = 1) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """
    词频统计并排序。

    Args:
        words: 过滤后的词语列表
        min_freq: 最低词频阈值

    Returns:
        (top20, all_freq) - 按阈值过滤的Top20和全量词频
    """
    all_counter = Counter(words)
    all_freq = sorted(all_counter.items(), key=lambda x: x[1], reverse=True)
    
    filtered_counter = Counter({k: v for k, v in all_counter.items() if v >= min_freq})
    top20 = filtered_counter.most_common(20)
    
    return top20, all_freq


def analyze(raw_text: str, min_freq: int = 1) -> AnalysisResult:
    """
    端到端文本分析管线：清洗 → 分词 → 过滤 → 统计。

    Args:
        raw_text: 原始文本
        min_freq: 最低词频阈值

    Returns:
        AnalysisResult 数据类

    Raises:
        EmptyTextError: 输入文本为空或无有效中文内容
    """
    if not raw_text or not raw_text.strip():
        raise EmptyTextError()
    
    cleaned_text = clean_text(raw_text)
    
    if not cleaned_text or not cleaned_text.strip():
        raise EmptyTextError()
    
    words = segment_words(cleaned_text)
    filtered_words = filter_words(words)
    
    if not filtered_words:
        raise EmptyTextError()
    
    top20, all_freq = count_and_rank(filtered_words, min_freq)
    
    return AnalysisResult(
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        words=words,
        filtered_words=filtered_words,
        top20=top20,
        all_freq=all_freq,
        total_words=len(filtered_words),
        vocabulary_size=len(all_freq)
    )