"""Pytest fixtures for dev-process tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _skip_profile_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    """CI may not have Hermes; job start skips profile probe in tests."""
    monkeypatch.setenv("DEV_PROCESS_NO_PROFILE_PROBE", "1")
