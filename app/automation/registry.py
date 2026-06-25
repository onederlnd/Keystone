# app/automation/registry.py

# This dict is the central store for all registered automation hooks.
# Shape: { "event.name": [fn1, fn2, ...] }
# Hooks are registered here via register_hook() in hooks.py.
# Nothing should write to this dict directly — always go through register_hook().

REGISTRY = {}
