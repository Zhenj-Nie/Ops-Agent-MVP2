from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import AgentBase


class PlannerAgent(AgentBase):
    name = "PlannerAgent"

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task["task_type"]
        config = task.get("config", {})

        if task_type == "stock_monitor":
            symbols = config.get("symbols", ["AAPL", "MSFT"])
            thresholds = config.get("thresholds", {})
            return {
                "goal": "监控指定股票或业务指标，识别显著波动并输出行动建议。",
                "task_type": task_type,
                "symbols": symbols,
                "thresholds": thresholds,
                "steps": [
                    "读取监控标的和阈值配置",
                    "调用 MarketDataAdapter 获取指标数据",
                    "判断涨跌幅、成交量、数据完整性是否异常",
                    "生成运营摘要和通知文案",
                ],
                "long_chain_reasoning": True,
                "multi_agent": ["Planner", "Executor", "Verifier", "Reporter"],
            }

        return {
            "goal": "执行通用运营自动化任务",
            "task_type": task_type,
            "steps": ["读取配置", "执行外部 API", "校验结果", "生成报告"],
            "long_chain_reasoning": True,
            "multi_agent": ["Planner", "Executor", "Verifier", "Reporter"],
        }
