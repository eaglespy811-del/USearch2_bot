import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Твоя карта для переводов
CARD_NUMBER = "2202208263906811"

# Цены и тарифы
PRICES = {
    "day": {"price": 49, "days": 1, "name": "1 день"},
    "week": {"price": 149, "days": 7, "name": "7 дней"},
    "month": {"price": 599, "days": 30, "name": "30 дней"},
    "year": {"price": 1299, "days": 365, "name": "365 дней"}
}

# Лимиты поиска
FREE_LIMIT = 3
PREMIUM_LIMIT = 20