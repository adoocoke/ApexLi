"""
Tushare 连接测试
用于验证 TUSHARE_TOKEN 是否配置正确，以及能否正常调用 Tushare API
"""

import os
import pytest

import tushare as ts


def test_tushare_token_exists():
    """测试 TUSHARE_TOKEN 环境变量是否存在"""
    token = os.getenv("TUSHARE_TOKEN")
    assert token is not None, (
        "环境变量 TUSHARE_TOKEN 未设置！\n"
        "请先去 https://tushare.pro 注册获取 token，"
        "然后执行：export TUSHARE_TOKEN=你的token"
    )
    assert len(token) > 10, "TUSHARE_TOKEN 看起来太短，请检查是否正确"


@pytest.mark.skipif(
    os.getenv("TUSHARE_TOKEN") is None,
    reason="未设置 TUSHARE_TOKEN，跳过真实 API 调用测试"
)
def test_tushare_connection():
    """测试能否成功连接 Tushare 并获取数据"""
    token = os.getenv("TUSHARE_TOKEN")
    ts.set_token(token)
    pro = ts.pro_api()

    try:
        # 尝试获取一条简单的期货数据（螺纹钢）
        df = pro.fut_daily(
            ts_code="RB2405.SHF",
            start_date="20240301",
            end_date="20240305",
            fields="ts_code,trade_date,close"
        )

        assert not df.empty, "查询结果为空，可能是 token 无效或没有权限"
        assert "close" in df.columns, "返回数据格式异常"

        print(f"\n✅ Tushare 连接成功！成功获取 {len(df)} 条数据")
        print(df.head())

    except Exception as e:
        pytest.fail(f"Tushare API 调用失败: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])