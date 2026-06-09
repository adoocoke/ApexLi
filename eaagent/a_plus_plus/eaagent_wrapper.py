from ..agent import ReActAgent


class APlusPlusReActAgent(ReActAgent):
    """
    扩展的 ReAct Agent，集成了交易相关的工具和 Playbook
    """

    def __init__(self, model_name: str = "grok-4.3", **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name

        # 延迟导入，避免强制依赖 mplfinance
        from .visualization import generate_kline_chart

        # 注册可视化工具
        self.add_tool(
            name="generate_kline_chart",
            description=generate_kline_chart.__doc__ or "生成K线图并标注支撑压力位",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "期货合约代码，例如 RB2605、I2609"
                    },
                    "period": {
                        "type": "string",
                        "description": "K线周期，D 表示日线，30 表示30分钟",
                        "default": "D"
                    }
                },
                "required": ["symbol"]
            },
            function=generate_kline_chart
        )

    def load_playbook(self):
        """加载交易 Playbook（由子类或外部调用）"""
        pass
