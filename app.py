import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter

from pyecharts.charts import WordCloud, Bar, Pie, Line, Radar
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts


def main():
    # ================= 页面设置 =================
    st.set_page_config(
        page_title="文本词频分析与可视化系统",
        layout="wide"  # 强制宽布局，给图表更多空间
    )

    st.markdown(
        """
        # 📊 文本词频分析与可视化系统  
        **流程：** 输入 URL → 抓取文本 → 分词统计 → 可视化展示
        """
    )

    st.divider()

    # ================= Sidebar =================
    st.sidebar.title("🧩 参数控制面板")

    chart_type = st.sidebar.radio(
        "选择可视化图形",
        (
            "词云图",
            "柱状图",
            "横向柱状图",
            "折线图",
            "面积图",
            "饼图",
            "雷达图"
        )
    )

    min_freq = st.sidebar.slider(
        "最低词频过滤（≥）",
        1, 15, 2
    )

    st.sidebar.info(
        "📌 支持 7 种图形切换\\n\\n"
        "📈 默认展示词频 Top20"
    )

    # ================= 主页面布局 =================
    left, right = st.columns([2, 4])  # 增大右侧图表区域的宽度占比

    with left:
        st.subheader("🔗 输入文章 URL")
        url = st.text_input(
            "输入后直接按 Enter 开始分析",
            placeholder="https://..."
        )

    with right:
        st.subheader("📈 可视化结果区域")
        st.caption("图表将根据参数自动更新")

    # ================= 业务逻辑 =================
    if url:
        try:
            # 1. 抓取网页
            response = requests.get(url, timeout=10)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()

            # 2. 分词
            words = jieba.lcut(text)
            words = [w for w in words if len(w) > 1 and w.strip()]

            # 3. 词频统计
            counter = Counter(words)
            counter = Counter({k: v for k, v in counter.items() if v >= min_freq})
            top20 = counter.most_common(20)  # 确认取20个数据

            labels = [i[0] for i in top20]
            values = [i[1] for i in top20]


            # ===== 左侧：词频表 =====
            with left:
                st.markdown("### 🏆 高频词 Top20")
                st.dataframe(
                    [{"词语": k, "出现次数": v} for k, v in top20],
                    use_container_width=True
                )

            # ===== 右侧：图表 =====
            with right:
                chart = None

                if chart_type == "词云图":
                    chart = (
                        WordCloud()
                        .add("", top20, word_size_range=[20, 90])
                        .set_global_opts(title_opts=opts.TitleOpts(title="词云分析结果"))
                    )

                elif chart_type == "柱状图":
                    chart = (
                        Bar(init_opts=opts.InitOpts(width="100%", height="600px"))
                        .add_xaxis(labels)
                        .add_yaxis("词频", values)
                        .set_global_opts(
                            title_opts=opts.TitleOpts(title="词频柱状图"),
                            xaxis_opts=opts.AxisOpts(
                                axislabel_opts=opts.LabelOpts(
                                    rotate=45, font_size=8, overflow="break"
                                ),
                                interval=0  # 强制显示所有X轴标签
                            )
                        )
                    )

                elif chart_type == "横向柱状图":
                    # 核心优化：横向柱状图（重点解决只显示10个的问题）
                    chart = (
                        # 1. 增大图表高度，足够容纳20个标签
                        Bar(init_opts=opts.InitOpts(width="100%", height="900px"))
                        .add_xaxis(labels)
                        .add_yaxis("词频", values)
                        .reversal_axis()  # 反转轴，变成横向
                        .set_global_opts(
                            title_opts=opts.TitleOpts(title="横向词频对比图"),
                            # 2. 强制显示所有Y轴标签（横向图的标签在Y轴）
                            yaxis_opts=opts.AxisOpts(
                                axislabel_opts=opts.LabelOpts(
                                    font_size=7,  # 最小化字体，减少占用空间
                                    overflow="break",  # 标签换行
                                    margin=3  # 缩小标签间距
                                ),
                                interval=0,  # 关键：强制显示所有标签，不截断
                                split_number=20,  # 强制分割为20个刻度
                            ),
                            # 3. 关闭自动缩放，避免标签被隐藏
                            datazoom_opts=[opts.DataZoomOpts(type_="inside")]
                        )
                    )

                elif chart_type == "折线图":
                    chart = (
                        Line(init_opts=opts.InitOpts(width="100%", height="600px"))
                        .add_xaxis(labels)
                        .add_yaxis("词频", values)
                        .set_global_opts(
                            title_opts=opts.TitleOpts(title="词频折线图"),
                            xaxis_opts=opts.AxisOpts(
                                axislabel_opts=opts.LabelOpts(rotate=45, font_size=8),
                                interval=0
                            )
                        )
                    )

                elif chart_type == "面积图":
                    chart = (
                        Line(init_opts=opts.InitOpts(width="100%", height="600px"))
                        .add_xaxis(labels)
                        .add_yaxis("词频", values, areastyle_opts=opts.AreaStyleOpts(opacity=0.4))
                        .set_global_opts(
                            title_opts=opts.TitleOpts(title="词频面积图"),
                            xaxis_opts=opts.AxisOpts(
                                axislabel_opts=opts.LabelOpts(rotate=45, font_size=8),
                                interval=0
                            )
                        )
                    )

                elif chart_type == "饼图":
                    chart = (
                        Pie(init_opts=opts.InitOpts(width="100%", height="600px"))
                        .add(
                            series_name="词频",
                            data_pair=top20,
                            center=["60%", "62%"],
                            radius=["35%", "60%"],
                            label_opts=opts.LabelOpts(position="outside", formatter="{b}: {c} ({d}%)", font_size=10)
                        )
                        .set_global_opts(
                            title_opts=opts.TitleOpts(title="词频占比饼图", pos_top="1%", pos_left="center"),
                            legend_opts=opts.LegendOpts(is_show=False)
                        )
                    )
                    st_pyecharts(chart, height="600px")
                    chart = None

                elif chart_type == "雷达图":
                    indicators = [opts.RadarIndicatorItem(name=l, max_=max(values)+5) for l in labels]
                    chart = (
                        Radar(init_opts=opts.InitOpts(width="100%", height="700px"))
                        .add_schema(schema=indicators, textstyle_opts=opts.TextStyleOpts(font_size=10))
                        .add("词频", [values])
                        .set_global_opts(title_opts=opts.TitleOpts(title="词频雷达图"))
                    )
                    st_pyecharts(chart, height="700px", width="100%")
                    chart = None

                # ===== 统一渲染其他图形 =====
                if chart:
                    if chart_type == "横向柱状图":
                        # 4. 渲染时再强制指定高度，双重保障
                        st_pyecharts(chart, height="900px", width="100%")
                    else:
                        st_pyecharts(chart, height="600px", width="100%")

        except Exception as e:
            st.error(f"文本解析或处理失败：{e}")


# ================= 主函数入口 =================
if __name__ == "__main__":
    main()