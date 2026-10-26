"""Freeze 500 elementary Python tasks with centrally defined semantics and deterministic test inputs."""
import ast
import hashlib
import json
import random
from pathlib import Path

FAMILIES = {
'natural_arithmetic': '''x + y|x * y|x ** 2|x ** 3|x + y + z|x * (y + z)|(x + y) * z|x * y + z|x + y * z|2 * x + y|x + 2 * y|x * x + y * y|(x + y) ** 2|x * (x + 1)|max(x - y, 0)|max(x - y - z, 0)|min(x + y, z)|max(x + y, z)|x + max(y - z, 0)|max(x - min(y, z), 0)''',
'integer_arithmetic': '''x + y|x - y|-x|x * y|abs(x)|x + y - z|x - (y - z)|-(x + y)|x * (y - z)|x * y - x * z|abs(x - y)|abs(x) + abs(y)|x * x|x ** 3|x * (y + 1)|x + (-y)|(-x) * (-y)|x - x * y|x * (1 - y)|x + y + z''',
'comparisons': '''x < y|x <= y|x == y|x != y|x > y|x >= y|x < y < z|x <= y <= z|x == y == z|x < y and y <= z|x <= y and y < z|x < y or x > z|x <= y or y <= x|x < y and y < x|x == y or y == z|x != y and y != z|x + y <= z|x - y < z|abs(x) <= y|x * x >= 0''',
'bounds_and_extrema': '''min(x, y)|max(x, y)|min(x, y, z)|max(x, y, z)|max(x, 0)|min(x, 0)|min(max(x, 0), n)|max(min(x, n), 0)|max(x, y) - min(x, y)|abs(x - y)|min(x + z, y + z)|max(x + z, y + z)|min(-x, -y)|max(-x, -y)|min(abs(x), abs(y))|max(abs(x), abs(y))|min(x, max(y, z))|max(x, min(y, z))|min(max(x, y), max(x, z))|max(min(x, y), min(x, z))''',
'parity': '''x % 2 == 0|x % 2 != 0|(x + y) % 2 == 0|(x + y) % 2 != 0|(x - y) % 2 == 0|(x * y) % 2 == 0|(x * y) % 2 != 0|(x * x) % 2 == 0|(-x) % 2 == 0|abs(x) % 2 == 0|(2 * x) % 2 == 0|(2 * x + 1) % 2 != 0|x % 2 == y % 2|x % 2 != y % 2|x % 2|(x + 1) % 2|(x + y + z) % 2|sum(xs) % 2 == 0|all(a % 2 == 0 for a in xs)|any(a % 2 != 0 for a in xs)''',
'division_remainders': '''x // 2|x % 2|x // 3|x % 3|x // 4|x % 4|x // 5|x % 5|x // (n + 1)|x % (n + 1)|(x // (n + 1)) * (n + 1)|x - x % (n + 1)|x % (n + 1) == 0|(x + (n + 1)) % (n + 1)|(x * (n + 1)) % (n + 1)|(x + 2) // 2|(2 * x) // 2|(2 * x + 1) // 2|(x // 2, x % 2)|(x // (n + 1), x % (n + 1))''',
'polynomials': '''x * (y + z)|x * y + x * z|(x + y) * (x - y)|x * x - y * y|(x + y) ** 2|(x - y) ** 2|x ** 2 + 2 * x * y + y ** 2|x ** 2 - 2 * x * y + y ** 2|(x + 1) ** 2|(x - 1) ** 2|(x + y) * (y + z)|(x + y + z) ** 2|x * y + y * z + z * x|x ** 3 - x|x * (x - 1) * (x + 1)|(x + y) ** 3|x ** 3 + 3 * x ** 2 * y + 3 * x * y ** 2 + y ** 3|x * (y * z)|x * (y - z) + x * z|(x - y) * (x - y)''',
'boolean_logic': '''not p|p and q|p or q|p != q|p == q|(not p) or q|not (p and q)|not (p or q)|p and (q or r)|p or (q and r)|(p and q) or (p and r)|(p or q) and (p or r)|(p and not q) or (not p and q)|p if q else r|not (not p)|p and True|p or False|(p == q) and (q == r)|(p or q) and not (p and q)|(not p or q) and (not q or r)''',
'conditionals': '''x if p else y|x if x >= 0 else -x|x if x <= y else y|x if x >= y else y|x + 1 if p else x - 1|x if p and q else y|x if p or q else y|x if not p else y|1 if p else 0|0 if x < 0 else x|x if x != 0 else y|y if x == 0 else x|x + y if p else x - y|-x if p else x|x if p else (y if q else z)|x + 1 if x % 2 == 0 else x|x if x <= n else n|x if x >= -n else -n|x if x >= y and x >= z else max(y, z)|x if x <= y and x <= z else min(y, z)''',
'pairs': '''(x, y)|(y, x)|pair[0]|pair[1]|(pair[1], pair[0])|pair[0] + pair[1]|pair[0] - pair[1]|pair[0] * pair[1]|(pair[0] + 1, pair[1])|(pair[0], pair[1] + 1)|(-pair[0], -pair[1])|(abs(pair[0]), abs(pair[1]))|(min(x, y), max(x, y))|(pair[0] + x, pair[1] + x)|(pair[0] * x, pair[1] * x)|pair[0] == pair[1]|pair[0] <= pair[1]|(x + y, x - y)|(len(xs), sum(xs))|(p and q, p or q)''',
'optional_values': '''opt is None|opt is not None|opt if opt is not None else x|None if p else x|x if p else None|None if opt is None else opt + 1|None if opt is None else -opt|None if opt is None else abs(opt)|None if opt is None else opt * x|None if opt is None else opt - x|opt is not None and opt > 0|opt is None or opt >= 0|[] if opt is None else [opt]|xs[0] if xs else None|xs[-1] if xs else None|x if x >= 0 else None|x if x % 2 == 0 else None|opt if opt is not None and opt >= 0 else None|opt if opt is not None else (x if p else None)|None if opt is None else (opt if opt <= x else x)''',
'list_construction': '''[]|[x]|[x, y]|[x, y, z]|[x] + xs|xs + [x]|[x] + xs + [y]|[x] * n|xs * 2|xs * 3|[x, x]|[x, y, x]|[x, y] * n|[0] * n|[True] * n|list(pair)|[p, q]|[len(xs)]|[sum(xs)]|[x] if p else []''',
'list_concatenation': '''xs + ys|xs + ys + zs|xs + ys + xs|xs + []|[] + xs|[x] + xs + ys|xs + [x] + ys|xs + ys + [x]|xs + ys + ys|xs + xs + ys|(xs + ys)[::-1]|xs[::-1] + ys|xs + ys[::-1]|[a + 1 for a in xs + ys]|sum(xs + ys)|len(xs + ys)|x in xs + ys|all(a >= 0 for a in xs + ys)|any(a == x for a in xs + ys)|[a for a in xs + ys if a > 0]''',
'list_lengths': '''len(xs)|len(xs + ys)|len([x] + xs)|len(xs + [x])|len(xs[::-1])|len([a + x for a in xs])|len(xs[:n])|len(xs[n:])|len(xs[:n]) + len(xs[n:])|len(xs * n)|len(list(zip(xs, ys)))|len([a for a in xs if a == x])|len([a for a in xs if a != x])|len([a for a in xs if a > 0])|len(xs) == len(ys)|len(xs) <= len(ys)|len(xs) + len(ys) + len(zs)|len(xs[1:])|len(xs[:-1])|len(xs + ys) - len(xs)''',
'list_mapping': '''[a + 1 for a in xs]|[a - 1 for a in xs]|[-a for a in xs]|[abs(a) for a in xs]|[a * 2 for a in xs]|[a * x for a in xs]|[a + x for a in xs]|[a - x for a in xs]|[a * a for a in xs]|[a % 2 for a in xs]|[a // 2 for a in xs]|[a >= 0 for a in xs]|[a == x for a in xs]|[max(a, 0) for a in xs]|[min(a, x) for a in xs]|[max(a, x) for a in xs]|[(a, a) for a in xs]|[(a, x) for a in xs]|[a + x if p else a - x for a in xs]|[a + 1 for a in xs[::-1]]''',
'list_filtering': '''[a for a in xs if a > 0]|[a for a in xs if a >= 0]|[a for a in xs if a < 0]|[a for a in xs if a <= 0]|[a for a in xs if a == 0]|[a for a in xs if a != 0]|[a for a in xs if a == x]|[a for a in xs if a != x]|[a for a in xs if a < x]|[a for a in xs if a <= x]|[a for a in xs if a > x]|[a for a in xs if a >= x]|[a for a in xs if a % 2 == 0]|[a for a in xs if a % 2 != 0]|[a for a in xs if x <= a <= y]|[a for a in xs if a < x or a > y]|[a for a in xs if a in ys]|[a for a in xs if a not in ys]|[a for a in xs if p]|[a + 1 for a in xs if a >= 0]''',
'list_sums': '''sum(xs)|sum(xs + ys)|sum([x] + xs)|sum(xs + [x])|sum(xs[::-1])|sum([a + x for a in xs])|sum([a * x for a in xs])|sum([-a for a in xs])|sum([abs(a) for a in xs])|sum([a for a in xs if a >= 0])|sum([a for a in xs if a < 0])|sum(xs * n)|sum(xs[:n])|sum(xs[n:])|sum(xs[:n]) + sum(xs[n:])|sum(xs) + sum(ys) + sum(zs)|sum([a * a for a in xs])|sum([a + b for a, b in zip(xs, ys)])|sum([a - b for a, b in zip(xs, ys)])|sum([x] * n)''',
'list_counting': '''xs.count(x)|xs.count(0)|xs.count(x) == 0|xs.count(x) > 0|xs.count(x) <= len(xs)|(xs + ys).count(x)|xs[::-1].count(x)|([x] + xs).count(x)|(xs + [x]).count(x)|len([a for a in xs if a % 2 == 0])|len([a for a in xs if a % 2 != 0])|len([a for a in xs if a > 0])|len([a for a in xs if a < 0])|sum([1 if a == x else 0 for a in xs])|len(xs) - xs.count(x)|[a + y for a in xs].count(x + y)|[-a for a in xs].count(-x)|(xs * n).count(x)|xs[:n].count(x) + xs[n:].count(x)|xs.count(x) + xs.count(y)''',
'list_reversal': '''xs[::-1]|xs[::-1][::-1]|(xs + ys)[::-1]|([x] + xs)[::-1]|(xs + [x])[::-1]|xs[::-1] + ys[::-1]|xs[::-1][:n]|xs[:n][::-1]|xs[n:][::-1]|[a + x for a in xs[::-1]]|[a for a in xs[::-1] if a != x]|sum(xs[::-1])|len(xs[::-1])|xs[::-1].count(x)|x in xs[::-1]|xs == xs[::-1]|xs[::-1][0] if xs else x|xs[::-1][-1] if xs else x|(xs + ys + zs)[::-1]|(xs * n)[::-1]''',
'list_membership': '''x in xs|x not in xs|x in xs + ys|x in [y] + xs|x in xs + [y]|x in xs[::-1]|x in xs[:n]|x in xs[n:]|all(a >= 0 for a in xs)|any(a < 0 for a in xs)|all(a == x for a in xs)|any(a == x for a in xs)|all(a in ys for a in xs)|any(a in ys for a in xs)|all(a != x for a in xs)|any(a != x for a in xs)|all(a % 2 == 0 for a in xs)|any(a % 2 == 0 for a in xs)|x in [a + y for a in xs]|x in [a for a in xs if a >= 0]''',
'safe_indexing': '''xs[n] if n < len(xs) else x|xs[0] if xs else x|xs[-1] if xs else x|xs[1] if len(xs) > 1 else x|xs[-2] if len(xs) > 1 else x|(xs + [x])[0]|([x] + xs)[-1]|([x] + xs)[0]|(xs + [x])[-1]|xs[n] if n < len(xs) else None|xs[n] + y if n < len(xs) else y|xs[n] == x if n < len(xs) else False|xs[:1]|xs[-1:]|xs[1:]|xs[:-1]|(xs + ys)[n] if n < len(xs + ys) else x|xs[::-1][n] if n < len(xs) else x|xs[n:n+1]|xs[:n][-1] if xs[:n] else x''',
'list_slicing': '''xs[:n]|xs[n:]|xs[:n] + xs[n:]|xs[n:n+k]|xs[:n][:k]|xs[n:][k:]|xs[:0]|xs[0:]|xs[:len(xs)]|xs[len(xs):]|xs[:n] + ys|xs[n:] + ys|(xs + ys)[:n]|(xs + ys)[n:]|len(xs[n:n+k])|sum(xs[n:n+k])|[a + x for a in xs[:n]]|[a for a in xs[n:] if a > 0]|xs[:n] == xs|xs[n:] == []''',
'list_zipping': '''list(zip(xs, ys))|[a + b for a, b in zip(xs, ys)]|[a - b for a, b in zip(xs, ys)]|[a * b for a, b in zip(xs, ys)]|[min(a, b) for a, b in zip(xs, ys)]|[max(a, b) for a, b in zip(xs, ys)]|[a == b for a, b in zip(xs, ys)]|[a <= b for a, b in zip(xs, ys)]|[a for a, b in zip(xs, ys)]|[b for a, b in zip(xs, ys)]|[(b, a) for a, b in zip(xs, ys)]|len(list(zip(xs, ys)))|sum([a + b for a, b in zip(xs, ys)])|all(a == b for a, b in zip(xs, ys))|any(a == b for a, b in zip(xs, ys))|list(zip(xs, xs))|list(zip(xs[::-1], ys))|list(zip(xs[:n], ys[:n]))|[(a + x, b + x) for a, b in zip(xs, ys)]|[abs(a - b) for a, b in zip(xs, ys)]''',
'natural_ranges': '''list(range(n))|list(range(n + 1))|list(range(n, n + k))|list(range(n))[::-1]|len(list(range(n)))|sum(range(n))|n in range(n)|k in range(n)|[a + 1 for a in range(n)]|[a * 2 for a in range(n)]|[a * 2 + 1 for a in range(n)]|[a + x for a in range(n)]|[a for a in range(n) if a < k]|list(range(n))[:k]|list(range(n))[k:]|list(range(n)) + list(range(k))|list(zip(range(n), range(n)))|all(a >= 0 for a in range(n))|all(a < n for a in range(n))|sum([x for a in range(n)])''',
'finite_sets': '''len(set(xs))|len(set(xs).union(ys))|len(set(xs).intersection(ys))|len(set(xs).difference(ys))|len(set(xs).symmetric_difference(ys))|x in set(xs)|x in set(xs).union(ys)|x in set(xs).intersection(ys)|x in set(xs).difference(ys)|set(xs).issubset(ys)|set(xs).issuperset(ys)|set(xs).isdisjoint(ys)|set(xs) == set(ys)|len(set(xs)) <= len(xs)|len(set(xs + [x]))|len(set(xs).difference([x]))|set(xs).union(ys) == set(ys).union(xs)|set(xs).intersection(ys) == set(ys).intersection(xs)|set(xs).difference(ys).isdisjoint(ys)|set(xs).union(ys).issuperset(xs)''',
}

ARG_TYPES={'x':'int','y':'int','z':'int','n':'int','k':'int','xs':'list[int]','ys':'list[int]','zs':'list[int]','p':'bool','q':'bool','r':'bool','pair':'tuple[int, int]','opt':'int | None'}
ORDER=list(ARG_TYPES)

def make_tasks():
    tasks=[]
    assert len(FAMILIES)==25
    for topic,items in FAMILIES.items():
        exprs=items.split('|')
        assert len(exprs)==20,(topic,len(exprs))
        for i,expr in enumerate(exprs,1):
            tree=ast.parse(expr,mode='eval')
            bound={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
            names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}-bound
            args=[a for a in ORDER if a in names]
            signature=', '.join(a+': '+ARG_TYPES[a] for a in args)
            code='def solution('+signature+'):\n    return '+expr+'\n'
            natural=[a for a in args if a in ('n','k') or topic=='natural_arithmetic']
            task_id=f'tiny_{topic}_{i:02d}'
            intent=f'Compute `{expr}` with the exact Python behavior shown. '
            intent+='Inputs '+', '.join(natural)+' are nonnegative integers. ' if natural else ''
            intent+='Other integer inputs may be negative. List order and duplicates matter; zip truncates to the shorter list; division and remainder follow Python with positive divisors.'
            rng=random.Random(task_id)
            samples=[]
            for j in range(32):
                values={}
                for a in args:
                    if a in ('p','q','r'):v=bool(rng.randrange(2))
                    elif a in ('xs','ys','zs'):
                        v=[] if j==0 else [rng.randrange(-4,5) for _ in range(rng.randrange(7))]
                    elif a=='pair':v=[rng.randrange(-4,5),rng.randrange(-4,5)]
                    elif a=='opt':v=None if j%3==0 else rng.randrange(-4,5)
                    else:v=rng.randrange(7) if a in natural else rng.randrange(-6,7)
                    values[a]=v
                ns={};exec(code,ns)
                inputs={k:tuple(v) if k=='pair' else v for k,v in values.items()}
                answer=ns['solution'](**inputs)
                samples.append({'inputs':values,'expected':answer})
            tasks.append({'task_id':task_id,'topic':topic,'index':i,'python':code,'args':args,'arg_types':{a:ARG_TYPES[a] for a in args},'natural_inputs':natural,'intent':intent,'tests':samples,'property_requirement':'Prove at least one universally quantified, nonvacuous property characterizing the output or its relation to the inputs; use the fixed Python semantics. Preserve at least two executable examples. Avoid a specification whose conclusion is only True or a self-equality.'})
    return tasks

if __name__=='__main__':
    root=Path(__file__).parent
    tasks=make_tasks()
    data=''.join(json.dumps(t,sort_keys=True)+'\n' for t in tasks)
    (root/'manifest.jsonl').write_text(data)
    (root/'manifest.sha256').write_text(hashlib.sha256(data.encode()).hexdigest()+'  manifest.jsonl\n')
    print(json.dumps({'tasks':len(tasks),'topics':len(FAMILIES),'sha256':hashlib.sha256(data.encode()).hexdigest()}))
