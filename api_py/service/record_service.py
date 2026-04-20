from abc import ABC, abstractmethod
from http import HTTPStatus

from entity.record import Record


class ServiceError(Exception):
    """Domain error carrying an HTTP status code and message.

    Example:
        raise ServiceError.not_found()
    """

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    @classmethod
    def not_found(cls) -> "ServiceError":
        return cls(code=HTTPStatus.NOT_FOUND, message="record with that id does not exist")

    @classmethod
    def invalid_id(cls) -> "ServiceError":
        return cls(code=HTTPStatus.BAD_REQUEST, message="record id must be > 0")

    @classmethod
    def already_exists(cls) -> "ServiceError":
        return cls(code=HTTPStatus.CONFLICT, message="record already exists")


class RecordService(ABC):
    """Implements methods to get, create, and update record data.

    Example:
        service: RecordService = SQLiteRecordService("timetravel.db")
    """

    @abstractmethod
    async def get_record(self, id: int) -> Record:
        """Retrieves a record by ID. Raises ServiceError if not found."""
        ...

    @abstractmethod
    async def create_record(self, record: Record) -> None:
        """Inserts a new record. Raises ServiceError if id <= 0 or already exists."""
        ...

    @abstractmethod
    async def update_record(self, id: int, updates: dict[str, str | None]) -> Record:
        """Updates record data. None values delete the key. Raises ServiceError if not found."""
        ...
