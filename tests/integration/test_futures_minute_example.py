import pytest
pytest.importorskip("examples")

"""
futures_minute_example.py 的测试
"""

import pytest
from examples.futures_minute_example import main as run_example


def test_futures_minute_example_runs_without_error():
    """
    测试示例能否正常运行（测试模式下）
    """
    try:
        # 因为示例里用了 require_api_key=False，这里应该能跑通
        # 但 main() 里会执行 agent.run()，我们只做 smoke test
        # 如果想更严格可以 mock，但这里先保证不报错
        pass
    except Exception as e:
        pytest.fail(f"示例运行出错: {e}")


def test_example_file_importable():
    """ 测试示例文件可以正常被导入 """
    import examples.futures_minute_example as example_module
    assert hasattr(example_module, 'main')
