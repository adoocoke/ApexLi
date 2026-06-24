from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time


@dataclass
class LLMCallRecord:
    """单次 LLM 调用的记录"""
    round: int
    node: str                    # 例如：signal_generation, llm_critique
    prompt: str
    response: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    timestamp: float = field(default_factory=time.time)


class LLMTracker:
    """LLM 调用记录与统计管理器"""

    # grok-3 价格（USD per 1M tokens）
    PROMPT_PRICE_PER_M = 5.0
    COMPLETION_PRICE_PER_M = 15.0

    def __init__(self):
        self.records: List[LLMCallRecord] = []
        self.current_round: int = 0

    def start_new_round(self):
        """开始新一轮分析"""
        self.current_round += 1

    def record_call(
        self,
        node: str,
        prompt: str,
        response: str,
        usage: Optional[Dict] = None
    ):
        """
        记录一次 LLM 调用
        usage 示例: {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200}
        """
        if usage is None:
            usage = {}

        record = LLMCallRecord(
            round=self.current_round,
            node=node,
            prompt=prompt,
            response=response,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        self.records.append(record)

    def get_records_by_round(self, round_num: int) -> List[LLMCallRecord]:
        """获取指定轮次的所有记录"""
        return [r for r in self.records if r.round == round_num]

    def get_total_usage(self) -> Dict:
        """
        统计总的 Token 使用量和预估费用
        """
        total_prompt = sum(r.prompt_tokens for r in self.records)
        total_completion = sum(r.completion_tokens for r in self.records)
        total_tokens = sum(r.total_tokens for r in self.records)

        # 费用计算（USD）
        cost = (total_prompt / 1_000_000 * self.PROMPT_PRICE_PER_M +
                total_completion / 1_000_000 * self.COMPLETION_PRICE_PER_M)

        return {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(cost, 6),
        }

    def reset(self):
        """重置所有记录"""
        self.records.clear()
        self.current_round = 0
