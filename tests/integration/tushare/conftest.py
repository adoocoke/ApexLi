import os
import pytest
import tushare as ts
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()


@pytest.fixture(scope="session")
def tushare_pro():
    """Tushare Pro API 客户端"""
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        pytest.skip("环境变量 TUSHARE_TOKEN 未设置，跳过 Tushare 期货接口测试")

    ts.set_token(token)
    return ts.pro_api()
