"""Domain errors raised by the analysis pipeline."""

from __future__ import annotations


class RagaratorError(Exception):
    """Base error with a stable machine-readable code."""

    def __init__(self, message: str, code: str = "RAGARATOR_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class UnsupportedFileError(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="UNSUPPORTED_FILE")


class EmptyDocumentError(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="EMPTY_DOCUMENT")


class DocumentTooSmallError(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="DOCUMENT_TOO_SMALL")


class DocumentTooLargeError(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="DOCUMENT_TOO_LARGE")


class FileNotFoundError_(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="FILE_NOT_FOUND")


class FileTooLargeError(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="FILE_TOO_LARGE")


class ExtractionError(RagaratorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="EXTRACTION_FAILED")
