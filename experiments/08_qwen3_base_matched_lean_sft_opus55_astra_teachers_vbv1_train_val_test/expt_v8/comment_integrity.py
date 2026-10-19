"""Insert Lean line comments only at lexical boundaries and recover the original bytes exactly."""
from __future__ import annotations

import re


def safe_line_starts(source: str) -> set[int]:
    """Conservatively track nested comments, quoted strings and escaped identifiers."""
    safe = {1}
    line, i, depth = 1, 0, 0
    quoted = False
    escaped_ident = False
    line_comment = False
    while i < len(source):
        c, pair = source[i], source[i:i + 2]
        if c == '\n':
            line += 1
            line_comment = False
            if not depth and not quoted and not escaped_ident:
                safe.add(line)
            i += 1
        elif line_comment:
            i += 1
        elif depth:
            if pair == '/-':
                depth += 1
                i += 2
            elif pair == '-/':
                depth -= 1
                i += 2
            else:
                i += 1
        elif quoted:
            if c == '\\':
                if i + 1 < len(source) and source[i + 1] == '\n':
                    line += 1
                i += 2
            elif c == '"':
                quoted = False
                i += 1
            else:
                i += 1
        elif escaped_ident:
            escaped_ident = c != '»'
            i += 1
        elif pair == '--':
            line_comment = True
            i += 2
        elif pair == '/-':
            depth = 1
            i += 2
        elif c == '"':
            # Raw strings need delimiter-aware parsing; reject rather than guess.
            if re.search(r'\br#*$', source[max(0, i - 12):i]):
                raise ValueError('raw string needs a separate lexical check')
            quoted = True
            i += 1
        elif c == '«':
            escaped_ident = True
            i += 1
        elif c == "'" and i + 2 < len(source) and source[i + 2] == "'":
            i += 3  # Single-character literal; identifier primes are otherwise ordinary text.
        elif c == "'" and i + 3 < len(source) and source[i + 1] == '\\' and source[i + 3] == "'":
            i += 4
        else:
            i += 1
    if depth or quoted or escaped_ident:
        raise ValueError('unterminated lexical context')
    return safe


def insert_comments(source: str, comments: list[dict], *, require_sketch: bool = True, allow_existing_prefix: bool = False) -> str:
    lines = source.splitlines(keepends=True)
    safe = safe_line_starts(source)
    indexed: dict[int, list[str]] = {}
    if not isinstance(comments, list) or not comments:
        raise ValueError('missing comments')
    for comment in comments:
        if not isinstance(comment, dict) or set(comment) != {'before_line', 'text'}:
            raise ValueError('comment must have exactly before_line and text')
        n, text = comment['before_line'], comment['text']
        if type(n) is not int or not 1 <= n <= len(lines) or n not in safe:
            raise ValueError(f'unsafe insertion line {n}')
        if not isinstance(text, str) or not text.strip() or len(text) > 360:
            raise ValueError('empty or overlong comment')
        if not all(c.isprintable() for c in text) or any(x in text for x in ('/-', '-/')):
            raise ValueError('comment contains control characters or comment delimiters')
        text = text.strip()
        if text.startswith('--') and not allow_existing_prefix:
            raise ValueError('text must not include a comment prefix')
        indexed.setdefault(n, []).append(text)
    if require_sketch and (len(indexed.get(1, [])) < 2 or not indexed[1][0].startswith('Proof sketch:')):
        raise ValueError('need a top-of-file Proof sketch and at least two header lines')
    result, retained = [], []
    for n, line in enumerate(lines, 1):
        indent = re.match(r'[ \t]*', line).group()
        result.extend(indent + '-- ' + text + '\n' for text in indexed.get(n, []))
        result.append(line)
        retained.append(result[-1])
    if ''.join(retained) != source:
        raise ValueError('original source changed')
    annotated = ''.join(result)
    # Independently remove the known inserted positions, retaining pre-existing comments.
    actual = annotated.splitlines(keepends=True)
    recovered, pos = [], 0
    for n in range(1, len(lines) + 1):
        pos += len(indexed.get(n, []))
        recovered.append(actual[pos])
        pos += 1
    if pos != len(actual) or ''.join(recovered) != source:
        raise ValueError('insertion roundtrip changed source bytes')
    return annotated
