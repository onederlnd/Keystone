# app/automation/listing_hook.py

from app.automation.hooks import register_hook


def on_listing_active(context):
    print(f"[HOOK] listing.active | {context}")


def on_listing_under_contract(context):
    print(f"[HOOK] listing.under_contract | {context}")


def on_listing_sold(context):
    print(f"[HOOK] listing.sold | {context}")


register_hook("listing.active", on_listing_active)
register_hook("listing.under_contract", on_listing_under_contract)
register_hook("listing.sold", on_listing_sold)
