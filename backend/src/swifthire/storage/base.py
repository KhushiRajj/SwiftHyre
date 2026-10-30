from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO


@dataclass
class StoredObject:
    object_key: str
    content_type: str
    size_bytes: int

    def to_dict(self) -> dict:
        return {
            'object_key': self.object_key,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
        }


class StorageError(RuntimeError):
    pass


class CVStorage(ABC):
    @abstractmethod
    def save(self, file: BinaryIO, content_type: str) -> StoredObject:
        raise NotImplementedError
