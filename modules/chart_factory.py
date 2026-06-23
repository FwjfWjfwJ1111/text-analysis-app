from enum import Enum
from typing import List, Tuple, Any

from pyecharts.charts import WordCloud, Bar, Pie, Line, Radar
from pyecharts import options as opts


class ChartType(Enum):
    WORD_CLOUD = "词云图"
    BAR = "柱状图"
    HORIZONTAL_BAR = "横向柱状图"
    LINE = "折线图"
    AREA = "面积图"
    PIE = "饼图"
    RADAR = "雷达图"


class ChartFactoryError(Exception):
    user_message = "图表生成失败"


def _build_word_cloud(top20: List[Tuple[str, int]], title: str) -> WordCloud:
    return (
        WordCloud()
        .add("", top20, word_size_range=[20, 90])
        .set_global_opts(title_opts=opts.TitleOpts(title=title))
    )


def _build_bar(top20: List[Tuple[str, int]], title: str) -> Bar:
    labels = [i[0] for i in top20]
    values = [i[1] for i in top20]
    return (
        Bar(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(labels)
        .add_yaxis("词频", values)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(
                    rotate=45, font_size=8, overflow="break"
                ),
                interval=0
            )
        )
    )


def _build_horizontal_bar(top20: List[Tuple[str, int]], title: str) -> Bar:
    labels = [i[0] for i in top20]
    values = [i[1] for i in top20]
    return (
        Bar(init_opts=opts.InitOpts(width="100%", height="900px"))
        .add_xaxis(labels)
        .add_yaxis("词频", values)
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(
                    font_size=7,
                    overflow="break",
                    margin=3
                ),
                interval=0,
                split_number=20,
            ),
            datazoom_opts=[opts.DataZoomOpts(type_="inside")]
        )
    )


def _build_line(top20: List[Tuple[str, int]], title: str) -> Line:
    labels = [i[0] for i in top20]
    values = [i[1] for i in top20]
    return (
        Line(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(labels)
        .add_yaxis("词频", values)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45, font_size=8),
                interval=0
            )
        )
    )


def _build_area(top20: List[Tuple[str, int]], title: str) -> Line:
    labels = [i[0] for i in top20]
    values = [i[1] for i in top20]
    return (
        Line(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(labels)
        .add_yaxis("词频", values, areastyle_opts=opts.AreaStyleOpts(opacity=0.4))
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45, font_size=8),
                interval=0
            )
        )
    )


def _build_pie(top20: List[Tuple[str, int]], title: str) -> Pie:
    return (
        Pie(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add(
            series_name="词频",
            data_pair=top20,
            center=["60%", "62%"],
            radius=["35%", "60%"],
            label_opts=opts.LabelOpts(position="outside", formatter="{b}: {c} ({d}%)", font_size=10)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_top="1%", pos_left="center"),
            legend_opts=opts.LegendOpts(is_show=False)
        )
    )


def _build_radar(top20: List[Tuple[str, int]], title: str) -> Radar:
    labels = [i[0] for i in top20]
    values = [i[1] for i in top20]
    max_value = max(values) + 5 if values else 10
    
    indicators = [opts.RadarIndicatorItem(name=l, max_=max_value) for l in labels]
    return (
        Radar(init_opts=opts.InitOpts(width="100%", height="800px"))
        .add_schema(schema=indicators, textstyle_opts=opts.TextStyleOpts(font_size=7))
        .add("词频", [values])
        .set_global_opts(title_opts=opts.TitleOpts(title=title))
    )


def create_chart(chart_type: ChartType, top20: List[Tuple[str, int]], title: str) -> Any:
    """
    根据图表类型创建对应的 pyecharts 图表对象。

    Args:
        chart_type: ChartType 枚举值
        top20: Top20 词频数据 [(word, freq), ...]
        title: 图表标题

    Returns:
        pyecharts 图表对象

    Raises:
        ChartFactoryError: 数据为空或图表类型无效
    """
    if not top20:
        raise ChartFactoryError("词频数据为空，无法生成图表")
    
    builders = {
        ChartType.WORD_CLOUD: _build_word_cloud,
        ChartType.BAR: _build_bar,
        ChartType.HORIZONTAL_BAR: _build_horizontal_bar,
        ChartType.LINE: _build_line,
        ChartType.AREA: _build_area,
        ChartType.PIE: _build_pie,
        ChartType.RADAR: _build_radar,
    }
    
    builder = builders.get(chart_type)
    if not builder:
        raise ChartFactoryError(f"不支持的图表类型: {chart_type}")
    
    return builder(top20, title)


def _prepare_comparison_data(
    top20_a: List[Tuple[str, int]],
    top20_b: List[Tuple[str, int]]
) -> Tuple[List[str], List[int], List[int]]:
    words_a = dict(top20_a)
    words_b = dict(top20_b)
    
    all_words = sorted(set(words_a.keys()) | set(words_b.keys()), key=lambda x: -(words_a.get(x, 0) + words_b.get(x, 0)))
    
    values_a = [words_a.get(w, 0) for w in all_words]
    values_b = [words_b.get(w, 0) for w in all_words]
    
    return all_words, values_a, values_b


def create_comparison_bar(
    top20_a: List[Tuple[str, int]],
    top20_b: List[Tuple[str, int]],
    label_a: str,
    label_b: str,
    title: str
) -> Bar:
    """
    创建文本对比叠加柱状图。

    Args:
        top20_a: 文本 A 的 Top20 词频数据
        top20_b: 文本 B 的 Top20 词频数据
        label_a: 文本 A 的来源标签
        label_b: 文本 B 的来源标签
        title: 图表标题

    Returns:
        Bar 图表对象（叠加柱状图）

    Raises:
        ChartFactoryError: 数据为空
    """
    if not top20_a and not top20_b:
        raise ChartFactoryError("对比数据为空")
    
    all_words, values_a, values_b = _prepare_comparison_data(top20_a, top20_b)
    
    return (
        Bar(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(all_words)
        .add_yaxis(label_a, values_a)
        .add_yaxis(label_b, values_b)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(
                    rotate=45, font_size=8, overflow="break"
                ),
                interval=0
            ),
            legend_opts=opts.LegendOpts(pos_top="5%")
        )
    )


def create_comparison_line(
    top20_a: List[Tuple[str, int]],
    top20_b: List[Tuple[str, int]],
    label_a: str,
    label_b: str,
    title: str
) -> Line:
    """
    创建文本对比折线图。

    Args:
        top20_a: 文本 A 的 Top20 词频数据
        top20_b: 文本 B 的 Top20 词频数据
        label_a: 文本 A 的来源标签
        label_b: 文本 B 的来源标签
        title: 图表标题

    Returns:
        Line 图表对象

    Raises:
        ChartFactoryError: 数据为空
    """
    if not top20_a and not top20_b:
        raise ChartFactoryError("对比数据为空")
    
    all_words, values_a, values_b = _prepare_comparison_data(top20_a, top20_b)
    
    return (
        Line(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(all_words)
        .add_yaxis(label_a, values_a)
        .add_yaxis(label_b, values_b)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45, font_size=8),
                interval=0
            ),
            legend_opts=opts.LegendOpts(pos_top="5%")
        )
    )


def create_comparison_area(
    top20_a: List[Tuple[str, int]],
    top20_b: List[Tuple[str, int]],
    label_a: str,
    label_b: str,
    title: str
) -> Line:
    """
    创建文本对比面积图。

    Args:
        top20_a: 文本 A 的 Top20 词频数据
        top20_b: 文本 B 的 Top20 词频数据
        label_a: 文本 A 的来源标签
        label_b: 文本 B 的来源标签
        title: 图表标题

    Returns:
        Line 图表对象（带面积填充）

    Raises:
        ChartFactoryError: 数据为空
    """
    if not top20_a and not top20_b:
        raise ChartFactoryError("对比数据为空")
    
    all_words, values_a, values_b = _prepare_comparison_data(top20_a, top20_b)
    
    return (
        Line(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add_xaxis(all_words)
        .add_yaxis(label_a, values_a, areastyle_opts=opts.AreaStyleOpts(opacity=0.3))
        .add_yaxis(label_b, values_b, areastyle_opts=opts.AreaStyleOpts(opacity=0.3))
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45, font_size=8),
                interval=0
            ),
            legend_opts=opts.LegendOpts(pos_top="5%")
        )
    )


def create_comparison_pie(
    top20_a: List[Tuple[str, int]],
    top20_b: List[Tuple[str, int]],
    label_a: str,
    label_b: str,
    title: str
) -> Pie:
    """
    创建文本对比环形饼图（两图并排）。

    Args:
        top20_a: 文本 A 的 Top20 词频数据
        top20_b: 文本 B 的 Top20 词频数据
        label_a: 文本 A 的来源标签
        label_b: 文本 B 的来源标签
        title: 图表标题

    Returns:
        Pie 图表对象

    Raises:
        ChartFactoryError: 数据为空
    """
    if not top20_a and not top20_b:
        raise ChartFactoryError("对比数据为空")
    
    return (
        Pie(init_opts=opts.InitOpts(width="100%", height="600px"))
        .add(
            series_name=label_a,
            data_pair=top20_a[:10],
            center=["25%", "50%"],
            radius=["30%", "55%"],
            label_opts=opts.LabelOpts(position="inside", formatter="{b}\n{d}%", font_size=8)
        )
        .add(
            series_name=label_b,
            data_pair=top20_b[:10],
            center=["75%", "50%"],
            radius=["30%", "55%"],
            label_opts=opts.LabelOpts(position="inside", formatter="{b}\n{d}%", font_size=8)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_top="1%", pos_left="center"),
            legend_opts=opts.LegendOpts(pos_bottom="5%")
        )
    )


class ComparisonChartType(Enum):
    BAR = "对比柱状图"
    LINE = "对比折线图"
    AREA = "对比面积图"
    PIE = "对比饼图"


def create_comparison_chart(
    chart_type: ComparisonChartType,
    top20_a: List[Tuple[str, int]],
    top20_b: List[Tuple[str, int]],
    label_a: str,
    label_b: str,
    title: str
) -> Any:
    """
    根据图表类型创建对比图表。

    Args:
        chart_type: ComparisonChartType 枚举值
        top20_a: 文本 A 的 Top20 词频数据
        top20_b: 文本 B 的 Top20 词频数据
        label_a: 文本 A 的来源标签
        label_b: 文本 B 的来源标签
        title: 图表标题

    Returns:
        pyecharts 图表对象

    Raises:
        ChartFactoryError: 数据为空或图表类型无效
    """
    builders = {
        ComparisonChartType.BAR: create_comparison_bar,
        ComparisonChartType.LINE: create_comparison_line,
        ComparisonChartType.AREA: create_comparison_area,
        ComparisonChartType.PIE: create_comparison_pie,
    }
    
    builder = builders.get(chart_type)
    if not builder:
        raise ChartFactoryError(f"不支持的对比图表类型: {chart_type}")
    
    return builder(top20_a, top20_b, label_a, label_b, title)