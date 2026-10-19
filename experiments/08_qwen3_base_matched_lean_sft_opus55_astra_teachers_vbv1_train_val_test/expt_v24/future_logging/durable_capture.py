"""Durable compiler streams without another process or a different timeout rule.

The native subprocess still executes through subprocess.run. Streams go directly
to persistent files; its normal captured return/timeout interface is reconstructed
for the unchanged verifier. This explicitly changes PIPE transport to regular
files. It never changes command arguments, timeout, exit code or proof policy.
"""
from __future__ import annotations
import builtins
import hashlib
import io
import json
import locale
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import types

REAL_RUN = subprocess.run


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def clone(function, **globals_override):
    namespace = dict(function.__globals__, **globals_override)
    result = types.FunctionType(function.__code__, namespace, function.__name__,
                                function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


class DurableCapture:
    def __init__(self, root, compiler, context=None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        compiler = Path(compiler).resolve()
        self.context = dict(context or {})
        self.compiler = dict(path=str(compiler), sha256=sha(compiler))
        self.compiler['version'] = REAL_RUN([str(compiler), '--version'], capture_output=True,
            text=True, timeout=10, check=False).stdout.strip()

    def __getattr__(self, name):
        return getattr(subprocess, name)

    def run(self, *args, **kwargs):
        command = args[0] if len(args) == 1 else kwargs.get('args')
        if isinstance(command, (list, tuple)) and list(command[:3]) == ['lake', 'env', 'lean']:
            if args:
                return self.run_logged(command, **kwargs)
            options = dict(kwargs)
            del options['args']
            return self.run_logged(command, **options)
        return REAL_RUN(*args, **kwargs)

    def run_logged(self, command, **kwargs):
        # These are the exact two frozen verifier call forms. Refuse accidental
        # future semantic changes instead of silently failing to record them.
        if kwargs.get('capture_output') is not True or kwargs.get('check', False):
            raise ValueError('Logged verifier calls require capture_output=True and check=False')
        if any(key in kwargs for key in ('input', 'stdout', 'stderr', 'shell')):
            raise ValueError('Unexpected frozen verifier subprocess options')
        command = list(command)
        folder = Path(tempfile.mkdtemp(prefix=f'call_{os.getpid()}_', dir=self.root))
        cwd = Path(kwargs.get('cwd') or os.getcwd()).resolve()
        environment = kwargs.get('env') or os.environ
        executable = shutil.which(str(command[0]), path=environment.get('PATH'))
        sources, setups = [], []
        for argument in command[1:]:
            path = Path(argument[8:]) if str(argument).startswith('--setup=') else Path(str(argument))
            if not path.is_absolute():
                path = cwd/path
            if path.is_file() and str(argument).endswith('.lean'):
                destination = folder/f'source_{len(sources)}.lean'
                destination.write_bytes(path.read_bytes())
                sources.append(dict(path=str(path.resolve()), sha256=sha(destination), snapshot=destination.name))
            elif path.is_file() and str(argument).startswith('--setup='):
                destination = folder/f'setup_{len(setups)}.json'
                destination.write_bytes(path.read_bytes())
                setups.append(dict(path=str(path.resolve()), sha256=sha(destination), snapshot=destination.name))
        stage = ('kernel_compile' if '-o' in command else 'kernel_inspect') if setups else 'initial_compile'
        metadata = dict(state='RUNNING', stage=stage, command=command, cwd=str(cwd),
            timeout_seconds=kwargs.get('timeout'), started_unix=time.time(), parent_pid=os.getpid(),
            compiler=self.compiler, command_executable=dict(path=executable, sha256=sha(executable)) if executable else None,
            sources=sources, setups=setups, context=self.context,
            stream_transport='durable regular files; caller capture interface reconstructed',
            wrapper_source_sha256=sha(__file__), exit_code=None, timed_out=False)
        stdout_path, stderr_path = folder/'stdout.log', folder/'stderr.log'
        forward = dict(kwargs)
        del forward['capture_output']

        def finish(state, code=None, error=None):
            metadata.update(state=state, exit_code=code, ended_unix=time.time(), error=error,
                stdout_sha256=sha(stdout_path), stderr_sha256=sha(stderr_path),
                stdout_bytes=stdout_path.stat().st_size, stderr_bytes=stderr_path.stat().st_size)
            atomic(folder/'execution.json', metadata)

        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            atomic(folder/'execution.json', metadata)
            try:
                completed = REAL_RUN(command, stdout=stdout, stderr=stderr, **forward)
            except subprocess.TimeoutExpired as exc:
                # run() has already killed and waited for the same native child.
                # communicate() with redirected files forwards a slightly
                # reduced remaining wait; expose the caller's original timeout,
                # matching the original captured-PIPE exception interface.
                exc.timeout = kwargs.get('timeout')
                stdout.flush(); stderr.flush()
                os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
                exc.output = stdout_path.read_bytes() or None
                exc.stderr = stderr_path.read_bytes() or None
                metadata['timed_out'] = True
                finish('TIMEOUT', error=type(exc).__name__)
                raise
            except BaseException as exc:
                stdout.flush(); stderr.flush()
                os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
                finish('RAISED', error=type(exc).__name__+': '+str(exc))
                raise
            stdout.flush(); stderr.flush()
            os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
            finish('COMPLETE', completed.returncode)
        text_mode = bool(kwargs.get('text') or kwargs.get('universal_newlines') or kwargs.get('encoding') or kwargs.get('errors'))

        def captured(path):
            value = path.read_bytes()
            if not text_mode:
                return value
            with io.TextIOWrapper(io.BytesIO(value), encoding=kwargs.get('encoding') or locale.getpreferredencoding(False),
                                  errors=kwargs.get('errors') or 'strict', newline=None) as stream:
                return stream.read()
        return subprocess.CompletedProcess(completed.args, completed.returncode,
            captured(stdout_path), captured(stderr_path))


def instrument_scorer(scorer, capture):
    """Clone original function bytecode into private logging globals only."""
    original_compile = scorer.compile_lean_file
    original_import = builtins.__import__

    def importing(name, *args, **kwargs):
        return capture if name == 'subprocess' else original_import(name, *args, **kwargs)
    private_builtins = dict(vars(builtins), __import__=importing)
    logged_compile = clone(original_compile, __builtins__=private_builtins)
    kernel = scorer.kernel_axioms
    logged_probe = clone(kernel.run_probe, subprocess=capture)
    logged_check = clone(kernel.check_file, run_probe=logged_probe)
    private_kernel = types.SimpleNamespace(**vars(kernel))
    private_kernel.check_file = logged_check
    private_kernel.run_probe = logged_probe
    assert logged_compile.__code__ is original_compile.__code__
    assert logged_probe.__code__ is kernel.run_probe.__code__
    assert logged_check.__code__ is kernel.check_file.__code__
    scorer.compile_lean_file = logged_compile
    scorer.kernel_axioms = private_kernel
    return dict(compile_bytecode_unchanged=True, kernel_probe_bytecode_unchanged=True,
                kernel_check_bytecode_unchanged=True, original_compile=original_compile,
                original_kernel=kernel)
