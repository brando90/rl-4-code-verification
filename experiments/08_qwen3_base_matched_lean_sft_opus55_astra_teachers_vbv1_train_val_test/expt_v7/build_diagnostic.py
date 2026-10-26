"""Freeze 50 previously trained prompts and 50 newly authored composition functions for inference only."""
from __future__ import annotations
import ast
import collections
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
REPO = HERE.parents[2]
RUN = Path(os.environ.get('TINY_RUN_ROOT', '/lfs/skampere1/0/eth127/rl4cv_tiny_training'))
ROOT = RUN / 'diagnostic_seen_fresh_v7'
sys.path.insert(0, str(REPO/'src'))

# Two new compositions per original topic. Shared primitives are intentional;
# these are novel function bodies, not a claim of disjoint mathematical topics.
FRESH = {
 'natural_arithmetic': ['(x + 1) * (y + 1) + z', 'max(x + y - z, 0)'],
 'integer_arithmetic': ['abs(x + y) - abs(x - y)', 'x // (abs(y) + 1) + x % (abs(y) + 1)'],
 'comparisons': ['(x < y) == (y < z)', 'min(x, y) <= z <= max(x, y)'],
 'bounds_and_extrema': ['min(max(x, min(y, z)), max(y, z))', 'max(abs(x), abs(y)) - min(abs(x), abs(y))'],
 'parity': ['sum(1 for a in xs if a % 2 == 0) % 2 == 0', '[(a + b) % 2 == 0 for a, b in zip(xs, ys)]'],
 'division_remainders': ['(x % (n + 1), x // (n + 1))', '(x + y) // (n + 1)'],
 'polynomials': ['(x + y + z) ** 2 - (x * x + y * y + z * z)', '(x + 1) * (x + 2) * (x + 3)'],
 'boolean_logic': ['p != (q and r)', 'not (p == q == r)'],
 'conditionals': ['x + y if x >= y else y - x', 'max(x, y) if p else min(x, y)'],
 'pairs': ['(pair[0] + pair[1], abs(pair[0] - pair[1]))', '(sum(xs), sum(a * a for a in xs))'],
 'optional_values': ['None if opt is None else opt * opt + 1', 'None if not xs else max(xs[0], xs[-1])'],
 'list_construction': ['xs + [x, y] + xs[::-1]', '[x if i % 2 == 0 else y for i in range(n)]'],
 'list_concatenation': ['[a + b for a in xs for b in ys]', 'xs[:n] + ys + xs[n:]'],
 'list_lengths': ['len([a for a in xs if x <= a <= y])', 'len(xs[:n] + ys[n:])'],
 'list_mapping': ['[abs(a - x) for a in xs]', '[a // 2 if a % 2 == 0 else -a for a in xs]'],
 'list_filtering': ['[a for a in xs if abs(a) <= n]', '[a for a, b in zip(xs, ys) if a < b]'],
 'list_sums': ['sum(a * b for a, b in zip(xs, ys))', 'sum(max(a - x, 0) for a in xs)'],
 'list_counting': ['sum(1 for a, b in zip(xs, ys) if a == b)', 'len([a for a in xs if a != x and a != y])'],
 'list_reversal': ['list(zip(xs, ys))[::-1]', '[a - b for a, b in zip(xs[::-1], ys)]'],
 'list_membership': ['x in [abs(a) for a in xs]', 'any(a + b == x for a, b in zip(xs, ys))'],
 'safe_indexing': ['sum(xs[:n]) if n <= len(xs) else x', '(xs[n], xs[n + 1]) if n + 1 < len(xs) else (x, y)'],
 'list_slicing': ['xs[:n] + xs[n + k:]', 'xs[n:] + xs[:n]'],
 'list_zipping': ['[(min(a, b), abs(a - b)) for a, b in zip(xs, ys)]', '[a + b for a, b in zip(xs, ys[::-1])]'],
 'natural_ranges': ['[x + i * i for i in range(n)]', '[i for i in range(n) if i % 2 == 0 and i < k]'],
 'finite_sets': ['set(xs).intersection(ys).issubset(zs)', 'len(set(xs).union(ys)) - len(set(xs).intersection(ys))'],
}
ARG_TYPES = {'x':'int','y':'int','z':'int','n':'int','k':'int',
             'xs':'list[int]','ys':'list[int]','zs':'list[int]',
             'p':'bool','q':'bool','r':'bool','pair':'tuple[int, int]','opt':'int | None'}

def read(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]

def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def family(source):
    """Normalize function/variable names and constants; preserve operators and call names."""
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if not functions:
        return None
    fn = next((f for f in functions if f.name == 'solution'), functions[0])
    names = {a.arg:f'arg{i}' for i,a in enumerate(fn.args.args)}
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.setdefault(node.id, f'local{len(names)}')
    class Normalize(ast.NodeTransformer):
        def visit_Name(self, node):
            return ast.copy_location(ast.Name(id=names.get(node.id,node.id),ctx=node.ctx),node)
        def visit_Constant(self, node):
            return ast.copy_location(ast.Constant(value=f'constant:{type(node.value).__name__}'),node)
    body = ast.Module(body=fn.body,type_ignores=[])
    return sha(ast.dump(Normalize().visit(body),include_attributes=False))

def fresh_tasks():
    output = []
    for topic, expressions in FRESH.items():
        for index, expr in enumerate(expressions, 1):
            parsed = ast.parse(expr, mode='eval')
            bound = {n.id for n in ast.walk(parsed) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
            names = {n.id for n in ast.walk(parsed) if isinstance(n,ast.Name)}-bound
            args = [a for a in ARG_TYPES if a in names]
            natural = [a for a in args if a in ('n','k') or topic == 'natural_arithmetic']
            source = 'def solution('+', '.join(a+': '+ARG_TYPES[a] for a in args)+'):\n    return '+expr+'\n'
            tid = f'fresh_{topic}_{index:02d}'
            intent = f'Compute `{expr}` with the exact Python behavior shown. '
            if natural:
                intent += 'Inputs '+', '.join(natural)+' are nonnegative integers. '
            intent += 'Other integer inputs may be negative. List order and duplicates matter; zip truncates to the shorter list; division and remainder follow Python with positive divisors.'
            ns = {}
            exec(compile(source,tid,'exec'),ns)
            rng = random.Random('seen-fresh-v7:'+tid)
            tests = []
            for j in range(32):
                values = {}
                for a in args:
                    if ARG_TYPES[a] == 'bool':
                        v = bool((j//(2**('pqr'.index(a))))%2) if j<8 else bool(rng.randrange(2))
                    elif a in ('xs','ys','zs'):
                        edges = [[],[0],[1],[-1],[1,-1,1],[0,0],[-2,0,2],[2,1,0]]
                        v = edges[(j+('xs','ys','zs').index(a))%8] if j<8 else [rng.randrange(-4,5) for _ in range(rng.randrange(7))]
                    elif a == 'pair':
                        v = [rng.randrange(-4,5),rng.randrange(-4,5)]
                    elif a == 'opt':
                        v = None if j%3 == 0 else rng.randrange(-4,5)
                    elif a in natural:
                        v = j%7 if j<8 else rng.randrange(8)
                    else:
                        v = [-3,-1,0,1,3,0,2,-2][j] if j<8 else rng.randrange(-6,7)
                    values[a] = v
                inputs = {k:tuple(v) if k=='pair' else v for k,v in values.items()}
                tests.append({'inputs':values,'expected':ns['solution'](**inputs)})
            assert len({json.dumps(t['expected'],sort_keys=True) for t in tests}) >= 2, tid
            output.append(dict(task_id=tid,cohort='fresh',topic=topic,index=index,python=source,
                args=args,arg_types={a:ARG_TYPES[a] for a in args},natural_inputs=natural,
                intent=intent,tests=tests,normalized_family=family(source)))
    assert len(output) == 50
    assert len({t['normalized_family'] for t in output}) == 50
    return output

def main():
    from rl4cv.veribench.exp103 import build_prompt
    from rl4cv.veribench.pack import longest_python_block
    from rl4cv.screens import screen
    ROOT.mkdir(parents=True, exist_ok=True)
    assert not (ROOT/'manifest.jsonl').exists(), 'manifest is immutable after creation'
    source = EXPERIMENT/'expt_v5'
    original = read(source/'manifest.jsonl')
    trained = {r['task_id']:r for r in read(RUN/'curriculum/training.jsonl')}
    assert len(original) == len(trained) == 500
    # Use the exact prompt-building functions and prompt sources admitted in v6.
    spec = importlib.util.spec_from_file_location('tiny_checker_v5', source/'check_example.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    seen = []
    for topic in sorted(FRESH):
        candidates = [dict(t) for t in original if t['topic']==topic]
        chosen = sorted(candidates,key=lambda t:sha('seen-fresh-v7:'+t['task_id']))[:2]
        for task in chosen:
            task.update(cohort='seen',normalized_family=family(task['python']))
            seen.append(task)
    fresh = fresh_tasks()
    existing_families = {family(t['python']) for t in original}
    existing_python = {t['task_id']:t['python'] for t in original}
    parse_failures = []
    replay = read(RUN/'onep7/data/existing.jsonl')
    for i,row in enumerate(replay):
        py = longest_python_block(row['messages'][1]['content'])
        if py:
            existing_python[f'replay_{i}'] = py
            try:
                f = family(py)
                if f: existing_families.add(f)
            except SyntaxError:
                parse_failures.append(i)
    overlap = [t['task_id'] for t in fresh if t['normalized_family'] in existing_families]
    assert not overlap, overlap
    protected = {}
    for row in csv.DictReader((EXPERIMENT/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if row['split'] in ('validation','test'):
            protected[row['task_id']+'/python'] = (checker.VB/'veribench_dataset/py_src'/row['py_relpath']).read_text()
            protected[row['task_id']+'/lean'] = (checker.VB/'veribench_dataset/lean_src/veribench'/row['gold_relpath']).read_text()
    reports = {
        'fresh_vs_training_text':screen({t['task_id']:t['python'] for t in fresh},existing_python),
        'fresh_vs_protected':screen({t['task_id']:t['python'] for t in fresh},protected),
        'normalized_body_overlap':overlap, 'training_parse_failures':parse_failures,
        'fresh_authorship':'coordinator-authored Python compositions; no solver/model outcomes consulted',
        'limitation':'Shared primitives and topics; syntactic family disjointness does not prove semantic-family independence.'}
    write(ROOT/'screening.json',reports)
    assert not reports['fresh_vs_training_text']['n_exact']
    assert not reports['fresh_vs_protected']['n_exact']
    assert not reports['fresh_vs_protected']['n_near']
    # Retain every near training-text similarity as a limitation rather than hide it.
    tasks = seen+fresh
    (ROOT/'pack').mkdir(exist_ok=True)
    for task in tasks:
        instruction = checker.make_instruction(task)
        prompt = build_prompt(instruction,root=checker.VB)
        if task['cohort']=='seen':
            assert prompt.messages() == trained[task['task_id']]['messages'][:2]
        task['instruction_sha256'] = sha(instruction)
        task['prompt_sha256'] = prompt.prompt_sha256
        task['required_paths'] = list(prompt.required_paths)
        task['system_prompt_sha256'] = prompt.system_prompt_sha256
        task['addendum_sha256'] = prompt.addendum_sha256
        folder = ROOT/'pack'/task['task_id']
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'instruction.md').write_text(instruction)
    text = ''.join(json.dumps(t,sort_keys=True)+'\n' for t in tasks)
    (ROOT/'manifest.jsonl').write_text(text)
    (ROOT/'task_ids.txt').write_text(''.join(t['task_id']+'\n' for t in tasks))
    expected = [{'task_id':t['task_id'],'sample_idx':0,'cohort':t['cohort']} for t in tasks]
    write(ROOT/'cells.json',expected)
    protocol = HERE/'PROTOCOL.md'
    write(ROOT/'admission.json',dict(status='PASS',tasks=100,seen=50,fresh=50,
        manifest_sha256=sha(text),protocol_sha256=sha(protocol.read_text()),
        source_training_sha256=sha((RUN/'curriculum/training.jsonl').read_text()),
        source_code_sha256=sha(Path(__file__).read_text()),
        new_optimizer_updates=0,benchmark_test_evaluation=False))
    print((ROOT/'admission.json').read_text())

if __name__=='__main__':
    main()
