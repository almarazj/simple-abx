import os
import logging
from app.core.config import settings

def setup_logging():
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("simple_abx")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(settings.LOG_FORMAT)

    file_handler = logging.FileHandler(settings.LOG_FILE, mode='a')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.propagate = False

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        log = logging.getLogger(logger_name)
        log.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        for handler in log.handlers:
            handler.setFormatter(formatter)
    
def get_app_logger() -> logging.Logger:
    """Obtener el logger de la aplicación"""
    return logging.getLogger("simple_abx")