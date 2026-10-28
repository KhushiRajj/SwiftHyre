from __future__ import annotations

from .minio import MinioStorage


class CloudinaryStorage(MinioStorage):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
