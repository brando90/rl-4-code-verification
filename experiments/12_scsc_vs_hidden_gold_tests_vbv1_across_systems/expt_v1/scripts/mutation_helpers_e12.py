"""Find local implementation helpers reachable from tested definitions for the final deterministic mutation fallback."""
import re
from adapter_e12 import IDENT, TOP, declarations, strip_comments


def reachable_helpers(source, symbols):
    clean = strip_comments(source)
    clean = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: ' ' * len(m.group()), clean)
    defs, _ = declarations(source)
    by_name = {d['full_name']: d for d in defs}
    boundaries = [m.start() for m in TOP.finditer(clean)]
    roots = {s['full_name'] for s in symbols}
    reached = set(roots)
    pending = sorted(roots)
    while pending:
        name = pending.pop()
        d = by_name.get(name)
        if d is None:
            continue
        stop = min((i for i in boundaries if i > d['start']), default=len(clean))
        for token in IDENT.findall(clean[d['body_start']:stop]):
            # Resolve only exact qualified or same-namespace references to local definitions.
            target = token if token in by_name else '.'.join(filter(None, [d['namespace'], token]))
            if target in by_name and target not in reached:
                reached.add(target)
                pending.append(target)
    return [d for d in defs if d['full_name'] in reached - roots]
