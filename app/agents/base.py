from __future__ import annotations

from typing import Any, Dict


class AgentBase:
    name = "AgentBase"

    def step(self, output: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.name, "output": output}
