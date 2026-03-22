class SmartCommitError(Exception):
    detail = "Unknown error"

    def __init__(self, *args):
        message = args[0] if args else self.detail
        super().__init__(message)


class GitOperationError(SmartCommitError):
    detail = "Git execution failed"


class ValidationError(SmartCommitError):
    detail = "Validation check failed"
