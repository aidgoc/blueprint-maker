import os
from pathlib import Path

# Load OpenRouter key from environment first, then fallback to heft_gateway .env
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    env_file = Path.home() / "heft_gateway" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith("OPENROUTER_API_KEY="):
                val = line.split("=", 1)[1].strip()
                # Strip surrounding quotes if present
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                OPENROUTER_API_KEY = val
                break

# Models -- all via OpenRouter
PLANNER_MODEL = "google/gemini-2.5-pro"  # smart model for planning + research
RENDERER_MODEL = "google/gemini-2.5-flash"  # capable model for subagent rendering
PORT = int(os.environ.get("PORT", 8770))

# Firebase / Google Cloud
FIREBASE_PROJECT_ID = "studio-2972039985-2dbb1"
FIRESTORE_DATABASE = "blueprint-maker"
STORAGE_BUCKET = "blueprint-maker-storage-983595415114"
