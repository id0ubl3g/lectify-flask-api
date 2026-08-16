from dotenv import load_dotenv
from datetime import timedelta
import mercadopago
import os

load_dotenv()

def initialize_mercadopago() -> dict:
    sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_SECRET_KEY"))

    plans = {
        "1_month": {
            "name": "1 Month",
            "price": 19.90,
            "days": 30
        },
        "6_months": {
            "name": "6 Months",
            "price": 99.90,
            "days": 180
        },
        "1_year": {
            "name": "1 Year",
            "price": 179.90,
            "days": 365
        }
    }

    return {
        "mercadopago": sdk,
        "webhook_secret": os.getenv("MERCADOPAGO_WEBHOOK_SECRET"),
        "plans": plans,
    }