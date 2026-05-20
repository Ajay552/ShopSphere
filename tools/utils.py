import functools
from pathlib import Path

import yaml
from langchain_ollama import ChatOllama

# Resolve project directories relative to the package root.
DATA_DIR = Path(__file__).parent.parent / "data"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@functools.lru_cache(maxsize=None)
def _load_prompt_yaml(stem: str) -> dict:
    """Load and cache parsed YAML from prompts/{stem}.yaml."""
    filepath = PROMPTS_DIR / f"{stem}.yaml"
    if not filepath.is_file():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_prompt(stem: str, **format_kwargs) -> str:
    """
    Load a system prompt from prompts/{stem}.yaml.

    Args:
        stem: YAML filename without extension (e.g. "part_a").
        format_kwargs: Optional key-value pairs for template substitution.

    Returns:
        The system prompt string, with template placeholders filled when requested.
    """
    data = _load_prompt_yaml(stem)

    if format_kwargs:
        if "template" not in data:
            raise KeyError(f"Prompt file '{stem}.yaml' has no 'template' key for formatting.")
        return data["template"].format(**format_kwargs).rstrip()

    if "system_prompt" not in data:
        raise KeyError(f"Prompt file '{stem}.yaml' has no 'system_prompt' key.")
    return data["system_prompt"].rstrip()


def get_llm():
    """Return the configured local Ollama chat model."""
    return ChatOllama(model="gemma4:e4b", temperature=0)
