"""
Tushare 连接测试
支持在未安装 tushare 或未配置 token 时自动跳过
真实 API 调用测试默认跳过，避免触发频率限制
"""

import os
import pytest

tushare = pytest.importorskip("tushare", reason="tushare 未安装，跳过 Tushare 相关测试")


def test_tushare_token_exists():
    """ 测试 TUSHARE_TOKEN 环境变量是否存在（快速测试） """
    token = os.getenv("TUSHARE_TOKEN")
    if token is None:
        pytest.skip("未设置 TUSHARE_TOKEN，跳过 token 检查测试")
    assert len(token) > 10, "TUSHARE_TOKEN 看起来太短，请检查是否正确"


def test_tushare_connection():
    """ 真实调用 Tushare API 测试（需要手动取消 skip 才能运行） """
    token = os.getenv("TUSHARE_TOKEN")
    tushare.set_token(token)
    pro = tushare.pro_api()

    try:
        df = pro.fut_daily(
            ts_code="RB2405.SHF",
            start_date="20240301",
            end_date="20240305",
            fields="ts_code,trade_date,close"
        )

        assert not df.empty
        assert "close" in df.columns

        print(f"\n✅ Tushare 连接成功！成功获取 {len(df)} 条数据")

    except Exception as e:
        pytest.fail(f"Tushare API 调用失败: {str(e)}")
