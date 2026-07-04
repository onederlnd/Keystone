# app/automation/pipeline

from app.automation.hooks import register_hook


def on_pipeline_offer_submitted(context):
    print(f"[HOOK] pipeline.offer_submitted | {context}")


def on_pipeline_closed(context):
    print(f"[HOOK] pipeline.closed | {context}")


def on_pipeline_lost(context):
    print(f"[HOOK] pipeline.lost | {context}")


register_hook("pipeline.offer_submitted", on_pipeline_offer_submitted)
register_hook("pipeline.closed", on_pipeline_closed)
register_hook("pipeline.lost", on_pipeline_lost)
