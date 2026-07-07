from ..agent import ReActAgent


class APlusPlusReActAgent(ReActAgent):
    """
    扩展的 ReAct Agent，集成了交易相关的工具和 Playbook
    """

    def __init__(self, model_name: str = "grok-4.3", **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name

        # 延迟导入，避免循环依赖
        from .visualization import generate_kline_chart
        from .tools import get_futures_holding, get_futures_basic, get_related_futures_dynamic, get_futures_news, visual_analyzer

        # 注册交易工具 (LLM可调用, Tushare 15000积分全覆盖, doc_id=290 fut_holding)
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

        self.add_tool(
            name="get_futures_holding",
            description="获取期货持仓排名 (Tushare fut_holding, doc_id=290). 用于分析主力持仓变化。ts_code如 SA2609.ZCE",
            parameters={
                "type": "object",
                "properties": {
                    "ts_code": {"type": "string", "description": "合约代码 (必须)"},
                    "trade_date": {"type": "string", "description": "交易日期 (可选, 默认最近)"}
                },
                "required": ["ts_code"]
            },
            function=get_futures_holding
        )

        self.add_tool(
            name="get_futures_basic",
            description="获取期货合约基本信息和主力列表 (fut_basic). 用于发现当前活跃合约。",
            parameters={
                "type": "object",
                "properties": {
                    "exchange": {"type": "string", "description": "交易所 (CZCE/DCE/SHF, 可空)"}
                }
            },
            function=get_futures_basic
        )

        self.add_tool(
            name="get_related_futures_dynamic",
            description="动态获取当前symbol的相关期货数据 (基于RELATED_MAP + 最新主力). 分析时强烈推荐调用。",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "主合约代码 (e.g. SA2609.ZCE)"}
                },
                "required": ["symbol"]
            },
            function=get_related_futures_dynamic
        )

        self.add_tool(
            name="get_futures_news",
            description="获取与期货相关的5条重要新闻/宏观事件 (Tushare news + 产业/政策). 返回title/date/summary/impact。用于判断外部驱动因素。",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "关联合约 (可选)"},
                    "limit": {"type": "integer", "description": "返回条数，默认5", "default": 5}
                }
            },
            function=get_futures_news
        )

        self.add_tool(
            name="visual_analyzer",
            description="Grok视觉K线分析工具。输入symbol，返回基于图像+**当前Playbook**的全历史高置信买卖点signals列表 (direction, trend_signal, reason引用规则+视觉模式, confidence)。优于纯文本分析，尤其趋势开启/结束判断。12个月**纯K线+量柱+关键位** (无MA13/任何均线, 严格只用当前playbook_name章节, 禁止v3/zen混用)。",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "期货合约代码 (e.g. RB2610.SHF)"},
                    "months": {"type": "integer", "description": "历史月份，默认12", "default": 12},
                    "playbook_name": {"type": "string", "description": "当前Playbook版本 (v3/zen/dow/abu)", "default": "v3"}
                },
                "required": ["symbol"]
            },
            function=visual_analyzer
        )

        print(f"[Agent] 已注册 {len(self.tools)} 个期货工具 (news + holding + basic + related + visual_analyzer for Grok vision, 15000积分覆盖, NEED_TOOL if missing)")

    def load_playbook(self):
        """加载交易 Playbook（由子类或外部调用）"""
        pass
