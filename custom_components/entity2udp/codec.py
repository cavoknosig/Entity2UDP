"""Pure, testable entity-to-wire conversion and configuration validation."""
from __future__ import annotations

import math
import re

KEY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
NUMBER_PATTERN = re.compile(r"-?(?:\d+)(?:\.\d+)?")
INVALID_STATES = {"unknown", "unavailable", "none", ""}
COVER_STATES = {"closed": 0, "open": 1, "opening": 2, "closing": 3}


def default_key(entity_id: str) -> str:
    return "ha_" + entity_id.replace(".", "_").replace("-", "_")


def validate_rule(entity_id: str, rule: dict) -> dict:
    if not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", entity_id):
        raise ValueError("invalid_entity")
    if not isinstance(rule, dict):
        raise ValueError("invalid_rule")
    key = rule.get("key", default_key(entity_id))
    if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
        raise ValueError("invalid_key")
    kind = rule.get("type", "auto")
    if kind not in ("auto", "number", "boolean", "text"):
        raise ValueError("invalid_type")
    translation = rule.get("translations", {})
    if not isinstance(translation, dict) or any(not isinstance(k, str) or not isinstance(v, (str, int, float, bool)) or isinstance(v, float) and not math.isfinite(v) for k, v in translation.items()):
        raise ValueError("invalid_translations")
    scale = float(rule.get("scale", 1))
    if not math.isfinite(scale):
        raise ValueError("invalid_scale")
    precision = int(rule.get("precision", 3))
    if not 0 <= precision <= 10:
        raise ValueError("invalid_precision")
    interval = float(rule.get("min_interval_seconds", 0))
    if not math.isfinite(interval) or not 0 <= interval <= 86400:
        raise ValueError("invalid_interval")
    delta = float(rule.get("min_delta", 0))
    if not math.isfinite(delta) or delta < 0:
        raise ValueError("invalid_delta")
    sentinel = str(rule.get("invalid_value", "-9999"))
    if not NUMBER_PATTERN.fullmatch(sentinel):
        raise ValueError("invalid_sentinel")
    enabled = rule.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("invalid_enabled")
    validated = {"key": key, "type": kind, "translations": translation,
            "scale": scale, "precision": precision,
            "min_delta": delta, "invalid_value": sentinel}
    if "enabled" in rule:
        validated["enabled"] = enabled
    if "min_interval_seconds" in rule:
        validated["min_interval_seconds"] = interval
    return validated


def encode_value(
    state: str | None, rule: dict, destination_sentinel: str, *, entity_id: str = ""
) -> tuple[str, bool]:
    """Return (wire value, invalid). Translation happens before type conversion."""
    if state is None or state.lower() in INVALID_STATES:
        return str(rule.get("invalid_value", destination_sentinel)), True
    kind = rule.get("type", "auto")
    fallback = COVER_STATES.get(state, state) if kind == "auto" and entity_id.startswith("cover.") else state
    mapped = rule.get("translations", {}).get(state, fallback)
    value = str(mapped).strip()
    if kind == "boolean" or (kind == "auto" and (isinstance(mapped, bool) or value.lower() in ("on", "off"))):
        if value.lower() in ("on", "true", "1"):
            return "1", False
        if value.lower() in ("off", "false", "0"):
            return "0", False
        return str(rule.get("invalid_value", destination_sentinel)), True
    if kind == "text":
        if any(c in value for c in "\r\n\x00") or len(value) > 512:
            return str(rule.get("invalid_value", destination_sentinel)), True
        return value, False
    try:
        number = float(value) * float(rule.get("scale", 1))
        if not math.isfinite(number):
            raise ValueError("non-finite")
    except (ValueError, TypeError, OverflowError):
        return str(rule.get("invalid_value", destination_sentinel)), True
    if float(rule.get("scale", 1)) == 1 and kind == "auto" and NUMBER_PATTERN.fullmatch(value):
        return value, False
    precision = int(rule.get("precision", 3))
    return f"{number:.{precision}f}".rstrip("0").rstrip(".") if precision else f"{number:.0f}", False
