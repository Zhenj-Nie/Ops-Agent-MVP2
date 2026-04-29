from __future__ import annotations

from typing import Any, Dict, List

from app.adapters.market_data import MarketDataAdapterFactory
from app.agents.base import AgentBase


class ExecutorAgent(AgentBase):
    name = "ExecutorAgent"

    def run(self, task: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task["task_type"]
        config = task.get("config", {})

        if task_type == "stock_monitor":
            provider = config.get("provider", "mock")
            symbols = config.get("symbols", plan.get("symbols", []))
            adapter = MarketDataAdapterFactory.create(provider)
            quotes = adapter.get_quotes(symbols)
            return {
                "source": provider,
                "quotes": [q.__dict__ for q in quotes],
                "raw_count": len(quotes),
            }

        return {
            "source": "placeholder",
            "message": "未实现的 task_type，已返回占位执行结果。",
            "config": config,
        }
