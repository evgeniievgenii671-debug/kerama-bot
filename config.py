import os
from pathlib import Path
from dotenv import load_dotenv
PORT = int(os.environ.get("PORT", 8080))
load_dotenv()

# === ����� (�������� �������� �� ����!) ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MANAGER_CHAT_ID = int(os.environ.get("MANAGER_CHAT_ID", "0"))

# === ������ Groq ===
MODEL_MAIN = "openai/gpt-oss-120b"
MODEL_BACKUP = "openai/gpt-oss-20b"
MODEL_WHISPER = "whisper-large-v3"

# === ���� ===
DB_PATH = Path("bot.db")
CATALOG_PATH = Path(__file__).parent / "data" / "catalog.json"
TMP_DIR = Path("tmp")
TMP_DIR.mkdir(exist_ok=True)
