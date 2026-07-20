import asyncio
from celery import Task
from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog


class NotificationTask(Task):
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        asyncio.run(self._log_failure(exc, task_id, args, kwargs))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        asyncio.run(self._log_failure(exc, task_id, args, kwargs))

    async def _log_failure(self, exc, task_id, args, kwargs):
        async with AsyncSessionLocal() as db:
            log = AuditLog(
                entity_type=kwargs.get("entity_type", "unknown"),
                entity_id=str(args[0]),
                action="notification_failed",
                from_state=None,
                to_state=None,
                triggered_by="automation",
                actor_id=None,
                notes=f"task_id={task_id} error={exc}",
            )
            db.add(log)
            await db.commit()
