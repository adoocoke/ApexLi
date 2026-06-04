"""
示例工具：天气查询
实际项目中请替换为真实 API（如和风天气、高德地图等）
"""

def get_weather(city: str) -> str:
    """
    查询城市天气（模拟实现）

    Args:
        city: 城市名称（支持中文或英文）

    Returns:
        天气信息字符串
    """
    # TODO: 替换为真实天气 API
    mock_data = {
        "北京": "晴朗，25°C，空气质量优，西北风2级",
        "上海": "多云，28°C，湿度65%",
        "深圳": "阵雨，30°C，有雷暴风险",
    }

    info = mock_data.get(city, f"{city} 当前天气晴朗，温度约24°C（模拟数据）")
    return f"【{city}天气】{info}"