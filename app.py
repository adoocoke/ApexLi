"""
eaagent Web 界面（使用 Gradio）
支持 Memory + 自动记忆 + Tushare 工具
"""

import gradio as gr
from eaagent import ReActAgent
from eaagent.tools.tushare_minute import get_futures_minute
from eaagent.tools.tushare_futures import get_futures_daily


def create_agent():
    """创建并配置 Agent"""
    agent = ReActAgent(
        verbose=False,           # Web 界面建议关闭详细日志
        require_api_key=True,    # 生产环境需要 Key
        auto_memory=True         # 开启自动记忆
    )

    # 注册日线工具
    agent.add_tool(
        name="get_futures_daily",
        description="获取期货日线数据",
        parameters={
            "type": "object",
            "properties": {
                "ts_code": {"type": "string", "description": "合约代码，如 RB2405.SHF"},
                "start_date": {"type": "string", "description": "开始日期 YYYYMMDD"}
            },
            "required": ["ts_code", "start_date"]
        },
        function=get_futures_daily,
    )

    # 注册分钟线工具
    agent.add_tool(
        name="get_futures_minute",
        description="获取期货分钟线数据",
        parameters={
            "type": "object",
            "properties": {
                "ts_code": {"type": "string"},
                "start_date": {"type": "string"},
                "freq": {"type": "string", "description": "1min, 5min, 15min 等"}
            },
            "required": ["ts_code", "start_date"]
        },
        function=get_futures_minute,
    )

    return agent


# 全局 Agent（生产环境建议做成单例或会话隔离）
agent = create_agent()


def chat_with_agent(message, history):
    """Gradio 聊天回调函数"""
    try:
        response = agent.run(message)
        return response
    except Exception as e:
        return f"出错了: {str(e)}"


# 创建 Gradio 界面
demo = gr.ChatInterface(
    fn=chat_with_agent,
    title="eaagent - 期货分析助手",
    description="基于 Grok + ReAct + Memory 的期货分析 Agent",
    examples=[
        "帮我分析一下螺纹钢 RB2405.SHF 最近的走势",
        "铁矿石 I2409 今天上午的 5 分钟线怎么样？",
        "目前市场对纯碱 SA 的情绪如何？"
    ]
)

if __name__ == "__main__":
    import os
    
    # 关键：让 localhost 不走代理
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    
    demo.launch(
        server_name="127.0.0.1",   # 只监听本地回环地址
        server_port=7860,
        share=False                # 先关闭 share
    )
