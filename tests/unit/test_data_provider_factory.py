import pytest
from unittest.mock import patch, MagicMock

from eaagent.data_providers.factory import get_data_provider
from eaagent.data_providers.tushare_futures import TushareFuturesProvider


class TestDataProviderFactory:

    @patch("eaagent.data_providers.factory.TushareFuturesProvider")
    def test_get_data_provider_default(self, mock_provider_class):
        """测试默认返回 TushareFuturesProvider"""
        mock_instance = MagicMock()
        mock_provider_class.return_value = mock_instance
        provider = get_data_provider()
        assert provider == mock_instance

    @patch("eaagent.data_providers.factory.TushareFuturesProvider")
    def test_get_data_provider_explicit_futures(self, mock_provider_class):
        """测试显式指定 tushare_futures"""
        mock_instance = MagicMock()
        mock_provider_class.return_value = mock_instance
        provider = get_data_provider("tushare_futures")
        assert provider == mock_instance

    def test_get_data_provider_unknown_raises_error(self):
        """测试传入不支持的 provider 时抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_data_provider("unknown_provider")

        assert "Unknown data provider" in str(exc_info.value)

    @patch("eaagent.data_providers.factory.TushareFuturesProvider")
    def test_get_data_provider_passes_kwargs(self, mock_provider_class):
        """测试 factory 能正确把参数传给具体 Provider"""
        mock_instance = MagicMock()
        mock_provider_class.return_value = mock_instance

        provider = get_data_provider("tushare_futures", token="fake_token_123")

        # 验证 TushareFuturesProvider 被调用时传入了 token
        mock_provider_class.assert_called_once_with(token="fake_token_123")
        assert provider == mock_instance
