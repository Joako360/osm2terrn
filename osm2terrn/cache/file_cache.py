"""Filesystem cache backend implementation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from osm2terrn.cache.backend import CacheBackend
from osm2terrn.cache.metadata import CacheMetadata


class FileCacheBackend(CacheBackend):
    """File-based cache backend.

    Layout:

    ``<root>/<namespace>/<key>.bin`` for payload and
    ``<root>/<namespace>/<key>.meta.json`` for metadata.
    """

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)

    @property
    def root_dir(self) -> Path:
        """Return filesystem root for this backend."""

        return self._root_dir

    def get(self, namespace: str, key: str) -> tuple[bytes, CacheMetadata] | None:
        data_path = self._data_path(namespace, key)
        meta_path = self._meta_path(namespace, key)
        if not data_path.exists() or not meta_path.exists():
            return None

        payload = data_path.read_bytes()
        raw_metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        metadata = CacheMetadata.from_dict(raw_metadata)
        if metadata.is_expired():
            self.remove(namespace, key)
            return None
        return payload, metadata

    def put(self, namespace: str, key: str, payload: bytes, metadata: CacheMetadata) -> None:
        data_path = self._data_path(namespace, key)
        meta_path = self._meta_path(namespace, key)
        data_path.parent.mkdir(parents=True, exist_ok=True)

        temp_data_path = data_path.with_suffix(".bin.tmp")
        temp_meta_path = meta_path.with_suffix(".json.tmp")
        temp_data_path.write_bytes(payload)
        temp_meta_path.write_text(
            json.dumps(metadata.to_dict(), ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_data_path.replace(data_path)
        temp_meta_path.replace(meta_path)

    def exists(self, namespace: str, key: str) -> bool:
        data_path = self._data_path(namespace, key)
        meta_path = self._meta_path(namespace, key)
        return data_path.exists() and meta_path.exists()

    def remove(self, namespace: str, key: str) -> bool:
        data_path = self._data_path(namespace, key)
        meta_path = self._meta_path(namespace, key)
        existed = False
        if data_path.exists():
            data_path.unlink()
            existed = True
        if meta_path.exists():
            meta_path.unlink()
            existed = True
        return existed

    def clear(self, namespace: str | None = None) -> None:
        if namespace is None:
            for child in self._root_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            return

        namespace_path = self._namespace_path(namespace)
        if namespace_path.exists():
            shutil.rmtree(namespace_path)

    def _namespace_path(self, namespace: str) -> Path:
        normalized_parts = [part for part in namespace.split("/") if part and part not in {".", ".."}]
        return self._root_dir.joinpath(*normalized_parts)

    def _data_path(self, namespace: str, key: str) -> Path:
        return self._namespace_path(namespace) / f"{key}.bin"

    def _meta_path(self, namespace: str, key: str) -> Path:
        return self._namespace_path(namespace) / f"{key}.meta.json"
