"""Execute the unchanged corrected hidden-test adapter on isolated, bounded train-only cells."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
E12 = HERE.parents[2] / '12_scsc_vs_hidden_gold_tests_vbv1_across_systems'
sys.path.insert(0, str(E12 / 'expt_v2/scripts'))
import adapter_v2 as adapter
from training_checkpoint import digest, write_new

ADDRESS_SPACE = 64 * 1024**3


class Runtime:
    def __init__(self, root, lake, lake_bin):
        self.root = Path(root)
        self.lake = Path(lake)
        self.lake_bin = str(lake_bin)
        (self.root / 'modules').mkdir(parents=True, exist_ok=True)

    def lean(self, path, extra=()):
        started = time.monotonic()
        env = {**os.environ, 'LEAN_PATH': str(self.root / 'modules')}
        command = ['prlimit', f'--as={ADDRESS_SPACE}', '--', 'nice', '-n', '10',
                   self.lake_bin, 'env', 'lean', '-j', '1', *extra, str(path)]
        with path.with_suffix('.log').open('x') as log:
            child = subprocess.Popen(command, cwd=self.lake, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = child.wait(timeout=600)
                status = 'ok' if code == 0 else 'error' if code > 0 else 'terminated'
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                code = child.wait()
                status = 'timeout'
        text = path.with_suffix('.log').read_text()
        if re.search(r'out of memory|failed to allocate|cannot allocate memory|std::bad_alloc', text, re.I):
            status = 'resource_limit'
        pairs = re.findall(r'^E12_TEST_(\d+)=(true|false)$', text, re.M)
        if len({int(i) for i, _ in pairs}) != len(pairs):
            status = 'duplicate_test_output'
        outputs = {int(i): v == 'true' for i, v in pairs}
        if status not in ('ok', 'error'):
            outputs = {}
        return {'status': status, 'returncode': code, 'seconds': time.monotonic()-started,
                'log': str(path.with_suffix('.log')), 'log_sha256': digest(path.with_suffix('.log')),
                'outputs': outputs}

    def compile(self, source, module):
        if not re.fullmatch(r'E13Hidden[0-9a-f]{24}', module):
            raise ValueError('module name must be an owned digest identifier')
        path = self.root / 'modules' / (module + '.lean')
        with path.open('x') as out:
            out.write(source)
        receipt = self.lean(path, ('--root=' + str(self.root/'modules'), '-o', str(path.with_suffix('.olean'))))
        return path, receipt

    def evaluate(self, suite, source, module, compiled=None):
        if not re.fullmatch(r'E13Hidden[0-9a-f]{24}', module):
            raise ValueError('module name must be an owned digest identifier')
        if suite['n_tests'] != len(suite['tests']):
            raise ValueError('hidden-test denominator changed')
        if not suite['n_tests']:
            return {'status': 'no_tests', 'n_tests': 0, 'hidden_all_pass': None,
                    'hidden_pass_rate': None, 'fully_applicable': False}
        if compiled is None:
            path, compiled = self.compile(source, module)
        else:
            path = self.root/'modules'/(module+'.lean')
            if (path.read_text() != source or compiled['status'] != 'ok'
                    or not path.with_suffix('.olean').exists()):
                raise ValueError('compiled mutant does not match its source')
        result = {'compile': compiled, 'candidate_sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'candidate_path': str(path)}
        if compiled['status'] != 'ok':
            failure = compiled['status'] == 'error'
            return {**result, 'status': 'compile_failure' if failure else 'unresolved_compile',
                    'n_tests': suite['n_tests'], 'fully_applicable': False,
                    'hidden_all_pass': False if failure else None,
                    'hidden_pass_rate': 0.0 if failure else None}
        initial, _, _ = adapter.map_symbols(suite['symbols'], source)
        symbols = {token: name for test in suite['tests'] for token, name in test['symbols'].items()}
        cache = {}

        def agreement(gold, matches, tuples):
            if tuples is None:
                return {'agrees': None, 'reason': 'argument_extraction_unknown'}
            qualified = []
            for args in tuples:
                converted = []
                for arg in args:
                    pieces = re.split(r'("(?:\\.|[^"\\])*")', arg)
                    for i in range(0, len(pieces), 2):
                        if any(token in symbols and symbols[token] not in initial
                               for token in adapter.IDENT.findall(pieces[i])):
                            return {'agrees': None, 'reason': 'argument_symbol_unmapped'}
                        pieces[i] = adapter.IDENT.sub(
                            lambda m: '_root_.' + initial[symbols[m.group()]]
                            if m.group() in symbols else m.group(), pieces[i])
                    converted.append(''.join(pieces))
                qualified.append(converted)
            key = hashlib.sha256(json.dumps([[d['full_name'] for d in matches], qualified]).encode()).hexdigest()[:20]
            if key in cache:
                return cache[key]
            lines = ['import Mathlib', 'import ' + module, 'deriving instance DecidableEq for Except']
            count = 0
            for args in qualified:
                callargs = ' '.join('(' + arg + ')' for arg in args)
                for other in matches[1:]:
                    left = '_root_.' + matches[0]['full_name'] + ' ' + callargs
                    right = '_root_.' + other['full_name'] + ' ' + callargs
                    lines.append(f'#eval IO.println ("E12_TEST_{count}=" ++ toString (decide (({left}) = ({right}))))')
                    count += 1
            probe = self.root / (module + '_Agreement_' + key + '.lean')
            with probe.open('x') as out:
                out.write('\n'.join(lines) + '\n')
            receipt = self.lean(probe)
            outputs = receipt['outputs']
            agrees = all(outputs.values()) if set(outputs) == set(range(count)) and receipt['status'] == 'ok' else None
            cache[key] = {'agrees': agrees, 'n_comparisons': count, 'n_decided': len(outputs),
                          'probe_sha256': digest(probe), 'arguments': qualified, 'compiler': receipt}
            return cache[key]

        mapping, diagnostics, declarations = adapter.map_symbols(suite['symbols'], source, suite['tests'], agreement)
        plan = adapter.per_test_plan(suite['tests'], mapping)
        probe = self.root / (module + '_Bridge.lean')
        with probe.open('x') as out:
            out.write(adapter.bridge(module, suite['tests'], mapping))
        evaluation = self.lean(probe) if mapping else {'status': 'not_applicable', 'outputs': {}}
        outputs = evaluation['outputs']
        if not set(outputs) <= {r['index'] for r in plan if r['status'] == 'mapped'}:
            raise ValueError('hidden evaluation returned undeclared tests')
        outcome = adapter.cell_outcome(suite['n_tests'], outputs, plan)
        return {**result, **outcome, 'status': 'measured' if outcome['fully_applicable'] else 'incomplete',
                'mapping': mapping, 'diagnostics': diagnostics, 'declarations': declarations,
                'evaluation': evaluation, 'bridge_sha256': digest(probe)}


def measure_cell(cell, config, bindings, execution_sha, runtime_class=Runtime):
    """Called by a parent with a published control/audit lock; one durable attempt per cell."""
    train_path = Path(config['train_ids'])
    if bindings.get(str(train_path)) != digest(train_path):
        raise ValueError('train allowlist is unbound or changed')
    if cell['split'] != 'train' or cell['task_id'] not in set(train_path.read_text().splitlines()):
        raise ValueError('hidden runtime only admits declared train cells')
    for key in ('source', 'suite'):
        if bindings.get(cell[key]) != digest(cell[key]):
            raise ValueError('hidden input is unbound or changed')
    identity = {key: cell[key] for key in ('cell_id', 'task_id', 'split')}
    binding = {**identity, 'execution_sha256': execution_sha,
               'source_sha256': digest(cell['source']), 'suite_sha256': digest(cell['suite'])}
    key = hashlib.sha256(cell['cell_id'].encode()).hexdigest()[:24]
    root = Path(config['root']) / key
    root.mkdir(parents=True, exist_ok=True)
    if (root/'attempt.json').exists():
        if json.loads((root/'attempt.json').read_text()) != binding:
            raise ValueError('hidden attempt binding changed')
        if (root/'result.json').exists():
            return json.loads((root/'result.json').read_text())
        raise RuntimeError('unfinished hidden attempt; reconcile cleanup, never implicitly rerun')
    write_new(root/'attempt.json', binding)
    suite = json.loads(Path(cell['suite']).read_text())
    source = Path(cell['source']).read_text()
    runtime = runtime_class(root, config['lake'], config['lake_bin'])
    result = {**binding, **runtime.evaluate(suite, source, 'E13Hidden' + key)}
    write_new(root/'result.json', result)
    return result
