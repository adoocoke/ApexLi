# Lazy to avoid pulling tushare deps (lxml) on top level import in streamlit
def __getattr__(name):
    if name == "get_futures_daily_recent":
        from .tushare_futures import get_futures_daily_recent
        return get_futures_daily_recent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["get_futures_daily_recent"]
