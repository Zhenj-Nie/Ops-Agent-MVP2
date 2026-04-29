from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.feishu import FeishuNotifier
from app.db import get_conn, init_db, now_iso, row_to_dict, rows_to_dicts
from app.queue import TaskQueue, Worker
from app.schemas import EnqueueResult, NotificationTest, TaskCreate

worker = Worker()
queue = TaskQueue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    worker.start()
    yield
    worker.stop()


app = FastAPI(title="Ops Agent MVP", version="0.1.0", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "time": now_iso()}


@app.post("/api/tasks")
def create_task(payload: TaskCreate) -> Dict[str, Any]:
    ts = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks(name, task_type, config_json, enabled, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (payload.name, payload.task_type, json.dumps(payload.config, ensure_ascii=False), ts, ts),
        )
        task_id = int(cur.lastrowid)

    queue_id = None
    if payload.enqueue_now:
        queue_id = queue.enqueue(task_id)

    return {"task_id": task_id, "queue_id": queue_id, "status": "created"}


@app.get("/api/tasks")
def list_tasks() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    tasks = []
    for item in rows_to_dicts(rows):
        item["config"] = json.loads(item.get("config_json") or "{}")
        tasks.append(item)
    return tasks


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    item = row_to_dict(row)
    if not item:
        raise HTTPException(status_code=404, detail="task not found")
    item["config"] = json.loads(item.get("config_json") or "{}")
    return item


@app.post("/api/tasks/{task_id}/enqueue")
def enqueue_task(task_id: int) -> EnqueueResult:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="task not found")
    queue_id = queue.enqueue(task_id)
    return EnqueueResult(queue_id=queue_id, task_id=task_id, status="queued")


@app.get("/api/runs")
def list_runs(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT r.*, t.name AS task_name, t.task_type AS task_type
            FROM task_runs r
            JOIN tasks t ON t.id = r.task_id
            ORDER BY r.started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    data = []
    for item in rows_to_dicts(rows):
        if item.get("result_json"):
            try:
                item["result"] = json.loads(item["result_json"])
            except Exception:
                item["result"] = None
        data.append(item)
    return data


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT r.*, t.name AS task_name, t.task_type AS task_type
            FROM task_runs r
            JOIN tasks t ON t.id = r.task_id
            WHERE r.run_id = ?
            """,
            (run_id,),
        ).fetchone()
    item = row_to_dict(row)
    if not item:
        raise HTTPException(status_code=404, detail="run not found")
    if item.get("result_json"):
        item["result"] = json.loads(item["result_json"])
    return item


@app.post("/api/demo/stock-monitor")
def create_demo_stock_monitor() -> Dict[str, Any]:
    payload = TaskCreate(
        name="股票/运营指标监控 Demo",
        task_type="stock_monitor",
        config={
            "provider": "mock",
            "symbols": ["AAPL", "MSFT", "NVDA", "TSLA", "BABA"],
            "thresholds": {
                "abs_change_pct": 3.0,
                "TSLA": 2.0,
                "NVDA": 2.5,
            },
        },
        enqueue_now=True,
    )
    return create_task(payload)


@app.post("/api/notifications/test")
def test_notification(payload: NotificationTest) -> Dict[str, Any]:
    return FeishuNotifier().send_text(payload.text, extra_payload={"source": "manual_test"})


@app.get("/api/notifications")
def list_notifications(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM notifications ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)
