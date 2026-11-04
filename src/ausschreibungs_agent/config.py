"""Liest Einstellungen und API-Keys aus der .env-Datei."""
import os

from dotenv import load_dotenv

load_dotenv()

BEISPIEL_QUELLE_API_KEY = os.getenv("BEISPIEL_QUELLE_API_KEY", "")
KI_API_KEY = os.getenv("KI_API_KEY", "")
SUCHBEGRIFFE = [s.strip() for s in os.getenv("SUCHBEGRIFFE", "").split(",") if s.strip()]
OUTPUT_ORDNER = "output"
