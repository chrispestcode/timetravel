from abc import ABC, abstractmethod
from typing import Self

class RecordInterface(ABC):
    
    @abstractmethod
    def copy(self) -> Self:
        pass