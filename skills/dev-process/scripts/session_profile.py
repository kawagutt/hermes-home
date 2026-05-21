"""Extract Hermes profile hints from session export payloads."""

from __future__ import annotations

import re
from typing import Any

DP_PROFILE_RE = re.compile(r"\b(dp-[a-z0-9-]+)\b", re.IGNORECASE)


def observed_profile_from_export(
    payload: dict[str, Any], summary: dict[str, Any] | None = None
) -> str:
    """Best-effort profile name from export (empty if not observable)."""
    summary = summary or {}
    for source in (payload, summary):
        if not isinstance(source, dict):
            continue
        for key in ("hermes_profile", "profile", "dp_profile"):
            raw = source.get(key)
            if isinstance(raw, str) and raw.strip().lower().startswith("dp-"):
                return raw.strip()
        mc = source.get("model_config")
        if isinstance(mc, dict):
            for key in ("profile", "hermes_profile", "hermesProfile"):
                raw = mc.get(key)
                if isinstance(raw, str) and raw.strip().lower().startswith("dp-"):
                    return raw.strip()
    title = payload.get("title")
    if isinstance(title, str):
        m = DP_PROFILE_RE.search(title)
        if m:
            return m.group(1)
    return ""
