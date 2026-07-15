# app/automation/hooks.py
import inspect
from app.core.config import settings
from app.automation.registry import REGISTRY


def register_hook(event, fn):
    REGISTRY.setdefault(event, [])
    REGISTRY[event].append(fn)


async def fire_hook(event, context):
    if not settings.automation_enabled:
        print(f"[AUTOMATION DISABLED] Would fire hook: {event} with context: {context}")
        return

    functions = REGISTRY.get(event, [])

    for fn in functions:
        if inspect.iscoroutinefunction(fn):
            await fn(context)
        else:
            fn(context)
