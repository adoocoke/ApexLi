"""
eaagent - Easy ReAct Agent powered by Grok (xAI)
"""

# Lazy import to avoid pulling in heavy OpenAI/pydantic dependencies on top-level import
# (prevents ModuleNotFoundError for pydantic_core/jiter in conda/streamlit envs)
def __getattr__(name):
    if name == "ReActAgent":
        from .agent import ReActAgent
        return ReActAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__version__ = "0.1.0"
__all__ = ["ReActAgent"]