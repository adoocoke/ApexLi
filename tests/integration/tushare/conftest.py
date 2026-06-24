import os
import pytest
import tushare as ts


@pytest.fixture(scope="session")
def tushare_pro():
    """Tushare Pro API 客户端"""
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        pytest.fail("环境变量 TUSHARE_TOKEN 未设置，无法运行 Tushare 期货接口测试")

    ts.set_token(token)
    return ts.pro_api()
