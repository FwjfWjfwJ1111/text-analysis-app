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
        layout="wide"
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
        "📌 支持 7 种图形切换\n\n"
        "📈 默认展示词频 Top20"
    )

    # ================= 主页面布局 =================
    left, right = st.columns([2, 3])

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
            top20 = counter.most_common(20)

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
                        Bar()
                        .add_xaxis(labels)
                        .add_yaxis("词频", values)
                        .set_global_opts(
                            title_opts=opts.TitleOpts(title="词频柱状图"),
                            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30))
                        )
                    )

                elif chart_type == "横向柱状图":
                    chart = (
                        Bar()
                        .add_xaxis(labels)
                        .add_yaxis("词频", values)
                        .reversal_axis()
                        .set_global_opts(title_opts=opts.TitleOpts(title="横向词频对比图"))
                    )

                elif chart_type == "折线图":
                    chart = Line().add_xaxis(labels).add_yaxis("词频", values).set_global_opts(
                        title_opts=opts.TitleOpts(title="词频折线图")
                    )

                elif chart_type == "面积图":
                    chart = (
                        Line()
                        .add_xaxis(labels)
                        .add_yaxis("词频", values, areastyle_opts=opts.AreaStyleOpts(opacity=0.4))
                        .set_global_opts(title_opts=opts.TitleOpts(title="词频面积图"))
                    )

                elif chart_type == "饼图":
                    chart = (
                        Pie()
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
                    st_pyecharts(chart)
                    chart = None  # 避免下面重复调用

                elif chart_type == "雷达图":
                    indicators = [opts.RadarIndicatorItem(name=l, max_=max(values)+5) for l in labels]
                    chart = (
                        Radar()
                        .add_schema(schema=indicators, textstyle_opts=opts.TextStyleOpts(font_size=10))
                        .add("词频", [values])
                        .set_global_opts(title_opts=opts.TitleOpts(title="词频雷达图"))
                    )
                    st_pyecharts(chart, height=500, width=700)
                    chart = None

                # ===== 统一渲染其他图形 =====
                if chart:
                    st_pyecharts(chart)

        except Exception as e:
            st.error(f"文本解析或处理失败：{e}")


# ================= 主函数入口 =================
if __name__ == "__main__":
    main()
