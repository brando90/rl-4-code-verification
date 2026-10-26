"""Keep Ray files in their owned run directory while binding Unix sockets through a short checked alias."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import socket
import stat

# The installed Ray session layout, conservatively allowing a ten-digit PID.
SESSION = 'session_9999-12-31_23-59-59_999999_2147483647'
SOCKET_SUFFIX = Path(SESSION)/'sockets/plasma_store'


@contextmanager
def short_directory(directory):
    """Never replace another path; retain run files and remove only our matching alias."""
    target = Path(directory).resolve()
    target.mkdir(parents=True, exist_ok=True)
    if target.stat().st_uid != os.getuid():
        raise ValueError('Ray directory is not owned by this execution user')
    token = hashlib.sha256(os.fsencode(target)).hexdigest()[:16]
    alias = Path('/tmp')/f'e13ray-{os.getuid()}-{token}'
    created = False
    try:
        alias.symlink_to(target, target_is_directory=True)
        created = True
    except FileExistsError:
        pass
    entry = alias.lstat()
    if (entry.st_uid != os.getuid() or not stat.S_ISLNK(entry.st_mode)
            or alias.readlink() != target):
        raise ValueError('Ray socket alias belongs to another path or owner')
    try:
        maximum = 103 if os.uname().sysname == 'Darwin' else 107
        if len(os.fsencode(alias/SOCKET_SUFFIX)) > maximum:
            raise OSError('short Ray alias still exceeds the Unix socket path limit')
        yield alias
    finally:
        if created and alias.is_symlink():
            current = alias.lstat()
            if (current.st_dev, current.st_ino) == (entry.st_dev, entry.st_ino):
                alias.unlink()


def check_socket(alias):
    """Bind a real worst-length socket, without constructing a model or accessing probe data."""
    alias = Path(alias)
    session = alias/SESSION
    session.mkdir(exist_ok=False)
    sockets = session/'sockets'
    path = sockets/'plasma_store'
    try:
        sockets.mkdir()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.bind(str(path))
        return {'status': 'PASS', 'scope': 'non-probe Unix socket infrastructure only',
                'socket_path_bytes': len(os.fsencode(path)),
                'limit_bytes': 103 if os.uname().sysname == 'Darwin' else 107,
                'model_calls': 0, 'admission_statistics_computed': False}
    finally:
        if path.exists(): path.unlink()
        if sockets.exists(): sockets.rmdir()
        session.rmdir()


def preflight(directory):
    with short_directory(directory) as alias:
        return check_socket(alias)
