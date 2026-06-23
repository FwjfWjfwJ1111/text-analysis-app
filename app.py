import streamlit as st
from streamlit_echarts import st_pyecharts
from datetime import datetime

from modules.fetch_web import (
    fetch_url_text, read_uploaded_file,
    FetchError, FetchConnectionError, FetchHTTPError,
    FetchTimeoutError, FetchContentTypeError, FetchEncodingError
)
from modules.text_clean_token import analyze, EmptyTextError, AnalysisResult
from modules.chart_factory import ChartType, create_chart, ComparisonChartType, create_comparison_chart
from modules.history import (
    load_history, save_record, delete_record, clear_all, get_record_by_id
)


def init_session_state():
    default_keys = {
        "current_tab": "url",
        "url_input": "",
        "paste_input": "",
        "uploaded_content": "",
        "uploaded_filename": "",
        "analysis_result": None,
        "selected_history_ids": [],
        "viewing_history_id": None,
        "comparing_records": None,
    }
    for key, default in default_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default


def get_chart_type_from_display_name(display_name: str) -> ChartType:
    for ct in ChartType:
        if ct.value == display_name:
            return ct
    return ChartType.WORD_CLOUD


def render_chart(chart_type: ChartType, top20, min_freq: int, title_suffix: str = ""):
    title = f"{chart_type.value}（Top20，词频≥{min_freq}）{title_suffix}"
    chart = create_chart(chart_type, top20, title)
    
    if chart_type == ChartType.HORIZONTAL_BAR:
        st_pyecharts(chart, height="900px", width="100%")
    elif chart_type == ChartType.RADAR:
        st_pyecharts(chart, height="700px", width="100%")
    elif chart_type == ChartType.PIE:
        st_pyecharts(chart, height="600px")
    else:
        st_pyecharts(chart, height="600px", width="100%")


def render_top20_table(top20, min_freq: int, title: str = ""):
    st.markdown(f"### 🏆 高频词 Top20（词频≥{min_freq}）{title}")
    st.dataframe(
        [{"词语": k, "出现次数": v} for k, v in top20],
        use_container_width=True,
        hide_index=True
    )


def render_history_panel():
    history = load_history()
    
    if not history:
        return
    
    st.divider()
    with st.expander("📜 历史记录", expanded=False):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("**按时间倒序排列，最多保留 50 条记录**")
        with col2:
            if st.button("🗑 清空全部历史", use_container_width=True):
                if st.session_state.get("clear_confirm", False):
                    clear_all()
                    st.session_state.selected_history_ids = []
                    st.session_state.viewing_history_id = None
                    st.session_state.clear_confirm = False
                    st.rerun()
                else:
                    st.session_state.clear_confirm = True
                    st.warning("再次点击确认清空所有历史记录")
                    return
        
        selected_ids = []
        for record in history:
            record_id = record["id"]
            timestamp = record["timestamp"]
            source_type = record["source_type"]
            source_label = record["source_label"]
            top3 = ", ".join([f"{w}({f})" for w, f in record["top20"][:3]])
            min_freq = record["min_freq"]
            
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = timestamp[:16]
            
            icon = {"url": "🔗", "upload": "📄", "paste": "📋"}.get(source_type, "📝")
            
            cols = st.columns([1, 3, 2, 1.5, 1.5])
            with cols[0]:
                checked = st.checkbox(
                    "",
                    key=f"history_check_{record_id}",
                    value=record_id in st.session_state.selected_history_ids,
                    label_visibility="collapsed"
                )
                if checked:
                    selected_ids.append(record_id)
            
            with cols[1]:
                st.markdown(f"**{icon} {source_label}**")
                st.caption(f"{time_str} | 词频阈值: ≥{min_freq}")
            
            with cols[2]:
                st.markdown(f"Top3: {top3}")
            
            with cols[3]:
                if st.button(
                    "📂 查看",
                    key=f"view_{record_id}",
                    use_container_width=True
                ):
                    st.session_state.viewing_history_id = record_id
                    st.session_state.comparing_records = None
                    st.rerun()
            
            with cols[4]:
                if st.button(
                    "🗑 删除",
                    key=f"delete_{record_id}",
                    use_container_width=True
                ):
                    delete_record(record_id)
                    if st.session_state.viewing_history_id == record_id:
                        st.session_state.viewing_history_id = None
                    st.session_state.selected_history_ids = [
                        id for id in st.session_state.selected_history_ids
                        if id != record_id
                    ]
                    st.rerun()
            
            st.markdown("---")
        
        st.session_state.selected_history_ids = selected_ids
        
        if len(selected_ids) == 2:
            if st.button("🔄 对比选中记录", use_container_width=True):
                record_a = get_record_by_id(selected_ids[0])
                record_b = get_record_by_id(selected_ids[1])
                st.session_state.comparing_records = {
                    "a": record_a,
                    "b": record_b
                }
                st.session_state.viewing_history_id = None
                st.rerun()
        elif len(selected_ids) == 0:
            st.info("请勾选 2 条记录进行对比")
        elif len(selected_ids) == 1:
            st.info("还需再勾选 1 条记录")
        else:
            st.warning("最多选择 2 条记录")


def render_comparison_view():
    comp = st.session_state.comparing_records
    if not comp:
        return
    
    record_a = comp["a"]
    record_b = comp["b"]
    
    if st.button("← 退出对比", use_container_width=True):
        st.session_state.comparing_records = None
        st.session_state.selected_history_ids = []
        st.rerun()
    
    if record_a["min_freq"] != record_b["min_freq"]:
        st.info(
            f"注意：文本 A 词频阈值={record_a['min_freq']}，"
            f"文本 B 词频阈值={record_b['min_freq']}，Top20 对比不完全对等"
        )
    
    st.markdown("## 📊 文本对比视图")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown(f"### 📄 {record_a['source_label']}")
        render_top20_table(record_a["top20"], record_a["min_freq"])
    
    with col_b:
        st.markdown(f"### 📄 {record_b['source_label']}")
        render_top20_table(record_b["top20"], record_b["min_freq"])
    
    st.markdown("---")
    
    col_chart_type, _ = st.columns([2, 4])
    with col_chart_type:
        comparison_chart_type_display = st.selectbox(
            "选择对比图表类型",
            [ct.value for ct in ComparisonChartType],
            key="comparison_chart_type"
        )
    
    comparison_chart_type = None
    for ct in ComparisonChartType:
        if ct.value == comparison_chart_type_display:
            comparison_chart_type = ct
            break
    
    chart = create_comparison_chart(
        comparison_chart_type,
        record_a["top20"],
        record_b["top20"],
        record_a["source_label"],
        record_b["source_label"],
        f"词频对比：{record_a['source_label']} vs {record_b['source_label']}"
    )
    st_pyecharts(chart, height="600px", width="100%")


def render_history_view():
    record_id = st.session_state.viewing_history_id
    if not record_id:
        return
    
    record = get_record_by_id(record_id)
    if not record:
        st.session_state.viewing_history_id = None
        return
    
    if st.button("← 返回当前分析", use_container_width=True):
        st.session_state.viewing_history_id = None
        st.rerun()
    
    st.info(f"正在查看历史记录：{record['source_label']}")
    
    top20 = record["top20"]
    min_freq = record["min_freq"]
    chart_type = get_chart_type_from_display_name(record["chart_type"])
    
    render_chart(chart_type, top20, min_freq, f"（历史记录）")
    render_top20_table(top20, min_freq)


def render_analysis_result(result: AnalysisResult, min_freq: int, chart_type: ChartType):
    top20 = result.top20
    
    if not top20:
        st.warning("无符合阈值的词汇，请降低词频过滤阈值")
        return
    
    render_chart(chart_type, top20, min_freq)
    render_top20_table(top20, min_freq)
    
    with st.expander("🧹 清洗后的文本", expanded=False):
        st.info(
            f"📊 文本统计：\n"
            f"清洗后字符数 {len(result.cleaned_text)} | "
            f"分词总数 {len(result.words)} | "
            f"过滤后分词数 {len(result.filtered_words)} | "
            f"总词汇数（去重）{len(result.all_freq)}"
        )
        st.text_area(
            label="清洗后文本",
            value=result.cleaned_text,
            height=200,
            placeholder="清洗后的文本将显示在这里...",
            label_visibility="collapsed"
        )
    
    with st.expander("📋 全量词频统计", expanded=False):
        freq_df = [{"词语": k, "出现次数": v} for k, v in result.all_freq]
        st.dataframe(
            freq_df,
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"共 {len(freq_df)} 个词汇（词频≥1，无过滤）")


def perform_analysis(raw_text: str, source_type: str, source_label: str, min_freq: int, chart_type: ChartType):
    try:
        with st.spinner("正在分析文本..."):
            result = analyze(raw_text, min_freq)
        
        st.session_state.analysis_result = result
        
        save_record({
            "source_type": source_type,
            "source_label": source_label,
            "text_preview": raw_text[:100] + "..." if len(raw_text) > 100 else raw_text,
            "total_words": result.total_words,
            "vocabulary_size": result.vocabulary_size,
            "top20": result.top20,
            "chart_type": chart_type.value,
            "min_freq": min_freq
        })
        
        st.toast("✅ 分析完成")
        return result
    
    except EmptyTextError as e:
        st.error(e.user_message)
    except Exception as e:
        st.error("系统内部错误，请刷新页面重试")
    return None


def main():
    init_session_state()
    
    st.set_page_config(
        page_title="文本词频分析与可视化系统",
        layout="wide"
    )
    
    st.markdown(
        """
        # 📊 文本词频分析与可视化系统  
        **流程：** 选择输入方式 → 输入文本 → 分词统计 → 可视化展示
        """
    )
    
    st.sidebar.title("🧩 参数控制面板")
    
    chart_type_display = st.sidebar.radio(
        "选择可视化图形",
        [ct.value for ct in ChartType]
    )
    chart_type = get_chart_type_from_display_name(chart_type_display)
    
    min_freq = st.sidebar.slider(
        "最低词频过滤（≥）",
        1, 15, 2
    )
    
    st.sidebar.info(
        "📌 支持 7 种图形切换\\n\\n"
        "📈 图表/Top20表格：按所选阈值过滤\\n"
        "📋 全量词频面板：显示所有词频≥1的词汇"
    )
    
    tab_labels = {"url": "🔗 URL 输入", "upload": "📁 上传文件", "paste": "📋 粘贴文本"}
    tabs = st.tabs(list(tab_labels.values()))
    
    tab_map = {0: "url", 1: "upload", 2: "paste"}
    
    with tabs[0]:
        st.subheader("输入文章 URL")
        st.session_state.url_input = st.text_input(
            "输入后按 Enter 或点击下方按钮开始分析",
            value=st.session_state.url_input,
            placeholder="https://..."
        )
        if st.button("🔍 开始分析（URL）", use_container_width=True):
            if st.session_state.url_input.strip():
                try:
                    raw_text = fetch_url_text(st.session_state.url_input)
                    perform_analysis(
                        raw_text,
                        "url",
                        st.session_state.url_input,
                        min_freq,
                        chart_type
                    )
                except FetchConnectionError as e:
                    st.error(e.user_message)
                except FetchHTTPError as e:
                    st.error(e.user_message)
                except FetchTimeoutError as e:
                    st.error(e.user_message)
                except FetchContentTypeError as e:
                    st.error(e.user_message)
                except FetchEncodingError as e:
                    st.error(e.user_message)
                except Exception as e:
                    st.error("系统内部错误，请刷新页面重试")
    
    with tabs[1]:
        st.subheader("上传本地文件")
        uploaded_file = st.file_uploader(
            "选择 .txt 或 .md 文件",
            type=["txt", "md"]
        )
        if uploaded_file is not None:
            try:
                raw_bytes = uploaded_file.read()
                raw_text, encoding = read_uploaded_file(raw_bytes, uploaded_file.name)
                
                st.session_state.uploaded_content = raw_text
                st.session_state.uploaded_filename = uploaded_file.name
                
                st.success(f"文件读取成功（编码：{encoding}）")
                st.caption(f"文件内容预览：{raw_text[:100]}...")
                
                perform_analysis(
                    raw_text,
                    "upload",
                    uploaded_file.name,
                    min_freq,
                    chart_type
                )
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error("文件读取失败，请重试")
    
    with tabs[2]:
        st.subheader("粘贴文本")
        st.session_state.paste_input = st.text_area(
            "直接粘贴中文文本",
            value=st.session_state.paste_input,
            height=200,
            placeholder="请在此粘贴要分析的中文文本..."
        )
        if st.button("🔍 开始分析（粘贴）", use_container_width=True):
            if st.session_state.paste_input.strip():
                perform_analysis(
                    st.session_state.paste_input,
                    "paste",
                    "手动粘贴",
                    min_freq,
                    chart_type
                )
            else:
                st.warning("请输入文本后再分析")
    
    st.markdown(f"📌 当前将分析来自「{tab_labels[st.session_state.current_tab]}」的文本")
    
    if st.session_state.comparing_records:
        render_comparison_view()
    elif st.session_state.viewing_history_id:
        render_history_view()
    elif st.session_state.analysis_result:
        render_analysis_result(st.session_state.analysis_result, min_freq, chart_type)
    else:
        st.info("请在上方输入文本后点击「开始分析」")
    
    render_history_panel()


if __name__ == "__main__":
    main()