from abc import ABC, abstractmethod
from enum import IntEnum

from entity.record import Record


class ServiceErrorCode(IntEnum):
    NOT_FOUND = 1
    ALREADY_EXISTS = 2
    INVALID_ID = 3


class ServiceError(Exception):
    """Domain error carrying a service-level error code and message.

    Example:
        raise ServiceError.not_found()
    """

    def __init__(self, code: ServiceErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    @classmethod
    def not_found(cls) -> "ServiceError":
        return cls(code=ServiceErrorCode.NOT_FOUND, message="record with that id does not exist")

    @classmethod
    def invalid_id(cls) -> "ServiceError":
        return cls(code=ServiceErrorCode.INVALID_ID, message="record id must be > 0")

    @classmethod
    def already_exists(cls) -> "ServiceError":
        return cls(code=ServiceErrorCode.ALREADY_EXISTS, message="record already exists")


class RecordService(ABC):
    """Implements methods to get, create, and update record data.

    Example:
        service: RecordService = SQLiteRecordService("timetravel.db")
    """

    @abstractmethod
    async def get_record(self, id: int) -> Record | None:
        """Retrieves a record by ID, or None if it does not exist."""
        ...

    @abstractmethod
    async def create_record(self, record: Record) -> Record:
        """Inserts a new record. Raises ServiceError if id <= 0 or already exists."""
        ...

    @abstractmethod
    async def update_record(self, id: int, updates: dict[str, str | None]) -> Record:
        """Updates record data. None values delete the key. Raises ServiceError if not found."""
        ...
