import os
from pathlib import Path

# Load OpenRouter key from heft_gateway .env
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

env_file = Path.home() / "heft_gateway" / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY=") and not OPENROUTER_API_KEY:
            OPENROUTER_API_KEY = line.split("=", 1)[1].strip()

# Models — all via OpenRouter
PLANNER_MODEL = "google/gemini-2.5-pro"  # smart model for planning + research
RENDERER_MODEL = "google/gemini-2.5-flash"  # capable model for subagent rendering
PORT = 8770
