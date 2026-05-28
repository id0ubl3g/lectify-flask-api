from dotenv import load_dotenv
from datetime import timedelta
import stripe
import os

load_dotenv()

def initialize_stripe() -> dict:
    stripe.api_key = os.getenv('stripe_secret_key')

    plans = {
        "1_month": os.getenv('stripe_price_1_month'),
        "6_months": os.getenv('stripe_price_6_months'),
        "1_year": os.getenv('stripe_price_1_year')
    }

    durations = {
        "1_month": timedelta(days=30),
        "6_months": timedelta(days=180),
        "1_year": timedelta(days=365)
    }

    return {
        "stripe": stripe,
        "stripe_webhook_secret": os.getenv('stripe_webhook_secret'),
        "plans": plans,
        "durations": durations
    }