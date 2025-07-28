import logging
import os

def setup_logger(name: str = "app", log_file: str = "logs/app.log", level=logging.DEBUG):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Avoid duplicating handlers
    if not logger.hasHandlers():
        logger.addHandler(file_handler)

    return logger

# Global logger
app_logger = setup_logger()
