from loguru import logger
import sys

def setup_logging():
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",  # Rotate file every 10 MB
        retention="7 days", # Keep logs for 7 days
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    return logger

# Initialize logger
logger = setup_logging()
