from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import AgentBase


class VerifierAgent(AgentBase):
    name = "VerifierAgent"

    def run(self, task: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
        config = task.get("config", {})
        thresholds = config.get("thresholds", {})
        default_abs_change_pct = float(thresholds.get("abs_change_pct", 3.0))
        alerts: List[Dict[str, Any]] = []
        warnings: List[str] = []

        quotes = execution.get("quotes", [])
        if not quotes:
            warnings.append("没有获取到任何数据，请检查数据源或 symbols 配置。")

        for q in quotes:
            symbol = q["symbol"]
            change_pct = float(q["change_pct"])
            symbol_threshold = float(thresholds.get(symbol, default_abs_change_pct))
            if abs(change_pct) >= symbol_threshold:
                alerts.append(
                    {
                        "symbol": symbol,
                        "reason": f"涨跌幅 {change_pct}% 超过阈值 ±{symbol_threshold}%",
                        "severity": "high" if abs(change_pct) >= symbol_threshold * 1.5 else "medium",
                        "quote": q,
                    }
                )

        return {
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
            "alerts": alerts,
            "alert_count": len(alerts),
            "checked_rules": ["数据非空", "涨跌幅阈值", "单标的自定义阈值"],
        }
