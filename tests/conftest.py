import os

# config.py requires these at import time; tests don't need real values.
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
