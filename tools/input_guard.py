"""Heuristic input guard for prompt-injection and abusive inputs (demo-level)."""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent / "config"
GUARD_CONFIG_PATH = CONFIG_DIR / "input_guard.yaml"

_REQUIRED_KEYS = (
    "max_input_length",
    "blocked_message",
    "empty_input_message",
    "length_exceeded_message",
    "error_fallback_message",
    "patterns",
)


@dataclass(frozen=True)
class GuardResult:
    """Result of validating user input before it reaches an agent."""

    allowed: bool
    message: str | None = None


@functools.lru_cache(maxsize=1)
def _load_guard_config() -> dict:
    """Load and cache parsed guard configuration from YAML."""
    if not GUARD_CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Guard config not found: {GUARD_CONFIG_PATH}")

    with open(GUARD_CONFIG_PATH, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Guard config must be a mapping: {GUARD_CONFIG_PATH}")

    for key in _REQUIRED_KEYS:
        if key not in data:
            raise KeyError(f"Guard config missing required key '{key}': {GUARD_CONFIG_PATH}")

    patterns = data["patterns"]
    if not isinstance(patterns, list) or not patterns:
        raise ValueError(f"Guard config 'patterns' must be a non-empty list: {GUARD_CONFIG_PATH}")

    compiled = []
    for index, pattern in enumerate(patterns):
        if not isinstance(pattern, str):
            raise ValueError(f"Pattern at index {index} must be a string.")
        compiled.append(re.compile(pattern))

    return {
        "max_input_length": int(data["max_input_length"]),
        "blocked_message": str(data["blocked_message"]).rstrip(),
        "empty_input_message": str(data["empty_input_message"]).rstrip(),
        "length_exceeded_message": str(data["length_exceeded_message"]).rstrip(),
        "error_fallback_message": str(data["error_fallback_message"]).rstrip(),
        "compiled_patterns": tuple(compiled),
    }


def get_error_fallback_message() -> str:
    """Return the configured fallback message for unexpected runtime errors."""
    return _load_guard_config()["error_fallback_message"]


def check_user_input(text: str) -> GuardResult:
    """
    Validate user input before invoking an agent.

    Returns:
        GuardResult with allowed=True when input may proceed, or allowed=False
        with a user-facing fallback message when blocked.
    """
    config = _load_guard_config()
    stripped = (text or "").strip()

    if not stripped:
        return GuardResult(allowed=False, message=config["empty_input_message"])

    if len(stripped) > config["max_input_length"]:
        return GuardResult(allowed=False, message=config["length_exceeded_message"])

    for pattern in config["compiled_patterns"]:
        if pattern.search(stripped):
            return GuardResult(allowed=False, message=config["blocked_message"])

    return GuardResult(allowed=True, message=None)
