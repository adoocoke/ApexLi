  from abc import ABC, abstractmethod
  import pandas as pd
  from typing import Optional, Dict, Any


  class DataProvider(ABC):
      """数据提供者抽象基类

          所有具体数据源（期货、股票等）都需要实现此接口。
              目的是统一不同数据源的访问方式，便于 Harness 切换和扩展。
                  """

      @abstractmethod
      def get_daily(
                  self, 
                          symbol: str, 
                                  start_date: str, 
                                          end_date: str
                                              ) -> pd.DataFrame:
          """获取日线数据
                  
                          Args:
                                      symbol: 标的代码（如 RB2605、000001.SZ）
                                                  start_date: 开始日期，格式 YYYYMMDD
                                                              end_date: 结束日期，格式 YYYYMMDD
                                                                          
                                                                                  Returns:
                                                                                              标准化后的 DataFrame，包含 trade_date, open, high, low, close, vol 等字段
                                                                                                      """
          pass

      @abstractmethod
      def get_minute(
                  self, 
                          symbol: str, 
                                  start_date: str, 
                                          end_date: str, 
                                                  freq: str = "5min"
                                                      ) -> pd.DataFrame:
          """获取分钟线数据"""
          pass

      @abstractmethod
      def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
          """获取标的物基本信息"""
          pass

      def get_name(self) -> str:
          """返回数据提供者名称，便于日志和调试"""
          return self.__class__.__name__
