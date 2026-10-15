"""Persist anchor cell and lease metadata with file and parent-directory synchronization."""
from __future__ import annotations

import os
from pathlib import Path

from panel import write_new as original_write_new
from lease import atomic_json as original_atomic_json


def sync_directory(path):
    fd=os.open(Path(path),os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def mkdir(path):
    path=Path(path)
    if path.is_dir():return
    mkdir(path.parent)
    path.mkdir(exist_ok=True)
    sync_directory(path.parent)


def write_new(path,value):
    path=Path(path);mkdir(path.parent)
    original_write_new(path,value);sync_directory(path.parent)


def atomic_json(path,value):
    path=Path(path);mkdir(path.parent)
    original_atomic_json(path,value);sync_directory(path.parent)
