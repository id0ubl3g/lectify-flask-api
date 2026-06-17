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
            "price": 0.1,
            "duration": timedelta(days=30)
        },
        "6_months": {
            "name": "6 Months",
            "price": 149.90,
            "duration": timedelta(days=180)
        },
        "1_year": {
            "name": "1 Year",
            "price": 249.90,
            "duration": timedelta(days=365)
        }
    }

    return {
        "mercadopago": sdk,
        "webhook_secret": os.getenv("MERCADOPAGO_WEBHOOK_SECRET"),
        "plans": plans,
    }