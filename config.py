import os
from dotenv import load_dotenv

load_dotenv()

ALERT_SERVER_URL = os.getenv("ALERT_SERVER_URL", "http://127.0.0.1:5001/alert")
ALERT_SERVER_PORT = int(os.getenv("ALERT_SERVER_PORT", "5001"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
ASK_HIGH_APPROVAL = os.getenv("ASK_HIGH_APPROVAL", "true").lower() == "true"
