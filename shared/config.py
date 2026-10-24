"""Loads environment config and the product catalog for every agent."""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load the .env sitting at the project root
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---- ASI:One ----
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY", "")
ASI_ONE_BASE_URL = os.getenv("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_ONE_MODEL = os.getenv("ASI_ONE_MODEL", "asi1-mini")

# ---- Razorpay ----
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# ---- Agent addresses ----
COORDINATOR_ADDRESS = os.getenv("COORDINATOR_ADDRESS", "")
INGESTION_ADDRESS = os.getenv("INGESTION_ADDRESS", "")
INTENT_ADDRESS = os.getenv("INTENT_ADDRESS", "")
INVOICE_ADDRESS = os.getenv("INVOICE_ADDRESS", "")
PAYMENT_ADDRESS = os.getenv("PAYMENT_ADDRESS", "")

PAYMENT_WEBHOOK_URL = os.getenv("PAYMENT_WEBHOOK_URL", "")


def load_catalog():
    with open(ROOT / "shared" / "catalog.json", "r", encoding="utf-8") as f:
        return json.load(f)
