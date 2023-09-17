from loguru import logger


class CustomError(Exception):
    """Base class for other exceptions"""

    def __init__(self, message):
        self.message = message
        logger.exception(message)


class FeatureNotSupported(CustomError):
    """Raised when Rulewerk feature is not supported in the current tool"""

    pass


class DirectoryNotFound(CustomError):
    """Raised when a directory is not found"""

    pass


class NoRlsFilesFound(CustomError):
    """Raised when no .rls files are found in the provided directory"""

    pass


class CouldNotStartJVM(CustomError):
    """Raised when JVM failed to start"""

    pass


class SystemNotSupported(CustomError):
    """Raised when Rulewerk feature is not supported in the current tool"""

    pass


def input_path_error(exc):
    # if given rls file path does not exist then raise error
    raise exc
