from entity.record import Record
from service.record import RecordService, ServiceError
from util.log import log_error


class InMemoryRecordService(RecordService):
    """In-memory implementation of RecordService backed by a plain dict.

    Example:
        service = InMemoryRecordService()
    """

    def __init__(self) -> None:
        self._data: dict[int, Record] = {}

    async def get_record(self, id: int) -> Record:
        record = self._data.get(id)
        if record is None:
            err = ServiceError.not_found()
            log_error(err)
            raise err
        return record.copy()  # copy so caller mutations don't affect stored record

    async def create_record(self, record: Record) -> None:
        if record.id <= 0:
            err = ServiceError.invalid_id()
            log_error(err)
            raise err

        if record.id in self._data:
            err = ServiceError.already_exists()
            log_error(err)
            raise err

        self._data[record.id] = record.copy()

    async def update_record(self, id: int, updates: dict[str, str | None]) -> Record:
        record = self._data.get(id)
        if record is None:
            err = ServiceError.not_found()
            log_error(err)
            raise err

        for key, value in updates.items():
            if value is None:  # deletion update
                record.data.pop(key, None)
            else:
                record.data[key] = value

        return record.copy()
