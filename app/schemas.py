from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    name: str
    task_type: str = Field(default="stock_monitor")
    config: Dict[str, Any] = Field(default_factory=dict)
    enqueue_now: bool = True


class TaskOut(BaseModel):
    id: int
    name: str
    task_type: str
    config: Dict[str, Any]
    enabled: int
    created_at: str
    updated_at: str


class EnqueueResult(BaseModel):
    queue_id: int
    task_id: int
    status: str


class NotificationTest(BaseModel):
    text: str = "这是一条飞书通知占位测试"


class AgentStep(BaseModel):
    agent: str
    output: Dict[str, Any]


class RunResult(BaseModel):
    run_id: str
    task_id: int
    status: str
    steps: List[AgentStep] = Field(default_factory=list)
    report: str = ""
    notification_text: str = ""
    metrics: Dict[str, Any] = Field(default_factory=dict)
