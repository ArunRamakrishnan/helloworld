"""Loads versioned LLM system prompts from prompts/system/*.md.

Keeps prompt text out of Python source, matching the repo's own convention of
versioning prompts under prompts/ (see prompts/master_prompt.md). Each file may
optionally start with a `---` front-matter block (version/date metadata); everything
after the closing `---` is the actual system prompt text.
"""
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts" / "system"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """Loads prompts/system/<name>.md and returns the prompt body (front-matter stripped)."""
    path = PROMPTS_DIR / f"{name}.md"
    text = path.read_text().strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text
