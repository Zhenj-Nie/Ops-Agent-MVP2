from __future__ import annotations

from typing import Any, Dict, List

from app.adapters.feishu import FeishuNotifier
from app.agents.executor import ExecutorAgent
from app.agents.planner import PlannerAgent
from app.agents.reporter import ReporterAgent
from app.agents.verifier import VerifierAgent


class MultiAgentOrchestrator:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.verifier = VerifierAgent()
        self.reporter = ReporterAgent()
        self.notifier = FeishuNotifier()

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        steps: List[Dict[str, Any]] = []

        plan = self.planner.run(task)
        steps.append(self.planner.step(plan))

        execution = self.executor.run(task, plan)
        steps.append(self.executor.step(execution))

        verification = self.verifier.run(task, execution)
        steps.append(self.verifier.step(verification))

        report = self.reporter.run(task, plan, execution, verification)
        steps.append(self.reporter.step(report))

        notification_result = self.notifier.send_text(
            report["notification_text"],
            extra_payload={"task_id": task["id"], "task_type": task["task_type"]},
        )
        steps.append({"agent": "FeishuNotifier", "output": notification_result})

        return {
            "steps": steps,
            "report": report["report"],
            "notification_text": report["notification_text"],
            "metrics": {
                "alert_count": verification.get("alert_count", 0),
                "quote_count": len(execution.get("quotes", [])),
                "notifier_status": notification_result.get("status"),
            },
        }
