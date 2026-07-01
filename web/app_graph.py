# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
from pathlib import Path
root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root))

import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart
from eaagent.playbooks.manager import manager
from eaagent.tools.tushare_futures import get_futures_daily_with_ma, get_main_contracts, get_popular_main_contracts
from web.report_builder import build_analysis_report

def run_analysis(symbol, data_source, playbook_name, strategy_name="full"):
    # 设置数据源
    os.environ["USE_MOCK_OBSERVATION"] = "false" if data_source == "Tushare" else "true"
    os.environ["DATA_PROVIDER"] = "tushare_futures"
    os.environ["PLAYBOOK_STRATEGY"] = strategy_name  # 新增 Strategy 支持

    # 关键：先加载用户选择的 Playbook，拿到正确的 name
    content, name = manager.load(playbook_name)
    print(f"[DEBUG] Web 传递的 Playbook: {playbook_name} → 实际使用: {name} | Strategy: {strategy_name}")

    # 把正确的 name 传给 create_initial_state
    state = create_initial_state(symbol, playbook_name=name)

    app = build_graph()
    final_state = app.invoke(state, {"configurable": {"thread_id": state["thread_id"]}})

    signal = final_state.get("signals", [{}])[-1]
    extra = final_state.get("extra_data", {})
    news = final_state.get("news", [])  # 新增新闻传递给report

    # K线图 (仅从menu更新, analysis不重复)
    df_main = pd.DataFrame(extra.get("technical_indicators", []))
    if df_main.empty:
        df_main = get_futures_daily_with_ma(symbol, months=3)
    main_chart = create_candlestick_chart(df_main, symbol)

    # 3. Dynamic related (0-2 based on symbol, common correlations)
    related_codes = get_related_for_symbol(symbol)
    related_charts = []
    name_map = {"I": "铁矿石", "J": "焦炭", "JM": "焦煤", "SA": "纯碱", "FG": "玻璃", "AL": "沪铝", "AG": "沪银"}
    for rcode in related_codes[:2]:
        df_r = get_futures_daily_with_ma(rcode, months=2)
        rname = name_map.get(rcode.split('.')[0], rcode.split('.')[0])
        related_charts.append(create_candlestick_chart(df_r, f"{rcode} ({rname})"))
    i_chart = related_charts[0] if related_charts else None
    j_chart = related_charts[1] if len(related_charts) > 1 else None

    # 1. 真实分析过程 (report_builder Markdown 直接返回给 gr.Markdown, 高度匹配K线680px)
    console_text = build_analysis_report(final_state, symbol, data_source)
    # 保持Markdown格式 (gr.Markdown支持 ##, ```, ** 等, 比Textbox美观). News section added in report_builder.
    return console_text, main_chart, i_chart or main_chart, j_chart or main_chart

with gr.Blocks() as demo:
    gr.Markdown("# ApexLi • 期货主力合约菜单 + 动态 K线 (带过滤)")

    with gr.Row():
        # 合约过滤 (新功能)
        exchange_filter = gr.Dropdown(["全部", "SHF", "DCE", "CZCE"], value="全部", label="交易所过滤")
        search_box = gr.Textbox(placeholder="搜索合约 (如 RB 或 I)", label="合约搜索")
        popular_choices = get_popular_main_contracts()  # "中文 代码" format, e.g. "螺纹钢 RB2610.SHF"
        # Extract clean ts_code for initial value to avoid "value not in choices" warning
        initial_value = popular_choices[0].split()[-1] if popular_choices else "RB2610.SHF"
        popular_menu = gr.Dropdown(
            choices=popular_choices,
            value=initial_value,  # Must match one of the choice strings exactly (full "中文 代码")
            label="关注主力合约 (中文显示)",
            interactive=True
        )
        # 5. 移除所有活跃合约菜单 (per user request) - only popular + filters remain
        source = gr.Dropdown(["Tushare", "Mock"], value="Tushare", label="数据源")
        playbook = gr.Dropdown(["v3", "zen", "dow", "abu"], value="v3", label="Playbook风格")
        strategy = gr.Dropdown(["full", "core", "idonly"], value="full", label="Strategy策略 (Token优化)")

    btn = gr.Button("开始完整分析 (EA)", variant="primary")

    with gr.Row():
        console = gr.Markdown(
            label="📜 分析过程 (多轮路径+规则引用+决策依据, 富文本Blog风格)",
            value="**等待分析...** (选择合约后点击'开始完整分析')",
            height=680,
            show_label=True
        )
        with gr.Column(scale=1, min_width=400):  # K-line side ~50%, resizable via drag on middle line (Gradio Row + scale)
            with gr.Tabs():
                with gr.Tab("当前合约 K线"):
                    main_plot = gr.Plot()
                with gr.Tab("相关品种 K线 (每个品种独立Tab)"):
                    with gr.Tabs():
                        with gr.Tab("相关1"):
                            i_markdown = gr.Markdown("**相关品种1**")
                            i_plot = gr.Plot()
                        with gr.Tab("相关2"):
                            j_markdown = gr.Markdown("**相关品种2**")
                            j_plot = gr.Plot()

    # 合约过滤 + 搜索功能 (新, 不再依赖all_menu)
    def filter_contracts(exchange, search_term):
        """支持中文显示的过滤 (仅用于search提示, extract ts_code)"""
        contracts = get_main_contracts()
        if exchange != "全部":
            contracts = [c for c in contracts if c["ts_code"].endswith(exchange)]
        if search_term:
            search_term = search_term.upper()
            contracts = [c for c in contracts if search_term in c["ts_code"] or search_term in str(c.get("name", ""))]
        return [c["ts_code"] for c in contracts]

    # update_all_menu no longer needed for all_menu (removed); filter now self-contained

    # 2+5. 仅菜单change更新K线 (移除all_menu, analysis click不再重复更新K线避免白版; filter仅更新自身)
    exchange_filter.change(fn=lambda e, s: e, inputs=[exchange_filter, search_box], outputs=exchange_filter)
    search_box.change(fn=lambda e, s: None, inputs=[exchange_filter, search_box], outputs=main_plot)  # No K-line on search

    def update_kline(symbol):
        if isinstance(symbol, str) and ' ' in symbol:
            symbol = symbol.split()[-1]
        df = get_futures_daily_with_ma(symbol, months=3)
        chart = create_candlestick_chart(df, symbol)
        return chart

    popular_menu.change(
        fn=update_kline,
        inputs=[popular_menu],
        outputs=main_plot
    )
    # all_menu removed - K-line only updates on popular change

    # 3. Dynamic related (reuse from nodes/data_gathering.py - now core EA dynamic)
    from eaagent.a_plus_plus.nodes.data_gathering import get_related_for_symbol

    def extract_ts_code(display_value):
        """Robust parser for Chinese '品种 代码' or '代码 代码' (fix for SA2609 SA2609.ZCE)"""
        if not isinstance(display_value, str):
            return display_value
        # Handle 'SA2609 SA2609.ZCE' or '纯碱 SA2609.ZCE' - take last valid ts_code part
        parts = display_value.strip().split()
        for p in reversed(parts):
            if '.' in p or any(c.isdigit() for c in p):  # ts_code pattern
                return p
        return display_value  # fallback

    btn.click(
        fn=lambda sym, *args: run_analysis(extract_ts_code(sym), *args),
        inputs=[popular_menu, source, playbook, strategy],
        outputs=[console, main_plot, i_plot, j_plot]  # console Markdown (rich 50% report), plots
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
