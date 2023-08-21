from loguru import logger


class FeatureNotSupported(Exception):
    logger.error("Feature not supported")


class DirectoryNotFound(Exception):
    logger.error("Could not find directory!")
