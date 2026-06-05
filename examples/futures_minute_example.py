"""
期货分钟线 + ReAct Agent 示例
演示如何让 Agent 使用 Tushare 分钟线工具进行分析
"""

from eaagent import ReActAgent
from eaagent.tools.tushare_minute import get_futures_minute


def main():
    print("=== 期货分钟线 ReAct Agent 示例 ===\n")

    agent = ReActAgent(
        verbose=True,
        require_api_key=False,   # 测试模式
        auto_memory=True         # 开启自动记忆提取
    )

    # 注册分钟线工具
    agent.add_tool(
        name="get_futures_minute",
        description="获取期货合约的分钟线数据（支持 1min, 5min, 15min, 30min, 60min）",
        parameters={
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "期货合约代码，例如 RB2405.SHF、I2409.DCE"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始时间，格式 YYYYMMDDHHMMSS"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束时间，格式 YYYYMMDDHHMMSS（可选）"
                },
                "freq": {
                    "type": "string",
                    "description": "频率，支持 1min, 5min, 15min, 30min, 60min"
                }
            },
            "required": ["ts_code", "start_date"]
        },
        function=get_futures_minute,
    )

    # 示例问题
    question = "帮我看看螺纹钢 RB2405.SHF 今天上午 9:00 到 10:00 的 5 分钟线情况，有没有明显趋势？"

    print(f"\n问题: {question}\n")
    print("=" * 60)

    answer = agent.run(question)

    print("\n" + "=" * 60)
    print(f"\n最终回复:\n{answer}")


if __name__ == "__main__":
    main()
