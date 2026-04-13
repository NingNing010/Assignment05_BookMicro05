"""
Shared utility functions.
"""
import json


def safe_json_loads(raw, default=None):
    """Safely parse a JSON string, returning *default* on failure."""
    if default is None:
        default = {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default
