from __future__ import annotations

from uuid import uuid4

from .base import CVStorage, StorageError, StoredObject


class MinioStorage(CVStorage):
    def __init__(self, bucket_name: str = 'swifthire-private') -> None:
        self.bucket_name = bucket_name
        self._objects: dict[str, bytes] = {}

    def save(self, file, content_type: str) -> StoredObject:
        data = file.read()
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)

        if len(data) == 0:
            raise StorageError('Uploaded CV is empty.')

        normalized_type = (content_type or 'application/pdf').lower()
        if normalized_type not in {'application/pdf', 'application/octet-stream'} and not normalized_type.endswith('/pdf'):
            raise StorageError('Please upload a PDF file under 10 MiB.')

        object_key = f'{uuid4()}.pdf'
        self._objects[object_key] = bytes(data)
        return StoredObject(
            object_key=object_key,
            content_type='application/pdf',
            size_bytes=len(data),
        )
