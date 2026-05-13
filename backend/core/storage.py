"""Persistence layer for Historai simulations.

Provides an in-memory implementation for local development and a Supabase-backed
implementation for deployments. The router talks to the ``Storage`` protocol;
the concrete implementation is chosen at startup based on env vars.
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)

SimulationRecord = dict[str, Any]


class Storage(Protocol):
    def create(self, *, question: str, turns: int, actors: list[dict]) -> str: ...

    def get(self, simulation_id: str) -> Optional[SimulationRecord]: ...

    def update_actors(self, simulation_id: str, actors: list[dict], turns: int) -> None: ...

    def set_status(self, simulation_id: str, status: str, *, error: Optional[str] = None) -> None: ...

    def set_result_and_report(
        self, simulation_id: str, *, result: dict, report: dict
    ) -> None: ...

    def list_recent(self, *, limit: int = 50) -> list[SimulationRecord]: ...


class InMemoryStorage:
    def __init__(self) -> None:
        self._data: dict[str, SimulationRecord] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create(self, *, question: str, turns: int, actors: list[dict]) -> str:
        simulation_id = str(uuid.uuid4())
        now = self._now()
        record: SimulationRecord = {
            "id": simulation_id,
            "question": question,
            "status": "pending",
            "turns": turns,
            "actors": actors,
            "result": None,
            "report": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            self._data[simulation_id] = record
        return simulation_id

    def get(self, simulation_id: str) -> Optional[SimulationRecord]:
        with self._lock:
            record = self._data.get(simulation_id)
            return dict(record) if record else None

    def update_actors(self, simulation_id: str, actors: list[dict], turns: int) -> None:
        with self._lock:
            record = self._data.get(simulation_id)
            if record is None:
                return
            record["actors"] = actors
            record["turns"] = turns
            record["updated_at"] = self._now()

    def set_status(self, simulation_id: str, status: str, *, error: Optional[str] = None) -> None:
        with self._lock:
            record = self._data.get(simulation_id)
            if record is None:
                return
            record["status"] = status
            if error is not None:
                record["error"] = error
            record["updated_at"] = self._now()

    def set_result_and_report(
        self, simulation_id: str, *, result: dict, report: dict
    ) -> None:
        with self._lock:
            record = self._data.get(simulation_id)
            if record is None:
                return
            record["result"] = result
            record["report"] = report
            record["status"] = "done"
            record["updated_at"] = self._now()

    def list_recent(self, *, limit: int = 50) -> list[SimulationRecord]:
        with self._lock:
            ordered = sorted(
                self._data.values(),
                key=lambda r: r.get("created_at", ""),
                reverse=True,
            )
            return [dict(r) for r in ordered[:limit]]


class SupabaseStorage:
    """Supabase-backed persistence. Requires ``SUPABASE_URL`` and ``SUPABASE_KEY``.

    The key MUST be the service-role key. The anon key cannot bypass RLS and
    therefore cannot read or write this table.
    """

    TABLE = "simulations"

    def __init__(self, url: str, key: str) -> None:
        from supabase import Client, create_client  # imported lazily

        self._client: Client = create_client(url, key)

    def create(self, *, question: str, turns: int, actors: list[dict]) -> str:
        payload = {
            "question": question,
            "turns": turns,
            "actors": actors,
            "status": "pending",
        }
        response = self._client.table(self.TABLE).insert(payload).execute()
        if not response.data:
            raise RuntimeError("Failed to insert simulation row")
        return response.data[0]["id"]

    def get(self, simulation_id: str) -> Optional[SimulationRecord]:
        response = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", simulation_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def update_actors(self, simulation_id: str, actors: list[dict], turns: int) -> None:
        self._client.table(self.TABLE).update(
            {"actors": actors, "turns": turns}
        ).eq("id", simulation_id).execute()

    def set_status(self, simulation_id: str, status: str, *, error: Optional[str] = None) -> None:
        payload: dict[str, Any] = {"status": status}
        if error is not None:
            payload["error"] = error
        self._client.table(self.TABLE).update(payload).eq("id", simulation_id).execute()

    def set_result_and_report(
        self, simulation_id: str, *, result: dict, report: dict
    ) -> None:
        self._client.table(self.TABLE).update(
            {"result": result, "report": report, "status": "done"}
        ).eq("id", simulation_id).execute()

    def list_recent(self, *, limit: int = 50) -> list[SimulationRecord]:
        response = (
            self._client.table(self.TABLE)
            .select("id,question,status,turns,created_at,updated_at,error")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []


def build_storage() -> Storage:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if url and key:
        try:
            storage: Storage = SupabaseStorage(url=url, key=key)
            logger.info("Using Supabase persistence")
            return storage
        except Exception:
            logger.exception("Supabase init failed; falling back to in-memory storage")
    logger.info("Using in-memory storage (set SUPABASE_URL and SUPABASE_KEY to persist)")
    return InMemoryStorage()


storage: Storage = build_storage()
