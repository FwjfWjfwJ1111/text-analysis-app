import pytest
from modules.text_clean_token import (
    clean_text, segment_words, filter_words, count_and_rank, analyze,
    EmptyTextError, AnalysisResult
)


def test_clean_text():
    raw = "  人工智能 正在\t改变\n世界！   "
    cleaned = clean_text(raw)
    assert cleaned == "人工智能正在改变世界！"
    
    raw_with_special = "hello@#$世界%^&测试"
    cleaned = clean_text(raw_with_special)
    assert cleaned == "hello世界测试"


def test_segment_words():
    text = "人工智能正在改变世界"
    words = segment_words(text)
    assert "人工智能" in words
    assert len(words) > 0


def test_filter_words():
    words = ["人", "人工智能", "改", "改变", " ", "测试"]
    filtered = filter_words(words)
    assert "人工智能" in filtered
    assert "改变" in filtered
    assert "测试" in filtered
    assert "人" not in filtered
    assert "改" not in filtered


def test_count_and_rank():
    words = ["人工智能", "人工智能", "改变", "世界", "改变", "人工智能"]
    top20, all_freq = count_and_rank(words, min_freq=1)
    
    assert top20[0][0] == "人工智能"
    assert top20[0][1] == 3
    assert top20[1][0] == "改变"
    assert top20[1][1] == 2
    
    top20_filtered, _ = count_and_rank(words, min_freq=2)
    assert len(top20_filtered) == 2
    assert top20_filtered[0][0] == "人工智能"


def test_analyze():
    text = "人工智能正在改变世界人工智能改变生活"
    result = analyze(text, min_freq=1)
    
    assert isinstance(result, AnalysisResult)
    assert result.total_words > 0
    assert result.vocabulary_size > 0
    assert len(result.top20) > 0
    assert len(result.all_freq) > 0


def test_analyze_empty_text():
    with pytest.raises(EmptyTextError):
        analyze("")
    
    with pytest.raises(EmptyTextError):
        analyze("   ")
    
    with pytest.raises(EmptyTextError):
        analyze("!!!$$$")