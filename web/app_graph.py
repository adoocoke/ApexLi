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

    # K线图部分（保持不变）
    df_main = pd.DataFrame(extra.get("technical_indicators", []))
    if df_main.empty:
        df_main = get_futures_daily_with_ma(symbol, months=3)
    main_chart = create_candlestick_chart(df_main, symbol)

    # 强制显示相关品种 (扩展为关注品种中文显示 per plan)
    df_i = get_futures_daily_with_ma("I2609.DCE", months=2)
    df_j = get_futures_daily_with_ma("J2609.DCE", months=2)
    i_chart = create_candlestick_chart(df_i, "I2609.DCE (铁矿石)")
    j_chart = create_candlestick_chart(df_j, "J2609.DCE (焦炭)")
    result_text = f"✅ 当前使用 Playbook: {name} | 方向: {signal.get('direction', '未返回方向')}\n关注品种菜单已启用中文显示 (螺纹钢 RB、铁矿石 I 等)"

    return result_text, main_chart, i_chart, j_chart

with gr.Blocks() as demo:
    gr.Markdown("# ApexLi • 期货主力合约菜单 + 动态 K线 (带过滤)")

    with gr.Row():
        # 合约过滤 (新功能)
        exchange_filter = gr.Dropdown(["全部", "SHF", "DCE", "CZCE"], value="全部", label="交易所过滤")
        search_box = gr.Textbox(placeholder="搜索合约 (如 RB 或 I)", label="合约搜索")
        popular_choices = get_popular_main_contracts()  # "中文 代码" format
        popular_menu = gr.Dropdown(
            choices=popular_choices,
            value=popular_choices[0].split()[-1] if popular_choices else "RB2610.SHF",  # Use ts_code as value to avoid Gradio warning
            label="关注主力合约 (中文显示)",
            interactive=True
        )
        main_choices = get_main_contracts()
        all_menu = gr.Dropdown(
            choices=[c.get("name", c["ts_code"]) for c in main_choices],  # Chinese name for display
            value=main_choices[0]["ts_code"] if main_choices else "I2609.DCE",
            label="所有活跃合约 (中文+代码)",
            interactive=True
        )
        source = gr.Dropdown(["Tushare", "Mock"], value="Tushare", label="数据源")
        playbook = gr.Dropdown(["v3", "zen", "dow", "abu"], value="v3", label="Playbook风格")
        strategy = gr.Dropdown(["full", "core", "idonly"], value="full", label="Strategy策略 (Token优化)")

    btn = gr.Button("开始完整分析 (EA)", variant="primary")

    with gr.Row():
        console = gr.Textbox(label="📜 分析过程", lines=10, scale=4)
        with gr.Column(scale=6):
            with gr.Tabs():
                with gr.Tab("当前合约 K线"):
                    main_plot = gr.Plot()
                with gr.Tab("相关品种 K线"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**铁矿石 I2609**")
                            i_plot = gr.Plot()
                        with gr.Column():
                            gr.Markdown("**焦炭 J2609**")
                            j_plot = gr.Plot()

    # 合约过滤 + 搜索功能 (新)
    def filter_contracts(exchange, search_term):
        """支持中文显示的过滤 (extract ts_code from '中文 代码' string)"""
        contracts = get_main_contracts()
        if exchange != "全部":
            contracts = [c for c in contracts if c["ts_code"].endswith(exchange)]
        if search_term:
            search_term = search_term.upper()
            contracts = [c for c in contracts if search_term in c["ts_code"] or search_term in c.get("name", "")]
        # Return ts_code for value, but UI shows full Chinese name via all_menu choices
        return [c["ts_code"] for c in contracts]

    def update_all_menu(exchange, search_term):
        choices_ts = filter_contracts(exchange, search_term)
        # Rebuild full Chinese choices using popular map for display
        popular_map = {item.split()[-1]: item for item in get_popular_main_contracts()}
        full_choices = [popular_map.get(ts, f"{ts.split('.')[0]} {ts}") for ts in choices_ts or ["RB2610.SHF"]]
        default_value = full_choices[0] if full_choices else "螺纹钢 RB2610.SHF"
        return gr.Dropdown(choices=full_choices, value=default_value)

    exchange_filter.change(fn=update_all_menu, inputs=[exchange_filter, search_box], outputs=all_menu)
    search_box.change(fn=update_all_menu, inputs=[exchange_filter, search_box], outputs=all_menu)

    # 菜单变更立即更新主 K线 (支持中文显示的symbol解析)
    def update_kline(symbol):
        # Extract ts_code if Chinese format passed ('螺纹钢 RB2610.SHF' → 'RB2610.SHF')
        if isinstance(symbol, str) and ' ' in symbol:
            symbol = symbol.split()[-1]
        df = get_futures_daily_with_ma(symbol, months=3)
        chart = create_candlestick_chart(df, symbol)
        return chart

    popular_menu.change(fn=update_kline, inputs=popular_menu, outputs=main_plot)
    all_menu.change(fn=update_kline, inputs=all_menu, outputs=main_plot)

    def extract_ts_code(display_value):
        """Helper to extract ts_code from Chinese '品种 代码' for run_analysis"""
        if isinstance(display_value, str) and ' ' in display_value:
            return display_value.split()[-1]
        return display_value

    btn.click(
        fn=lambda sym, *args: run_analysis(extract_ts_code(sym), *args),  # Parse Chinese before analysis
        inputs=[popular_menu, source, playbook, strategy],
        outputs=[console, main_plot, i_plot, j_plot]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
