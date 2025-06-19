"""
Custom exception classes for standardized error handling.
"""
from typing import Dict, Any, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""
    
    # Authentication & Authorization
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Database Operations
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    DATABASE_ERROR = "DATABASE_ERROR"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    
    # Document Processing
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    OCR_PROCESSING_FAILED = "OCR_PROCESSING_FAILED"
    LLM_PROCESSING_FAILED = "LLM_PROCESSING_FAILED"
    INVALID_DOCUMENT_FORMAT = "INVALID_DOCUMENT_FORMAT"
    DOCUMENT_TOO_LARGE = "DOCUMENT_TOO_LARGE"
    
    # Business Logic
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # External Services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # General
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class MedicalAppException(Exception):
    """Base exception for all medical app related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.error_code.value,
            "message": self.message,
            "details": self.details
        }


class AuthenticationError(MedicalAppException):
    """Authentication related errors."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INVALID_TOKEN, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details, status_code=401)


class AuthorizationError(MedicalAppException):
    """Authorization related errors."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INSUFFICIENT_PERMISSIONS, details, status_code=403)


class ValidationError(MedicalAppException):
    """Input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, ErrorCode.VALIDATION_ERROR, error_details, status_code=400)


class ResourceNotFoundError(MedicalAppException):
    """Resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} with ID {resource_id} not found"
        error_details = details or {}
        error_details.update({"resource_type": resource_type, "resource_id": resource_id})
        super().__init__(message, ErrorCode.RESOURCE_NOT_FOUND, error_details, status_code=404)


class DuplicateResourceError(MedicalAppException):
    """Duplicate resource errors."""
    
    def __init__(self, resource_type: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if not message:
            message = f"Duplicate {resource_type} already exists"
        error_details = details or {}
        error_details["resource_type"] = resource_type
        super().__init__(message, ErrorCode.DUPLICATE_RESOURCE, error_details, status_code=409)


class DocumentProcessingError(MedicalAppException):
    """Document processing related errors."""
    
    def __init__(
        self, 
        message: str, 
        document_id: Optional[str] = None,
        processing_stage: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.DOCUMENT_PROCESSING_FAILED,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if document_id:
            error_details["document_id"] = document_id
        if processing_stage:
            error_details["processing_stage"] = processing_stage
        super().__init__(message, error_code, error_details, status_code=422)


class ExternalServiceError(MedicalAppException):
    """External service integration errors."""
    
    def __init__(
        self, 
        service_name: str, 
        message: str = None, 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 502
    ):
        if not message:
            message = f"Error communicating with {service_name}"
        error_details = details or {}
        error_details["service_name"] = service_name
        super().__init__(message, ErrorCode.EXTERNAL_SERVICE_ERROR, error_details, status_code)


class RateLimitError(MedicalAppException):
    """Rate limiting errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        super().__init__(message, ErrorCode.RATE_LIMIT_EXCEEDED, error_details, status_code=429)


class DatabaseError(MedicalAppException):
    """Database operation errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        super().__init__(message, ErrorCode.DATABASE_ERROR, error_details, status_code=500) 