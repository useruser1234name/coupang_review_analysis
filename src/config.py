import os
from dotenv import load_dotenv
from src.utils.logger import logger

load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "coupang_reviews")

    # Proxy Configuration
    PROXY_HOST = os.getenv("PROXY_HOST")
    PROXY_USERNAME = os.getenv("PROXY_USERNAME")
    PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

    # Scraping Browser WebDriver
    SBR_WEBDRIVER_AUTH = os.getenv("SBR_WEBDRIVER_AUTH")

    @classmethod
    def validate(cls):
        required_vars = [
            "DB_PASSWORD",
            "PROXY_HOST",
            "PROXY_USERNAME",
            "PROXY_PASSWORD",
            "SBR_WEBDRIVER_AUTH"
        ]
        missing_vars = [var for var in required_vars if getattr(cls, var) is None]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file.")
            # sys.exit(1) # Uncomment to exit if critical variables are missing

Config.validate()
