import json
from pathlib import Path

from langchain_ollama import ChatOllama

# Resolve the data directory relative to project root.
DATA_DIR = Path(__file__).parent.parent / "data"


def load_data(filename: str):
    """Load and return parsed JSON content from the data directory."""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def get_llm():
    """Return the configured local Ollama chat model."""
    return ChatOllama(model="gemma4:e4b", temperature=0)
