import pytest
from pyecharts.charts import WordCloud, Bar, Pie, Line, Radar
from modules.chart_factory import ChartType, create_chart, create_comparison_bar, ChartFactoryError


def test_create_word_cloud():
    top20 = [("测试", 10), ("人工智能", 8), ("改变", 5)]
    chart = create_chart(ChartType.WORD_CLOUD, top20, "测试")
    assert isinstance(chart, WordCloud)


def test_create_bar():
    top20 = [("测试", 10), ("人工智能", 8)]
    chart = create_chart(ChartType.BAR, top20, "测试")
    assert isinstance(chart, Bar)


def test_create_horizontal_bar():
    top20 = [("测试", 10), ("人工智能", 8)]
    chart = create_chart(ChartType.HORIZONTAL_BAR, top20, "测试")
    assert isinstance(chart, Bar)


def test_create_line():
    top20 = [("测试", 10), ("人工智能", 8)]
    chart = create_chart(ChartType.LINE, top20, "测试")
    assert isinstance(chart, Line)


def test_create_area():
    top20 = [("测试", 10), ("人工智能", 8)]
    chart = create_chart(ChartType.AREA, top20, "测试")
    assert isinstance(chart, Line)


def test_create_pie():
    top20 = [("测试", 10), ("人工智能", 8)]
    chart = create_chart(ChartType.PIE, top20, "测试")
    assert isinstance(chart, Pie)


def test_create_radar():
    top20 = [("测试", 10), ("人工智能", 8), ("改变", 6), ("世界", 4), ("生活", 3), ("技术", 2)]
    chart = create_chart(ChartType.RADAR, top20, "测试")
    assert isinstance(chart, Radar)


def test_create_chart_empty_data():
    top20 = []
    with pytest.raises(ChartFactoryError):
        create_chart(ChartType.WORD_CLOUD, top20, "测试")


def test_create_comparison_bar():
    top20_a = [("测试", 10), ("人工智能", 8)]
    top20_b = [("测试", 5), ("改变", 6)]
    
    chart = create_comparison_bar(top20_a, top20_b, "文本A", "文本B", "对比")
    assert isinstance(chart, Bar)


def test_create_comparison_bar_empty_both():
    top20_a = []
    top20_b = []
    
    with pytest.raises(ChartFactoryError):
        create_comparison_bar(top20_a, top20_b, "文本A", "文本B", "对比")