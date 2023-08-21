from loguru import logger


class CustomError(Exception):
    """Base class for other exceptions"""

    def __init__(self, message):
        self.message = message
        logger.error(message)


class FeatureNotSupported(CustomError):
    """Raised when Rulewerk feature is not supported in the current tool"""

    pass


class DirectoryNotFound(CustomError):
    """Raised when a directory is not found"""

    pass


class NoRlsFilesFound(Exception):
    """Raised when no .rls files are found in the provided directory"""

    pass


class CouldNotStartJVM(Exception):
    """Raised when JVM failed to start"""

    pass
