"""Structured error codes for the API."""

from enum import StrEnum


class ErrorCategory(StrEnum):
    """Error category for grouping related errors."""

    NETWORK = "network"
    GENERATION = "generation"
    VALIDATION = "validation"
    SERVER = "server"
    RATE_LIMIT = "rate_limit"
    AUTOFIX = "autofix"


class ErrorCode(StrEnum):
    """Structured error codes shared between backend and frontend."""

    # Network errors
    NETWORK_DISCONNECTED = "NETWORK_DISCONNECTED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"

    # Generation errors
    GENERATION_FAILED = "GENERATION_FAILED"
    GENERATION_TIMEOUT = "GENERATION_TIMEOUT"
    GENERATION_EMPTY = "GENERATION_EMPTY"

    # Validation errors
    VALIDATION_SYNTAX_ERROR = "VALIDATION_SYNTAX_ERROR"
    VALIDATION_INVALID_TYPE = "VALIDATION_INVALID_TYPE"
    VALIDATION_UNBALANCED_BRACKETS = "VALIDATION_UNBALANCED_BRACKETS"
    VALIDATION_EMPTY_NODE = "VALIDATION_EMPTY_NODE"

    # Server errors
    SERVER_INTERNAL_ERROR = "SERVER_INTERNAL_ERROR"
    SERVER_DATABASE_ERROR = "SERVER_DATABASE_ERROR"

    # Rate limit errors
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Autofix errors
    AUTOFIX_FAILED = "AUTOFIX_FAILED"
    AUTOFIX_MAX_ATTEMPTS = "AUTOFIX_MAX_ATTEMPTS"


# Error messages in Japanese and English
ERROR_MESSAGES: dict[ErrorCode, dict[str, str]] = {
    ErrorCode.NETWORK_DISCONNECTED: {
        "ja": "ネットワーク接続が切断されました",
        "en": "Network connection lost",
    },
    ErrorCode.NETWORK_TIMEOUT: {
        "ja": "接続がタイムアウトしました",
        "en": "Connection timed out",
    },
    ErrorCode.GENERATION_FAILED: {
        "ja": "図の生成に失敗しました",
        "en": "Failed to generate diagram",
    },
    ErrorCode.GENERATION_TIMEOUT: {
        "ja": "生成がタイムアウトしました",
        "en": "Generation timed out",
    },
    ErrorCode.GENERATION_EMPTY: {
        "ja": "空の結果が返されました",
        "en": "Empty result returned",
    },
    ErrorCode.VALIDATION_SYNTAX_ERROR: {
        "ja": "Mermaid構文エラーが検出されました",
        "en": "Mermaid syntax error detected",
    },
    ErrorCode.VALIDATION_INVALID_TYPE: {
        "ja": "無効な図タイプです",
        "en": "Invalid diagram type",
    },
    ErrorCode.VALIDATION_UNBALANCED_BRACKETS: {
        "ja": "括弧の対応が不正です",
        "en": "Unbalanced brackets in diagram",
    },
    ErrorCode.VALIDATION_EMPTY_NODE: {
        "ja": "空のノードラベルが検出されました",
        "en": "Empty node label detected",
    },
    ErrorCode.SERVER_INTERNAL_ERROR: {
        "ja": "サーバー内部エラーが発生しました",
        "en": "Internal server error",
    },
    ErrorCode.SERVER_DATABASE_ERROR: {
        "ja": "データベースエラーが発生しました",
        "en": "Database error",
    },
    ErrorCode.RATE_LIMIT_EXCEEDED: {
        "ja": "リクエスト制限を超過しました。しばらく待ってから再試行してください",
        "en": "Rate limit exceeded. Please wait and try again",
    },
    ErrorCode.AUTOFIX_FAILED: {
        "ja": "自動修正に失敗しました",
        "en": "Autofix failed",
    },
    ErrorCode.AUTOFIX_MAX_ATTEMPTS: {
        "ja": "最大修正回数に達しました",
        "en": "Maximum fix attempts reached",
    },
}

# Retryable error codes
RETRYABLE_ERRORS: set[ErrorCode] = {
    ErrorCode.NETWORK_DISCONNECTED,
    ErrorCode.NETWORK_TIMEOUT,
    ErrorCode.GENERATION_TIMEOUT,
    ErrorCode.RATE_LIMIT_EXCEEDED,
    ErrorCode.SERVER_INTERNAL_ERROR,
}


def get_error_category(code: ErrorCode) -> ErrorCategory:
    """Get the category for an error code."""
    prefix = code.split("_")[0]
    category_map = {
        "NETWORK": ErrorCategory.NETWORK,
        "GENERATION": ErrorCategory.GENERATION,
        "VALIDATION": ErrorCategory.VALIDATION,
        "SERVER": ErrorCategory.SERVER,
        "RATE": ErrorCategory.RATE_LIMIT,
        "AUTOFIX": ErrorCategory.AUTOFIX,
    }
    return category_map.get(prefix, ErrorCategory.SERVER)


def get_error_message(code: ErrorCode, lang: str = "ja") -> str:
    """Get localized error message for an error code."""
    messages = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.SERVER_INTERNAL_ERROR])
    return messages.get(lang, messages["en"])


def is_retryable(code: ErrorCode) -> bool:
    """Check if an error is retryable."""
    return code in RETRYABLE_ERRORS
