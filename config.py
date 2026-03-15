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

# Models -- 3-model pipeline via OpenRouter
PLANNER_MODEL = "openai/gpt-5.2-pro"             # Stage 1: research + planning (fast, cost-effective)
OUTLINE_MODEL = "google/gemini-3-flash-preview"   # Stage 2: master blueprint structure + matrix outline
RENDERER_MODEL = "qwen/qwen3.5-397b-a17b"        # Stage 3: department execution (massive model for depth)
PORT = int(os.environ.get("PORT", 8770))

# Firebase / Google Cloud
FIREBASE_PROJECT_ID = "studio-2972039985-2dbb1"
FIRESTORE_DATABASE = "blueprint-maker"
STORAGE_BUCKET = "blueprint-maker-storage-983595415114"

# Block renderer version — increment when block renderers change
CURRENT_RENDERER_VERSION = 1

# Model for chat-based blueprint editing (fast, cheap)
EDITOR_MODEL = os.getenv("EDITOR_MODEL", "google/gemini-2.5-flash")
