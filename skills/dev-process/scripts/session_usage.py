#!/usr/bin/env python3
"""Extract Hermes session model/token usage for dev-process artifacts.

Reads one JSON object exported by:
  hermes sessions export /tmp/session.jsonl --session-id '<id>'

Prints JSON or a compact Markdown row. Policy resolution and model_usage rows:
use dp_stage_boundary.py instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


def load_session_export(path: Path) -> dict[str, Any]:
    """Load one Hermes session object from exported JSONL (single non-empty line)."""
    return _load_session(path)


def _load_session(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"session export not found: {path}")
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not lines:
        raise ValueError(f"session export is empty: {path}")
    if len(lines) != 1:
        raise ValueError(
            f"session export must contain exactly one non-empty JSONL line, found {len(lines)}: {path}"
        )
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in session export line: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"unexpected top-level type (expected object): {path}")
    return payload


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_num(value: int | None) -> str:
    if value is None:
        return "unknown"
    return f"{value:,}"


def _fmt_usd(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"${value:.6f}"


def _md_cell(value: Any) -> str:
    if value is None:
        text = "unknown"
    else:
        text = str(value)
    return text.replace("\n", " ").replace("|", r"\|")


def _fmt_time(value: Any) -> str:
    ts = _to_float(value)
    if ts is None:
        return "unknown"
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def resolve_time_cell(time_value: str, summary: dict[str, Any]) -> str:
    if time_value != "auto":
        return time_value
    started = _fmt_time(summary.get("started_at"))
    ended = _fmt_time(summary.get("ended_at"))
    if started == "unknown" and ended == "unknown":
        return "unknown"
    if started == ended:
        return started
    return f"{started} -> {ended}"


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    input_tokens = _to_int(payload.get("input_tokens"))
    output_tokens = _to_int(payload.get("output_tokens"))
    reasoning_tokens = _to_int(payload.get("reasoning_tokens"))
    cache_read_tokens = _to_int(payload.get("cache_read_tokens"))
    cache_write_tokens = _to_int(payload.get("cache_write_tokens"))
    total_tokens = None
    if input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    model_config_raw = payload.get("model_config")
    model_config = None
    if isinstance(model_config_raw, str) and model_config_raw.strip():
        try:
            model_config = json.loads(model_config_raw)
        except json.JSONDecodeError:
            model_config = model_config_raw
    elif isinstance(model_config_raw, dict):
        model_config = model_config_raw

    return {
        "session_id": payload.get("id"),
        "title": payload.get("title"),
        "model": payload.get("model"),
        "model_config": model_config,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens_no_cache": total_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "api_call_count": _to_int(payload.get("api_call_count")),
        "message_count": _to_int(payload.get("message_count")),
        "estimated_cost_usd": _to_float(payload.get("estimated_cost_usd")),
        "actual_cost_usd": _to_float(payload.get("actual_cost_usd")),
        "started_at": payload.get("started_at"),
        "ended_at": payload.get("ended_at"),
    }


def format_usage_cost(summary: dict[str, Any]) -> str:
    tokens = (
        f"in={_fmt_num(summary.get('input_tokens'))}, "
        f"out={_fmt_num(summary.get('output_tokens'))}, "
        f"reasoning={_fmt_num(summary.get('reasoning_tokens'))}, "
        f"total(no-cache)={_fmt_num(summary.get('total_tokens_no_cache'))}, "
        f"cache_read={_fmt_num(summary.get('cache_read_tokens'))}"
    )
    cost = (
        f"actual={_fmt_usd(summary.get('actual_cost_usd'))}, "
        f"est={_fmt_usd(summary.get('estimated_cost_usd'))}"
    )
    return f"{tokens}; {cost}"


def markdown_row(
    summary: dict[str, Any],
    *,
    time_cell: str,
    stage_id: str,
    action: str,
    profile: str,
    role: str,
    preset: str,
    reasoning: str,
    evidence: str,
) -> str:
    model = _md_cell(summary.get("model") or "unknown")
    session_id = _md_cell(summary.get("session_id") or "unknown")
    profile_role = _md_cell(f"{profile} / {role}")
    preset_reasoning = _md_cell(f"{preset} / {reasoning}")
    return (
        f"| {_md_cell(time_cell)} | `{_md_cell(stage_id)}` | {_md_cell(action)} | "
        f"{profile_role} | {preset_reasoning} | `{session_id}` | {model} | "
        f"{_md_cell(format_usage_cost(summary))} | {_md_cell(evidence)} |"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract model/token/cost summary from Hermes session export JSONL."
    )
    parser.add_argument("session_export", help="Path to exported session JSONL file.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--stage-id",
        default="implementation",
        help="Stage id for markdown row mode.",
    )
    parser.add_argument(
        "--time",
        default="[time]",
        help="Time cell. Use 'auto' for started_at -> ended_at from export.",
    )
    parser.add_argument("--evidence", default="hermes sessions export")
    parser.add_argument("--action", default="[action]")
    parser.add_argument("--role", default="[role]")
    parser.add_argument("--profile", default="[profile]")
    parser.add_argument("--preset", default="[preset]")
    parser.add_argument("--reasoning", default="[expected/observed]")
    args = parser.parse_args()

    try:
        payload = _load_session(Path(args.session_export))
    except (OSError, ValueError) as exc:
        print(f"session_usage.py: {exc}", file=sys.stderr)
        return 2
    summary = build_summary(payload)

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=True, indent=2))
    else:
        print(
            markdown_row(
                summary,
                time_cell=resolve_time_cell(args.time, summary),
                stage_id=args.stage_id,
                action=args.action,
                profile=args.profile,
                role=args.role,
                preset=args.preset,
                reasoning=args.reasoning,
                evidence=args.evidence,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
