from pydantic import BaseModel
from entity.record_interface import RecordInterface
from typing import Self

class Record(BaseModel, RecordInterface):
    """A stored record with an integer ID and a key-value data map.

    Example:
        record = Record(id=1, data={"key": "value"})
    """

    id: int
    data: dict[str, str] = {}

    def clone(self) -> Self:
        """Returns a deep copy so mutations don't affect the stored record."""
        return self.model_copy(deep=True)
    