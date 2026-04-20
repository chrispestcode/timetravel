from pydantic import BaseModel


class Record(BaseModel):
    """A stored record with an integer ID and a key-value data map.

    Example:
        record = Record(id=1, data={"key": "value"})
    """

    id: int
    data: dict[str, str] = {}

    def copy(self) -> "Record":
        """Returns a deep copy so mutations don't affect the stored record."""
        return self.model_copy(deep=True)
    
    
    # TODO needs to be subclassed for various record versions