class ApplicationServiceError(Exception):
    """Base exception for application service layer errors."""
    pass

class EntityNotFoundError(ApplicationServiceError):
    """Raised when a requested entity does not exist."""
    pass

class EntityAlreadyExistsError(ApplicationServiceError):
    """Raised when attempting to create an entity that already exists."""
    pass

class ServiceValidationError(ApplicationServiceError):
    """Raised when application business validation fails."""
    pass
