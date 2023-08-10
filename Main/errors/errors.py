from loguru import logger
class CustomError(Exception):
    """Raised when feature is not supported"""
    logger.error("Feature is not supported")
