# hf_backup_tool/exceptions/custom_exceptions.py
# Custom exception classes for the Hugging Face Backup Tool.


class APIKeyError(Exception):
    """
    Raised when there's an issue with the API key.

    Possible causes include:
        - API key is missing or invalid.
        - API key does not have the required permissions.
        - API key has been revoked.
    """

    pass


class UploadError(Exception):
    """
    Raised during file upload failures.

    Possible causes include:
        - Network connectivity issues.
        - Insufficient permissions to upload to the repository.
        - File size exceeds the maximum allowed limit.
        - Invalid file format.
    """

    pass


class ConfigError(Exception):
    """
    Raised when there are configuration issues.

    Possible causes include:
        - Configuration file is missing or corrupted.
        - Required configuration settings are missing.
        - Invalid configuration values.
    """

    pass


class RateLimitError(Exception):
    """
    Raised when the application exceeds the Hugging Face Hub's rate limits.

    Possible causes include:
        - Making too many API requests in a short period of time.
        - Not implementing proper rate limiting mechanisms.
    """

    pass


class AuthenticationError(Exception):
    """
    Raised when authentication with the Hugging Face Hub fails.

    Possible causes include:
        - Invalid API token.
        - Incorrect username or password (if applicable).
        - Account is locked or disabled.
    """

    pass


class RepositoryError(Exception):
    """
    Raised when there are issues with the Hugging Face repository.

    Possible causes include:
        - Repository does not exist.
        - Insufficient permissions to access the repository.
        - Repository is corrupted or unavailable.
    """

    pass
