from __future__ import annotations

import json
import threading
import time
import uuid
from typing import Any, Dict, Optional

from app.config import settings
from app.db import get_conn, now_iso, row_to_dict
from app.orchestrator import MultiAgentOrchestrator


class TaskQueue:
    def enqueue(self, task_id: int) -> int:
        with get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO task_queue(task_id, status, created_at, updated_at)
                VALUES (?, 'queued', ?, ?)
                """,
                (task_id, now_iso(), now_iso()),
            )
            return int(cur.lastrowid)

    def fetch_next(self) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM task_queue
                WHERE status = 'queued'
                ORDER BY id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            run_id = str(uuid.uuid4())
            conn.execute(
                """
                UPDATE task_queue
                SET status = 'running', run_id = ?, updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (run_id, now_iso(), row["id"]),
            )
            item = row_to_dict(row)
            item["run_id"] = run_id
            return item

    def mark_done(self, queue_id: int) -> None:
        with get_conn() as conn:
            conn.execute(
                "UPDATE task_queue SET status = 'done', updated_at = ? WHERE id = ?",
                (now_iso(), queue_id),
            )

    def mark_failed(self, queue_id: int) -> None:
        with get_conn() as conn:
            conn.execute(
                "UPDATE task_queue SET status = 'failed', updated_at = ? WHERE id = ?",
                (now_iso(), queue_id),
            )


class Worker:
    def __init__(self) -> None:
        self.queue = TaskQueue()
        self.orchestrator = MultiAgentOrchestrator()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ops-agent-worker")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _loop(self) -> None:
        while not self._stop.is_set():
            item = self.queue.fetch_next()
            if item is None:
                time.sleep(settings.worker_poll_interval_seconds)
                continue
            self._process(item)

    def _process(self, queue_item: Dict[str, Any]) -> None:
        queue_id = int(queue_item["id"])
        task_id = int(queue_item["task_id"])
        run_id = queue_item["run_id"]
        started = now_iso()

        with get_conn() as conn:
            task_row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if task_row is None:
                self.queue.mark_failed(queue_id)
                return
            task = row_to_dict(task_row)
            task["config"] = json.loads(task.get("config_json") or "{}")
            conn.execute(
                """
                INSERT INTO task_runs(run_id, task_id, status, started_at)
                VALUES (?, ?, 'running', ?)
                """,
                (run_id, task_id, started),
            )

        try:
            result = self.orchestrator.run(task)
            with get_conn() as conn:
                conn.execute(
                    """
                    UPDATE task_runs
                    SET status = 'success', finished_at = ?, result_json = ?
                    WHERE run_id = ?
                    """,
                    (now_iso(), json.dumps(result, ensure_ascii=False), run_id),
                )
            self.queue.mark_done(queue_id)
        except Exception as exc:
            with get_conn() as conn:
                conn.execute(
                    """
                    UPDATE task_runs
                    SET status = 'failed', finished_at = ?, error = ?
                    WHERE run_id = ?
                    """,
                    (now_iso(), repr(exc), run_id),
                )
            self.queue.mark_failed(queue_id)
