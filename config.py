import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Court Reserve credentials
    USERNAME = os.getenv("CR_USERNAME")
    PASSWORD = os.getenv("CR_PASSWORD")

    # Site URLs
    LOGIN_URL = "https://app.courtreserve.com/Online/Account/LogIn/13730"
    EVENTS_URL = "https://app.courtreserve.com/Online/Events/List/13730/"
    BASE_URL = "https://app.courtreserve.com"

# 11710. -- East
# 13730. -- South

    # Settings
    SKILL_LEVEL = os.getenv("SKILL_LEVEL", "Intermediate (3.0 - 3.49)")
    ADVANCE_BOOKING_DAYS = int(os.getenv("ADVANCE_BOOKING_DAYS", "21"))

    # Time preferences
    WEEKDAY_TIME = "Evening"  # Monday - Friday
    WEEKEND_TIME = "Morning"  # Saturday - Sunday

    # Price filter
    MAX_PRICE = 0  # Only free events

    @staticmethod
    def get_target_date():
        """Calculate the target booking date (21 days from now)"""
        return datetime.now() + timedelta(days=Config.ADVANCE_BOOKING_DAYS)

    @staticmethod
    def is_weekend(date):
        """Check if date is weekend (Saturday=5, Sunday=6)"""
        return date.weekday() >= 5

    @staticmethod
    def get_time_filter(date):
        """Get appropriate time filter based on day of week"""
        return Config.WEEKEND_TIME if Config.is_weekend(date) else Config.WEEKDAY_TIME

    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.USERNAME or not Config.PASSWORD:
            raise ValueError("CR_USERNAME and CR_PASSWORD must be set in .env file")
        return True
