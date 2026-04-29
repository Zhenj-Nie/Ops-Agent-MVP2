from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import AgentBase
from app.adapters.llm import OptionalLLMClient


class ReporterAgent(AgentBase):
    name = "ReporterAgent"

    def __init__(self) -> None:
        self.llm = OptionalLLMClient()

    def run(self, task: Dict[str, Any], plan: Dict[str, Any], execution: Dict[str, Any], verification: Dict[str, Any]) -> Dict[str, Any]:
        quotes = execution.get("quotes", [])
        alerts = verification.get("alerts", [])
        task_name = task.get("name", "未命名任务")

        lines = [
            f"# 运营自动化运行报告：{task_name}",
            "",
            "## 1. 任务目标",
            plan.get("goal", "执行自动化任务"),
            "",
            "## 2. 数据概览",
        ]

        if quotes:
            lines.append("| 标的 | 当前值 | 涨跌幅 | 成交量 | 数据源 |")
            lines.append("|---|---:|---:|---:|---|")
            for q in quotes:
                lines.append(f"| {q['symbol']} | {q['price']} | {q['change_pct']}% | {q['volume']} | {q.get('source', '')} |")
        else:
            lines.append("暂无数据。")

        lines.extend(["", "## 3. 异常判断"])
        if alerts:
            for item in alerts:
                lines.append(f"- [{item['severity']}] {item['symbol']}：{item['reason']}")
        else:
            lines.append("- 暂未触发异常阈值。")

        lines.extend([
            "",
            "## 4. 建议动作",
        ])
        if alerts:
            lines.extend([
                "- 优先确认数据源是否正常，排除接口延迟或异常值。",
                "- 对触发阈值的标的进行二次核查，必要时推送到业务群。",
                "- 如果该指标影响广告投放、库存、销售线索或风控策略，可接入自动化 API 执行后续动作。",
            ])
        else:
            lines.append("- 保持当前监控频率，无需人工介入。")

        report = "\n".join(lines)

        notification_text = f"【{task_name}】运行完成：发现 {len(alerts)} 个异常。"
        if alerts:
            top = alerts[0]
            notification_text += f" 首个异常：{top['symbol']}，{top['reason']}。"

        # 可选：如果配置了 LLM，则让 LLM 优化通知文案，但不影响 MVP 运行
        llm_text = self.llm.chat([
            {"role": "system", "content": "你是运营自动化助手，请把报告压缩为适合飞书群的简短通知。"},
            {"role": "user", "content": report[:4000]},
        ])
        if llm_text:
            notification_text = llm_text.strip()

        return {
            "report": report,
            "notification_text": notification_text,
            "summary": {
                "quote_count": len(quotes),
                "alert_count": len(alerts),
            },
        }
