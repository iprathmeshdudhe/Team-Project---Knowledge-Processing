class FeatureNotSupported(Exception):
    """Raised when Rulewerk feature is not supported in the current tool"""

    pass


class DirectoryNotFound(Exception):
    """Raised when a directory is not found"""

    pass


class NoRlsFilesFound(Exception):
    """Raised when no .rls files are found in the provided directory"""

    pass


class CouldNotStartJVM(Exception):
    """Raised when JVM failed to start"""

    pass
