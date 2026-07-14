# app/automation/contact.py

from backend.app.automation.hooks import register_hook


def on_contact_created(context):
    print(f"[HOOK] contact.created | {context}")


register_hook("contact.created", on_contact_created)
