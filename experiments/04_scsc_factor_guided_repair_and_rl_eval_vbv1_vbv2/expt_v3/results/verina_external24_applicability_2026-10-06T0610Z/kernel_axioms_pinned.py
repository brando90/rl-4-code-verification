#!/usr/bin/env python3
# TLDR: IC_pp counts every named source theorem/lemma whose kernel axiom cone is allowed.
"""Check the kernel dependency cone, including sorry hidden behind helpers.

The denominator includes named ``theorem`` and ``lemma`` declarations, with any
visibility modifier. Source tokens supply locations; Lean's declaration selection
ranges link them to exact kernel constants, including private and qualified names.
Examples and generated equation/proof helpers have no matching source declaration.
The legacy theorem regex is used only for historical diagnostics, never resolution.

Only propext, Classical.choice and Quot.sound are allowed by default. A complete,
randomly framed kernel dump AND process exit zero AND no Lean errors are required.
Unknown declarations fail closed. This is a proof dependency check, not an OS
sandbox against arbitrary executable Lean metaprograms.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional, Pattern

KERNEL_CHECK_ID = "kernel_axioms_v4_2026-09-09"
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
NATIVE_DECIDE_AXIOMS = frozenset({"Lean.ofReduceBool", "Lean.ofReduceNat", "Lean.trustCompiler"})
CATEGORIES = ("honest", "sorryAx", "native_decide", "declared_axiom", "unknown")
# Archived scorer regex: diagnostics only. It deliberately misses lemma/private.
DEFAULT_THEOREM_RE = re.compile(
    r"^[ \t]*(?:noncomputable\s+)?(?:@\[.*?\]\s*)?theorem\s+(\w+)", re.MULTILINE)
_IDENT_PART = r"(?:«[^»]*»|[A-Za-z_\u0080-\U0010ffff][\w'!?\u0080-\U0010ffff]*)"
IDENT_RE = re.compile(rf"{_IDENT_PART}(?:\.{_IDENT_PART})*")
ERROR_LINE_RE = re.compile(r"^(.*?):(\d+):(\d+): error: (.*)$", re.MULTILINE)
RAW_STRING_RE = re.compile(r'r(#{0,})"')
CHAR_RE = re.compile(r"'(?:\\.|[^'\\\n])'")


def _block_end(src: str, i: int) -> int:
    depth, i = 1, i + 2
    while i < len(src) and depth:
        if src.startswith("/-", i):
            depth, i = depth + 1, i + 2
        elif src.startswith("-/", i):
            depth, i = depth - 1, i + 2
        else:
            i += 1
    return i


def _string_end(src: str, i: int) -> int:
    """Skip a string, including strings inside interpolation expressions."""
    interpolated = i > 0 and src[i - 1] == "!"
    i += 1
    while i < len(src):
        if src[i] == "\\":
            i += 2
        elif src[i] == '"':
            return i + 1
        elif interpolated and src.startswith("{{", i):
            i += 2
        elif interpolated and src[i] == "{":
            depth, i = 1, i + 1
            while i < len(src) and depth:
                if src.startswith("/-", i):
                    i = _block_end(src, i)
                elif src.startswith("--", i):
                    end = src.find("\n", i)
                    i = len(src) if end < 0 else end
                elif (raw := RAW_STRING_RE.match(src, i)):
                    stop = '"' + raw.group(1)
                    end = src.find(stop, raw.end())
                    i = len(src) if end < 0 else end + len(stop)
                elif src[i] == '"':
                    i = _string_end(src, i)
                elif src[i] == "«":
                    end = src.find("»", i + 1)
                    i = len(src) if end < 0 else end + 1
                elif src[i] == "'" and (char := CHAR_RE.match(src, i)):
                    i = char.end()
                else:
                    depth += (src[i] == "{") - (src[i] == "}")
                    i += 1
        else:
            i += 1
    return min(i, len(src))


def strip_comments(src: str, *, keep_literals: bool = False) -> str:
    """Mask comments and string literals, preserving codepoint positions/newlines.

    Set ``keep_literals`` to remove only comments when rendering source context.
    Quoted identifiers are retained as atomic tokens by ``_tokens``. Ordinary,
    interpolated and raw strings are skipped, so comment delimiters inside them
    never hide following declarations. Character literals cannot open comments.
    """
    out = list(src)
    i, n = 0, len(src)

    def blank(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        start = i
        if src.startswith("--", i):
            i = src.find("\n", i)
            i = n if i < 0 else i
        elif src.startswith("/-", i):
            i = _block_end(src, i)
        elif src[i] == "«":
            end = src.find("»", i + 1)
            i = n if end < 0 else end + 1
            continue
        elif (raw := RAW_STRING_RE.match(src, i)):
            stop = '"' + raw.group(1)
            end = src.find(stop, raw.end())
            i = n if end < 0 else end + len(stop)
            if keep_literals:
                continue
        elif src[i] == '"':
            i = _string_end(src, i)
            if keep_literals:
                continue
        elif src[i] == "'" and (char := CHAR_RE.match(src, i)):
            i = char.end()
            if keep_literals:
                continue
        else:
            i += 1
            continue
        blank(start, i)
    return "".join(out)


def _tokens(src: str):
    masked = strip_comments(src)
    i = 0
    quote_depth = 0
    while i < len(masked):
        # Syntax quotations describe generated commands, not stated declarations.
        if masked.startswith("`(", i):
            quote_depth += 1
            i += 2
            continue
        if quote_depth:
            if masked[i] == "(":
                quote_depth += 1
            elif masked[i] == ")":
                quote_depth -= 1
            i += 1
            continue
        ident = IDENT_RE.match(masked, i)
        if ident:
            yield ident.group(), i, ident.end()
            i = ident.end()
        else:
            if not masked[i].isspace():
                yield masked[i], i, i + 1
            i += 1


@dataclass
class StatedTheorem:
    name: str
    short: str
    line: int
    column: int
    offset: int
    declaration: str
    prefix: str = ""  # populated from kernel data where useful, never guessed
    phantom: bool = False
    full_name: Optional[str] = None
    kind: Optional[str] = None
    axioms: list[str] = field(default_factory=list)
    category: str = "unknown"
    resolution: str = "none"
    regex_sorry: Optional[bool] = None

    @property
    def wanted(self) -> str:
        return self.name

    @property
    def kernel_honest(self) -> bool:
        return self.category == "honest"


def stated_theorems(src: str, theorem_re: Pattern[str] = DEFAULT_THEOREM_RE) -> list[StatedTheorem]:
    """All literal named theorem/lemma declarations, independent of historical regex."""
    tokens = list(_tokens(src))
    result = []
    for (word, _, _), (name, start, _) in zip(tokens, tokens[1:]):
        if word not in ("theorem", "lemma") or IDENT_RE.fullmatch(name) is None:
            continue
        result.append(StatedTheorem(
            name=name, short=name, line=src.count("\n", 0, start) + 1,
            column=start - (src.rfind("\n", 0, start) + 1), offset=start,
            declaration=word))
    return result


# JSON protects quoted identifiers containing punctuation/newlines. Selection
# ranges use Lean.Position's codepoint columns (not its UTF-16 LSP columns).
PROBE_EVAL = r'''
run_cmd do
  let env ← Lean.getEnv
  let target := Lean.Name.fromJson? (Lean.Json.str __MODULE_JSON__)
  let .ok target := target | throwError "invalid target module"
  let some idx := env.getModuleIdx? target | throwError "target module missing"
  let mut out : Array String := #[]
  for ci in env.header.moduleData[idx]!.constants do
    let n := ci.name
    let kind := match ci with
      | .thmInfo _ => "theorem"
      | .axiomInfo _ => "axiom"
      | _ => "other"
    if kind != "other" then
      let axs ← Lean.collectAxioms n
      let r ← Lean.findDeclarationRangesCore? n
      let row := Lean.Json.mkObj [
        ("name", Lean.toJson n.toString),
        ("kind", Lean.toJson kind),
        ("axioms", Lean.toJson (axs.map (·.toString))),
        ("line", Lean.toJson (r.map (·.selectionRange.pos.line))),
        ("column", Lean.toJson (r.map (·.selectionRange.pos.column))),
        ("range_line", Lean.toJson (r.map (·.range.pos.line))),
        ("range_column", Lean.toJson (r.map (·.range.pos.column)))]
      out := out.push row.compress
  IO.println "__MARKER__:BEGIN"
  for row in out.qsort (· < ·) do
    IO.println ("__MARKER__:ROW " ++ row)
  IO.println ("__MARKER__:END " ++ toString out.size)
'''


def build_probe(module_name: str, marker: str) -> str:
    """Inspect a compiled module. The original source is never spliced into this file."""
    return ("import Lean\nimport " + module_name + "\n" + PROBE_EVAL
            .replace("__MARKER__", marker)
            .replace("__MODULE_JSON__", json.dumps(module_name, ensure_ascii=False)))


@dataclass
class ProbeExecution:
    rc: int
    stdout: str
    stderr: str
    compile_rc: int
    inspect_rc: Optional[int]
    source_sha256: str
    compiled_module_sha256: Optional[str]
    evidence_dir: Optional[str]
    compiled_module: str


def _module_name(path: Path, lake_dir: Path) -> str:
    # Match Lean's module identity, including digit-prefixed or dotted path parts.
    try:
        relative = path.resolve().relative_to(lake_dir.resolve())
    except ValueError:
        return "_stdin"
    parts = relative.with_suffix("").parts
    if any("«" in part or "»" in part or "\n" in part or "\r" in part for part in parts):
        raise ValueError("module path cannot be represented as a Lean identifier")
    return ".".join(part if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", part)
                    else "«" + part + "»" for part in parts)


def _setup(name: str, import_arts: Optional[dict] = None) -> dict:
    # Omit `imports?`: Lean reads the original source header unchanged. Only the
    # baseline module name is fixed, because -o otherwise rejects external paths.
    return dict(name=name, isModule=False, plugins=[], dynlibs=[], options={},
                importArts=import_arts or {})


def run_probe(lean_path: str, lake_dir: str, stated: list[StatedTheorem], marker: str,
              timeout: int = 900, keep_dir: Optional[str] = None) -> ProbeExecution:
    original = Path(lean_path).resolve()
    source_sha = hashlib.sha256(original.read_bytes()).hexdigest()
    module_name = _module_name(original, Path(lake_dir))
    if keep_dir is not None:
        Path(keep_dir).mkdir(parents=True, exist_ok=True)
    # Keep-mode uses its own unique directory even when files have the same stem.
    directory = Path(tempfile.mkdtemp(prefix="vbax_", dir=keep_dir)).resolve()
    compiled = directory / "original.olean"
    compile_setup = directory / "compile_setup.json"
    compile_setup.write_text(json.dumps(_setup(module_name)), encoding="utf-8")
    deadline = time.monotonic() + timeout

    def execute(stage: str, args: list[str]) -> tuple[int, str, str]:
        command = ["lake", "env", "lean", *args]
        try:
            r = subprocess.run(command, cwd=str(Path(lake_dir).resolve()), capture_output=True,
                               text=True, timeout=max(0.01, deadline - time.monotonic()), check=False)
            result = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
            result = 124, decoded(exc.stdout), decoded(exc.stderr) + "\ntimeout"
        except OSError as exc:
            result = 127, "", str(exc)
        (directory / (stage + "_stdout.log")).write_text(result[1], encoding="utf-8")
        (directory / (stage + "_stderr.log")).write_text(result[2], encoding="utf-8")
        (directory / (stage + "_exit_code.txt")).write_text(str(result[0]) + "\n")
        (directory / (stage + "_command.json")).write_text(json.dumps(command), encoding="utf-8")
        return result

    compile_rc, compile_out, compile_err = execute("compile", ["--setup=" + str(compile_setup),
        "-o", str(compiled), "-i", str(directory / "original.ilean"), str(original)])
    inspect_rc, inspect_out, inspect_err = None, "", ""
    if compile_rc == 0 and compiled.is_file():
        parts = [str(compiled)]
        for suffix in (".server", ".private"):
            if Path(str(compiled) + suffix).is_file():
                parts.append(str(compiled) + suffix)
        inspector = directory / "Inspector.lean"
        inspector.write_text(build_probe(module_name, marker), encoding="utf-8")
        inspect_setup = directory / "inspect_setup.json"
        inspect_setup.write_text(json.dumps(_setup("VBAXInspector", {module_name: parts})), encoding="utf-8")
        inspect_rc, inspect_out, inspect_err = execute("inspect", ["--setup=" + str(inspect_setup), str(inspector)])
    rc = compile_rc or (inspect_rc if inspect_rc is not None else 125)
    if hashlib.sha256(original.read_bytes()).hexdigest() != source_sha:
        rc = 125
        compile_err += "\nsource changed during kernel check"
    stdout = compile_out + "\n" + inspect_out
    stderr = compile_err + "\n" + inspect_err
    result = ProbeExecution(rc, stdout, stderr, compile_rc, inspect_rc, source_sha,
                            hashlib.sha256(compiled.read_bytes()).hexdigest() if compiled.is_file() else None,
                            str(directory) if keep_dir is not None else None, module_name)
    (directory / "stdout.log").write_text(stdout, encoding="utf-8")
    (directory / "stderr.log").write_text(stderr, encoding="utf-8")
    (directory / "exit_code.txt").write_text(str(rc) + "\n")
    (directory / "execution.json").write_text(json.dumps(asdict(result)), encoding="utf-8")
    if keep_dir is None:
        shutil.rmtree(directory)
    return result


@dataclass
class ProbeOutput:
    dump: dict[str, dict]
    complete: bool
    errors: list[tuple[str, int, str]]
    protocol_errors: list[str]


def parse_probe_output(text: str, marker: str) -> ProbeOutput:
    dump = {}
    begun = ended = False
    protocol_errors = []
    for line in text.splitlines():
        if not line.startswith(marker + ":"):
            continue
        payload = line[len(marker) + 1:]
        if payload == "BEGIN" and not begun and not ended:
            begun = True
        elif payload.startswith("ROW ") and begun and not ended:
            try:
                row = json.loads(payload[4:])
                assert isinstance(row, dict) and isinstance(row["name"], str)
                assert row["kind"] in ("theorem", "axiom")
                assert isinstance(row["axioms"], list) and all(isinstance(a, str) for a in row["axioms"])
                assert all(row[k] is None or type(row[k]) is int for k in ("line", "column"))
                assert row["name"] not in dump
                dump[row["name"]] = row
            except (ValueError, KeyError, TypeError, AssertionError):
                protocol_errors.append("malformed or duplicate kernel row")
        elif payload.startswith("END ") and begun and not ended:
            ended = True
            if payload[4:] != str(len(dump)):
                protocol_errors.append("kernel row count mismatch")
        else:
            protocol_errors.append("unexpected kernel framing")
    errors = [(m.group(1), int(m.group(2)), m.group(4)) for m in ERROR_LINE_RE.finditer(text)]
    return ProbeOutput(dump, begun and ended and not protocol_errors, errors, protocol_errors)


def classify(axioms: list[str], allow_native_decide: bool = False) -> str:
    axs = set(axioms)
    if "sorryAx" in axs:
        return "sorryAx"
    if axs - ALLOWED_AXIOMS - NATIVE_DECIDE_AXIOMS:
        return "declared_axiom"
    if axs & NATIVE_DECIDE_AXIOMS:
        return "honest" if allow_native_decide else "native_decide"
    return "honest"


@dataclass
class KernelAxiomReport:
    kernel_check: str
    path: str
    probe_ok: bool
    probe_rc: int
    allow_native_decide: bool
    n_stated: int
    n_phantom: int  # legacy regex matches in comments/strings; diagnostics only
    n_theorems: int
    n_honest: int
    n_sorry_ax: int
    n_native_decide: int
    n_declared_axiom: int
    n_unknown: int
    ic_pp: float
    theorems: list[dict]
    declared_axioms: list[str]
    extra_theorems: list[dict]  # generated helpers, excluded from denominator
    probe_errors: list[dict]
    stderr_tail: str = ""
    probe_output_sha256: str = ""
    n_legacy_theorems: int = 0
    compile_rc: Optional[int] = None
    inspect_rc: Optional[int] = None
    source_sha256: str = ""
    compiled_module_sha256: Optional[str] = None
    evidence_dir: Optional[str] = None
    compiled_module: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


ProbeRunner = Callable[[str, str, list[StatedTheorem], str], tuple[int, str, str]]


def _source_declaration(src: str, row: dict) -> Optional[StatedTheorem]:
    """Read a theorem's tiny declaration header from its kernel source range.

    This independently recovers source declarations even if a lexical masking
    bug earlier in the file hid them. Generated helpers have no such header.
    """
    if row.get("range_line") is None or row.get("line") is None:
        return None
    lines = src.splitlines(keepends=True)

    def offset(line, column):
        if type(line) is not int or type(column) is not int or not 1 <= line <= len(lines):
            return None
        if not 0 <= column <= len(lines[line - 1].rstrip("\r\n")):
            return None
        return sum(map(len, lines[:line - 1])) + column

    begin = offset(row["range_line"], row.get("range_column"))
    start = offset(row["line"], row.get("column"))
    if begin is None or start is None or begin > start:
        return None
    header = list(_tokens(src[begin:start]))
    ident = IDENT_RE.match(src, start)
    if not header or header[-1][0] not in ("theorem", "lemma") or ident is None:
        return None
    return StatedTheorem(ident.group(), ident.group(), row["line"], row["column"], start, header[-1][0])


def check_file(lean_path: str, lake_dir: str, theorem_re: Pattern[str] = DEFAULT_THEOREM_RE,
               timeout: int = 900, allow_native_decide: bool = False,
               sorry_re: Optional[Pattern[str]] = None, keep_dir: Optional[str] = None,
               runner: Optional[ProbeRunner] = None) -> KernelAxiomReport:
    """Recompile a file and classify every source theorem; any failed probe scores zero.

    A test runner receives (path, lake_dir, stated, random_marker). The marker is
    generated per invocation; old/unframed ``#print`` output cannot supply honesty.
    """
    src = Path(lean_path).read_bytes().decode("utf-8")
    stated = stated_theorems(src)
    legacy = list(theorem_re.finditer(src))
    masked = strip_comments(src)
    n_phantom = sum(masked[m.start(1):m.end(1)] != m.group(1) for m in legacy)
    marker = "VBAX_" + secrets.token_hex(16)
    if runner is None:
        execution = run_probe(lean_path, lake_dir, stated, marker, timeout=timeout, keep_dir=keep_dir)
        rc, out, err = execution.rc, execution.stdout, execution.stderr
        if execution.source_sha256 != hashlib.sha256(src.encode()).hexdigest():
            rc = 125
            err += "\nsource changed between declaration scan and compilation"
    else:
        rc, out, err = runner(lean_path, lake_dir, stated, marker)
        execution = ProbeExecution(rc, out, err, rc, rc, hashlib.sha256(src.encode()).hexdigest(), None, None, "test")
    parsed = parse_probe_output(out + "\n" + err, marker)
    probe_ok = rc == 0 and parsed.complete and not parsed.errors
    if probe_ok:
        candidates = {t.offset: t for t in stated}
        for row in parsed.dump.values():
            if row["kind"] == "theorem" and (t := _source_declaration(src, row)) is not None:
                candidates.setdefault(t.offset, t)
        stated = sorted(candidates.values(), key=lambda t: t.offset)
    if sorry_re is not None:
        old_verdicts = {
            m.start(1): bool(sorry_re.search(src[m.start():legacy[i+1].start() if i+1 < len(legacy) else len(src)]))
            for i, m in enumerate(legacy)
        }
        for t in stated:
            t.regex_sorry = old_verdicts.get(t.offset)
    by_position = {}
    for name, row in parsed.dump.items():
        if row["kind"] == "theorem" and row["line"] is not None:
            by_position.setdefault((row["line"], row["column"]), []).append(name)
    for t in stated:
        if not probe_ok:
            t.resolution = "probe_failed"
            continue
        matches = by_position.get((t.line, t.column), [])
        if len(matches) != 1:
            t.resolution = "ambiguous_source_position" if matches else "missing_source_position"
            continue
        t.full_name = matches[0]
        row = parsed.dump[t.full_name]
        t.kind = row["kind"]
        t.axioms = sorted(row["axioms"])
        t.category = classify(t.axioms, allow_native_decide)
        t.resolution = "source_position"
    matched = {t.full_name for t in stated if t.full_name}
    extra = [{"full_name": name, "axioms": row["axioms"], "category": classify(row["axioms"], allow_native_decide)}
             for name, row in sorted(parsed.dump.items()) if row["kind"] == "theorem" and name not in matched]
    counts = {cat: sum(t.category == cat for t in stated) for cat in CATEGORIES}
    errors = [{"line": line, "file": file, "msg": message,
               "in_original": file == str(Path(lean_path).resolve())}
              for file, line, message in parsed.errors]
    errors += [{"line": None, "msg": message, "in_original": False} for message in parsed.protocol_errors]
    return KernelAxiomReport(
        kernel_check=KERNEL_CHECK_ID, path=str(lean_path), probe_ok=probe_ok, probe_rc=rc,
        allow_native_decide=allow_native_decide, n_stated=len(stated), n_phantom=n_phantom,
        n_theorems=len(stated), n_honest=counts["honest"], n_sorry_ax=counts["sorryAx"],
        n_native_decide=counts["native_decide"], n_declared_axiom=counts["declared_axiom"],
        n_unknown=counts["unknown"], ic_pp=counts["honest"] / len(stated) if stated else 0.0,
        theorems=[dict(asdict(t), kernel_honest=t.kernel_honest) for t in stated],
        declared_axioms=sorted(n for n, row in parsed.dump.items() if row["kind"] == "axiom"),
        extra_theorems=extra, probe_errors=errors, stderr_tail=err[-2000:],
        probe_output_sha256=hashlib.sha256((out + "\n" + err).encode()).hexdigest(),
        n_legacy_theorems=len(legacy), compile_rc=execution.compile_rc, inspect_rc=execution.inspect_rc,
        source_sha256=execution.source_sha256, compiled_module_sha256=execution.compiled_module_sha256,
        evidence_dir=execution.evidence_dir, compiled_module=execution.compiled_module)


def valid_report(data: dict) -> bool:
    """Validate reusable successful evidence, recomputing every theorem category.

    File hashes are format-checked here; a caller that retains raw evidence must
    also compare them against the original source and compiled artifact bytes.
    """
    try:
        if (data["kernel_check"] != KERNEL_CHECK_ID or data["probe_ok"] is not True
                or any(type(data[key]) is not int or data[key] != 0
                       for key in ("probe_rc", "compile_rc", "inspect_rc", "n_unknown"))
                or data["probe_errors"] or type(data["allow_native_decide"]) is not bool):
            return False
        for key in ("source_sha256", "compiled_module_sha256"):
            if not isinstance(data[key], str) or re.fullmatch(r"[0-9a-f]{64}", data[key]) is None:
                return False
        ts = data["theorems"]
        if not isinstance(ts, list) or any(type(data[key]) is not int or data[key] != len(ts)
                                          for key in ("n_theorems", "n_stated")):
            return False
        counts = dict.fromkeys(CATEGORIES, 0)
        names = set()
        for theorem in ts:
            name, axioms = theorem["full_name"], theorem["axioms"]
            if (not isinstance(name, str) or not name or name in names or theorem["phantom"]
                    or theorem["resolution"] != "source_position" or not isinstance(axioms, list)
                    or not all(isinstance(a, str) for a in axioms)):
                return False
            names.add(name)
            category = classify(axioms, data["allow_native_decide"])
            if theorem["category"] != category or theorem["kernel_honest"] is not (category == "honest"):
                return False
            counts[category] += 1
        for key, category in (("n_honest", "honest"), ("n_sorry_ax", "sorryAx"),
                              ("n_native_decide", "native_decide"), ("n_declared_axiom", "declared_axiom")):
            if type(data[key]) is not int or data[key] != counts[category]:
                return False
        expected = counts["honest"] / len(ts) if ts else 0.0
        return isinstance(data["ic_pp"], (int, float)) and abs(data["ic_pp"] - expected) < 1e-12
    except (KeyError, TypeError, ValueError):
        return False


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Kernel axiom check for Lean files (JSON output).")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lake-dir", default=str(Path(__file__).resolve().parents[2] / "veribench_dataset/lean_src"))
    ap.add_argument("--allow-native-decide", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--keep-dir")
    args = ap.parse_args(argv)
    failed = False
    for path in args.files:
        report = check_file(path, args.lake_dir, allow_native_decide=args.allow_native_decide,
                            timeout=args.timeout, keep_dir=args.keep_dir)
        print(json.dumps(report.to_dict(), indent=1))
        failed |= not report.probe_ok
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
