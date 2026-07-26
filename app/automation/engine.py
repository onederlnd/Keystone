# app/automation/engine.py

from datetime import datetime, timezone
from sqlalchemy import select
from app.models.automation_rule import AutomationRule
from app.models.approval_queue import ApprovalQueue
from app.core.config import settings


async def evaluate_rules(event, context, db):
    from app.automation.hooks import fire_hook

    if not settings.automation_enabled:
        return

    result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.trigger_event == event, AutomationRule.is_active
        )
    )
    rules = result.scalars().all()

    for rule in rules:
        if evaluate_condition(rule.condition, context):
            if rule.requires_approval:
                queue_entry = ApprovalQueue(
                    entity_type=event.split(".")[0],
                    entity_id=(
                        context.get("listing_id")
                        or context.get("pipeline_id")
                        or context.get("contact_id")
                        or context.get("document_id")
                    ),
                    proposed_action=rule.action,
                    context=context,
                    status="pending",
                    created_by="automation",
                )
                db.add(queue_entry)
                await db.commit()
            else:
                await fire_hook(rule.action, context)


def evaluate_condition(condition, context):
    field = condition["field"]
    op = condition["op"]
    value = condition["value"]
    context_value = context.get(field)

    if context_value is None:
        return False

    match op:
        case "eq":
            return context_value == value
        case "gt":
            return context_value > value
        case "lt":
            return context_value < value
        case "contains":
            return value in context_value
        case "days_since":
            elapsed = datetime.now(timezone.utc) - context_value
            return elapsed.days >= value
        case _:
            return False
