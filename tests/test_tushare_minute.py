"""
Tushare 分钟线工具测试
"""

import pytest
from eaagent.tools.tushare_minute import get_futures_minute


def test_get_futures_minute_basic():
    """基础功能测试（需要 TUSHARE_TOKEN）"""
    # 这里只做 smoke test，实际调用需要 token
    # 在 CI 中如果没有 token 会跳过
    try:
        result = get_futures_minute(
            ts_code="RB2405.SHF",
            start_date="20240305090000",
            end_date="20240305100000",
            freq="5min"
        )
        assert isinstance(result, str)
        assert "RB2405.SHF" in result or "未查询到" in result or "失败" in result
    except Exception as e:
        if "TUSHARE_TOKEN" in str(e):
            pytest.skip("没有 TUSHARE_TOKEN，跳过真实调用测试")
        else:
            raise
