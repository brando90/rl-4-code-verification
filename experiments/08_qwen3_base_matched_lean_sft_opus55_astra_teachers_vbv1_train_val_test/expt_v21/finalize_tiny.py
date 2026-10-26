"""Freeze checked tiny repairs, preserving an outcome for every declared source row.

This admission step reads existing kernel receipts; it never invokes Lean or a model.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'expt_v8')]
import repair_batches as repair
from comment_integrity import safe_line_starts

ROOT, RUN, base = repair.ROOT, repair.RUN, repair.base
ACCEPTED = {
    'ACCEPTED_REPAIRED', 'ACCEPTED_MECHANICAL_RFL', 'ACCEPTED_SAVED_CANDIDATE',
    'ACCEPTED_REUSED', 'MECHANICAL_RFL', 'SAVED_CANDIDATE',
}
TERMINAL_EXCLUSION = {'EXCLUDED_BOUNDED_REPAIR'}
BASELINE_SHA = '0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7'
FORBIDDEN = re.compile(r'\b(sorry|admit|axiom|run_tac|run_cmd|unsafe|elab|macro)\b')
NEW_COMMAND = re.compile(r'(?m)^\s*(?:theorem|lemma|def|example|namespace|end|section|variable|open|import|attribute|instance|structure|inductive|class|abbrev|opaque|constant|axiom|syntax|notation|export|initialize)\b')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scoped_proofs(original, candidate, inp, automation, strip_comments, *, require_inline=True):
    """Verify original fixed bytes around the only permitted proof substitutions.

The one additional block is the prescribed sketch immediately after the original
imports. The non-proof bytes, including all preserved proof terms, match exactly.
    """
    imports = list(re.finditer(r'(?m)^import [^\n]+\n', original))
    require(imports, 'Original imports not found')
    at = imports[-1].end()
    require(candidate[:at] == original[:at], 'Original import/header bytes changed')
    sketch = re.match(r'\n/- Proof sketch:\n(.*?)\n-/\n', candidate[at:], re.S)
    require(sketch is not None, 'Missing prescribed proof-sketch block after imports')
    lines = sketch[1].splitlines()
    require(2 <= len(lines) <= 10, 'Proof sketch must contain 2–10 lines')
    require(all(0 < len(line) <= 400 and '-/' not in line for line in lines), 'Malformed sketch line')
    require(all(re.search(r'[A-Za-z]{3}', line) for line in lines), 'Sketch lacks English explanations')
    body = candidate[:at] + candidate[at + sketch.end():]
    targets = sorted(inp['ranges'], key=lambda row: row['start'])
    require(targets, 'No targeted proofs in declared tiny repair')
    pieces, end = [], 0
    for n, item in enumerate(targets):
        start, stop = item['start'], item['end']
        require(end <= start < stop <= len(original), 'Invalid/overlapping cached proof range')
        require(original[start:stop] == item['original'], 'Cached original proof bytes changed')
        pieces.extend((re.escape(original[end:start]), f'(?P<proof_{n}>.*?)'))
        end = stop
    pieces.append(re.escape(original[end:]))
    match = re.fullmatch(''.join(pieces), body, re.S)
    require(match is not None, 'Implementation/statements/tests or other original non-proof bytes changed')
    proofs, inline = [], 0
    for n, item in enumerate(targets):
        proof = match[f'proof_{n}']
        require(proof.strip().startswith(('by\n', 'by ')), 'Replacement is not a by proof')
        safe_line_starts(proof)
        hits = automation(proof)
        require(not hits, f'Excluded automation in replacement: {hits}')
        masked = strip_comments(proof)
        require(not FORBIDDEN.search(masked), 'Forbidden proof escape or unproved declaration')
        require(not NEW_COMMAND.search(masked), 'New declaration/command inside replacement bytes')
        comments = re.findall(r'(?m)^\s*--([^\n]+)', proof)
        inline += sum(bool(re.search(r'[A-Za-z]{3}', line)) for line in comments)
        proofs.append(dict(index=item['index'], proof_sha256=base.sha(proof), automation=[],
                           start=match.start(f'proof_{n}') + sketch.end(),
                           end=match.end(f'proof_{n}') + sketch.end()))
    preserved = []
    for item in inp['preserved_proofs']:
        proof = original[item['start']:item['end']]
        require(proof == item['original'], 'Preserved proof bytes differ from the cached source')
        hits = automation(proof)
        exception = bool(item.get('anonymous') and hits == ['native_decide'])
        require(not hits or exception, f'Excluded automation in preserved proof: {hits}')
        inline += sum(bool(re.search(r'[A-Za-z]{3}', line)) for line in re.findall(r'(?m)^\s*--([^\n]+)', proof))
        preserved.append(dict(index=item['index'], proof_sha256=base.sha(proof), original_anonymous_native_decide=exception))
    require(not require_inline or inline > 0, 'No meaningful English inline proof comment')
    return dict(scope_gate='exact_original_nonproof_bytes_and_preserved_proofs',
                original_sha256=base.sha(original), source_sha256=base.sha(candidate),
                proof_sketch_lines=len(lines), english_inline_proof_comments=inline,
                replaced_proofs=proofs, preserved_proofs=preserved)


def protected_references():
    protected = {}
    vb = RUN / 'repo/external/veribench'
    split = HERE.parent / 'expt_v1/results/split/vbv1_split_manifest.csv'
    with split.open() as stream:
        for item in csv.DictReader(stream):
            if item['split'] in ('validation', 'test'):
                protected[item['task_id'] + '/python'] = (vb / 'veribench_dataset/py_src' / item['py_relpath']).read_text()
                protected[item['task_id'] + '/lean'] = (vb / 'veribench_dataset/lean_src/veribench' / item['gold_relpath']).read_text()
    for item in base.read_rows(RUN / 'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort'] == 'fresh':
            protected[item['task_id'] + '/python'] = item['python']
    require(len(protected) == 764, 'Protected reference set changed')
    return protected


def copy_receipt(final, folder, row, receipt_path, scope, source, binding):
    """Copy raw receipts, exact source and compiler evidence; retain old paths as provenance."""
    dest = final / 'proof_receipts' / f'tiny_{row["example_index"]:04d}'
    dest.mkdir(parents=True)
    files = {}

    def copy(source, rel):
        source = Path(source)
        require(source.is_file() and not source.is_symlink(), f'Missing/nonregular proof evidence: {source}')
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        files[str(rel)] = base.sha(target.read_bytes())

    for name in ('Original.lean', 'input.json', 'envelope.json', 'original.json', 'prior_verification.json'):
        copy(folder / name, name)
    copy(folder / 'Solution.lean', 'CheckedSolution.lean')
    (dest / 'Solution.lean').write_text(source)
    files['Solution.lean'] = base.sha((dest / 'Solution.lean').read_bytes())
    copy(receipt_path, 'result.json')
    receipt = repair.read(receipt_path)
    evidence = Path(receipt['kernel_report']['evidence_dir'])
    for source in sorted(evidence.rglob('*')):
        require(not source.is_symlink(), 'Symlink in compiler evidence')
        if source.is_file():
            copy(source, Path('kernel') / source.relative_to(evidence))
    require(files.get('kernel/original.olean') == receipt['kernel_report']['compiled_module_sha256'], 'Portable compiled module differs')
    repair.write(dest / 'scope_binding.json', scope)
    files['scope_binding.json'] = base.sha((dest / 'scope_binding.json').read_bytes())
    repair.write(dest / 'comment_binding.json', binding)
    files['comment_binding.json'] = base.sha((dest / 'comment_binding.json').read_bytes())
    repair.write(dest / 'files.json', files)
    return dict(example_index=row['example_index'], task_id=row['task_id'],
                source_sha256=row['lean_sha256'], receipt_sha256=base.sha(receipt_path.read_bytes()),
                kernel_checked_source_sha256=receipt['kernel_report']['source_sha256'],
                portable_receipt=str((dest / 'result.json').relative_to(final)),
                portable_comment_binding=str((dest / 'comment_binding.json').relative_to(final)),
                files_manifest=str((dest / 'files.json').relative_to(final)),
                files_manifest_sha256=base.sha((dest / 'files.json').read_bytes()),
                original_receipt_path=str(receipt_path))


def finalize(baseline):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    repair.assert_inspector()
    require(base.sha(repair.SOURCE.read_bytes()) == repair.SOURCE_SHA, 'Original tiny corpus hash changed')
    original = base.read_rows(repair.SOURCE)
    manifest = repair.read(ROOT / 'manifest.json')
    dispatch = repair.read(ROOT / 'dispatch.json')
    require(len(original) == len(manifest) == 500 and dispatch['declared'] == 500, 'Declared cohort is not exactly 500')
    require({row['example_index'] for row in manifest} == set(range(500)), 'Missing/repeated source index')
    require(len({row['task_id'] for row in manifest}) == 500, 'Repeated task identifier')
    batches = sorted((ROOT / 'batches').glob('*/status.json'))
    require(len(batches) == 125, 'Expected 125 declared four-case batches')
    require(all(repair.read(path)['state'] == 'DONE' for path in batches), 'Not all declared repair batches are terminal')
    published = ROOT / 'final'
    require(not published.exists(), 'Final outputs already exist; preserve immutable prior admission')
    final = ROOT / f'final_build_{int(time.time())}_{os.getpid()}'
    final.mkdir()
    (final / 'driver_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (final / 'add_missing_inline.py').write_bytes((HERE / 'add_missing_inline.py').read_bytes())
    frozen = repair.prior.FROZEN
    (final / 'kernel_axioms.py').write_bytes(frozen.read_bytes())
    kernel = repair.prior.kernel_module()
    sys.path[:0] = [str(RUN / 'repo/src'), str(HERE.parent / 'expt_v1/scripts')]
    from transformers import AutoTokenizer
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    from add_missing_inline import annotate_checked_source
    tok = AutoTokenizer.from_pretrained(repair.prior.TOKENIZER, local_files_only=True)
    baseline = Path(baseline).resolve()
    require(base.sha(baseline.read_bytes()) == BASELINE_SHA, 'Frozen live V20 baseline hash differs')
    prior = base.read_rows(baseline)
    require(prior, 'Empty global-dedup baseline')

    def source_key(source):
        return ' '.join(kernel.strip_comments(source, keep_literals=True).split())

    seen_source, seen_prompt = {}, {}
    for row in prior:
        answer = row['messages'][-1]['content']
        marker = re.search(r'(?m)^FILE: ([^\n]+)', answer)
        require(marker is not None, 'Unsupported baseline FILE format')
        source = extract_lean(answer, [marker[1]], root=RUN / 'repo/external/veribench').lean
        uid = row.get('uid', row['task_id'])
        seen_source.setdefault(source_key(source), uid)
        seen_prompt.setdefault(row['messages'][1]['content'], uid)
    protected = protected_references()
    case_bindings = {}
    for item in manifest:
        folder = ROOT / 'cases' / item['task_id']
        require(repair.read(folder / 'status.json')['state'] in ACCEPTED | TERMINAL_EXCLUSION,
                f'Nonterminal case despite finished batches: {item["task_id"]}')
        case_bindings[item['task_id']] = {name:base.sha((folder / name).read_bytes())
            for name in ('input.json', 'original.json', 'Original.lean', 'envelope.json', 'status.json')}
    repair.write(final / 'freeze.json', dict(declared=500, source_sha256=repair.SOURCE_SHA,
        manifest_sha256=base.sha((ROOT / 'manifest.json').read_bytes()), dispatch_sha256=base.sha((ROOT / 'dispatch.json').read_bytes()),
        driver_sha256=base.sha(Path(__file__).read_bytes()), inspector_sha256=repair.core.INSPECTOR_SHA,
        comment_adapter_sha256=base.sha((HERE / 'add_missing_inline.py').read_bytes()),
        baseline_path=str(baseline), baseline_sha256=base.sha(baseline.read_bytes()), baseline_rows=len(prior),
        protected_references=764, protected_reference_sha256=base.sha(json.dumps({k:base.sha(v) for k,v in protected.items()},sort_keys=True)),
        case_bindings=case_bindings, compiler_calls=0, model_calls=0, observed_unix=time.time()))
    reports, candidates = [], []
    for item in sorted(manifest, key=lambda row: row['example_index']):
        i, tid = item['example_index'], item['task_id']
        folder = ROOT / 'cases' / tid
        status = repair.read(folder / 'status.json')
        report = dict(task_id=tid, example_index=i, state=status['state'], kernel_verified=False,
                      admitted=False, exclusion='', format='NOT_RUN', source_sha256='', n_assistant_tokens='')
        try:
            require(base.sha((folder / 'status.json').read_bytes()) == case_bindings[tid]['status.json'], 'Status changed after finalization freeze')
            require(status['state'] in ACCEPTED | TERMINAL_EXCLUSION, 'Nonterminal case status')
            require(status['state'] in ACCEPTED, status.get('reason', 'Bounded repair did not establish a checked explicit proof'))
            require(original[i]['task_id'] == tid and repair.read(folder / 'original.json') == original[i], 'Original row binding changed')
            require(base.sha((folder / 'input.json').read_bytes()) == item['original_input_sha256'], 'Parsed input hash changed')
            inp = repair.read(folder / 'input.json')
            original_source = (folder / 'Original.lean').read_text()
            require(base.sha(original_source) == inp['original_sha256'] == original[i]['lean_sha256'], 'Original source SHA mismatch')
            source = (folder / 'Solution.lean').read_text()
            digest = base.sha(source)
            require(status['verified'] and status['source_sha256'] == digest, 'Accepted source/status mismatch')
            receipt_path = Path(status['receipt']).resolve()
            require(receipt_path.is_relative_to((folder / 'checks').resolve()), 'Receipt outside this case checks')
            receipt = repair.read(receipt_path)
            require(receipt['task_id'] == tid and receipt['source_sha256'] == digest, 'Receipt source/task mismatch')
            require(receipt['scope_gate'] == 'construction_only_original_proof_terms', 'Unexpected checker scope')
            require(receipt['passed'] and kernel.valid_report(receipt['kernel_report']), 'Frozen checker did not pass')
            kr = receipt['kernel_report']
            require(kr['source_sha256'] == digest and kr['n_theorems'] > 0 and kr['n_theorems'] == kr['n_honest'], 'Not all named theorems honest')
            expected_names = []
            for proof in inp['ranges'] + inp['preserved_proofs']:
                if proof.get('anonymous'):
                    continue
                name = re.search(r'\b(?:theorem|lemma)\s+([^\s(:]+)', proof['statement'])
                require(name is not None, 'Unsupported original named theorem syntax')
                expected_names.append(name[1])
            require(Counter(expected_names) == Counter(theorem['name'] for theorem in kr['theorems']),
                    'Checked named theorem set differs from the exact original parser declarations')
            require((receipt_path.parent / 'Solution.lean').read_text() == source, 'Checked snapshot differs')
            module = Path(kr['evidence_dir']) / 'original.olean'
            require(base.sha(module.read_bytes()) == kr['compiled_module_sha256'], 'Compiled artifact hash differs')
            report['kernel_verified'] = True
            checked_source = source
            scope = scoped_proofs(original_source, checked_source, inp, repair.prior.automation,
                                  kernel.strip_comments, require_inline=False)
            binding = dict(method='byte_identical_checked_source', checked_source_sha256=digest,
                           annotated_source_sha256=digest, original_bytes_preserved=True,
                           noncomment_tokens_unchanged=True, insertions=[], compiler_calls=0, model_calls=0)
            if not scope['english_inline_proof_comments']:
                source, binding = annotate_checked_source(checked_source, scope['replaced_proofs'],
                    lambda text: kernel.strip_comments(text, keep_literals=True))
                digest = base.sha(source)
                scope = scoped_proofs(original_source, source, inp, repair.prior.automation, kernel.strip_comments)
            require(scope['english_inline_proof_comments'] > 0, 'Final training source lacks meaningful English inline proof comments')
            binding.update(kernel_receipt_sha256=base.sha(receipt_path.read_bytes()),
                           kernel_checked_source_sha256=receipt['kernel_report']['source_sha256'])
            envelope = repair.read(folder / 'envelope.json')
            require(envelope['prefix'] + original_source + envelope['suffix'] == original[i]['messages'][-1]['content'], 'Original FILE envelope mismatch')
            answer = envelope['prefix'] + source + envelope['suffix']
            require(extract_lean(answer, [envelope['path']], root=RUN / 'repo/external/veribench').lean == source, 'Frozen FILE extraction differs')
            messages = [dict(message) for message in original[i]['messages']]
            require([message['role'] for message in messages] == ['system', 'user', 'assistant'], 'Unexpected original conversation roles')
            messages[-1]['content'] = answer
            checked = render(tok, messages[0]['content'], messages[1]['content'], answer)
            require(all(checked[key] for key in ('byte_prefix_ok', 'token_prefix_ok', 'span_matches_expected', 'within_cap')), 'Actual Qwen FILE/chat-template gate failed')
            require(checked['n_assistant_tokens'] < 1000, 'Assistant loss span is not below 1000 tokens')
            row = dict(original[i], uid=f'tiny_v21:{i:04d}:{tid}', pool='tiny', example_index=i,
                messages=messages, lean_sha256=digest, response_sha256=base.sha(answer),
                n_prompt_tokens=checked['n_prompt_tokens'], n_assistant_tokens=checked['n_assistant_tokens'],
                n_total_tokens=checked['n_total_tokens'], current_kernel_verified=True,
                automation_cleanup_v21=dict(state=status['state'], model=status.get('model'), effort=status.get('effort'),
                    receipt=str(receipt_path), receipt_sha256=base.sha(receipt_path.read_bytes()),
                    kernel_checked_source_sha256=receipt['kernel_report']['source_sha256'],
                    kernel_evidence_kind='checked_original_plus_comment_insertion_identity' if binding['insertions'] else 'exact_checked_source',
                    comment_only_annotation=bool(binding['insertions']),
                    original_response_sha256=base.sha(original[i]['messages'][-1]['content']),
                    no_automated_fallback=True, original_nonproof_bytes_unchanged=True,
                    header_proof_sketch=True, english_inline_proof_comments=scope['english_inline_proof_comments']))
            row.pop('lean_norm_hash', None)
            report.update(format='PASS', source_sha256=digest, n_assistant_tokens=checked['n_assistant_tokens'])
            candidates.append((row, source, receipt_path, scope, binding))
        except Exception as exc:
            report['exclusion'] = repr(exc)
        reports.append(report)
    screening = screen({str(row['example_index']): row['messages'][1]['content'] + '\n' + row['messages'][2]['content'] for row,_,_,_,_ in candidates}, protected)
    clean = set(screening['clean_ids'])
    byindex = {row['example_index']:row for row in reports}
    accepted, portable = [], []
    for row, source, receipt_path, scope, binding in candidates:
        report = byindex[row['example_index']]
        if str(row['example_index']) not in clean:
            report['exclusion'] = 'Protected exact/near overlap screen'
            continue
        key, prompt = source_key(source), row['messages'][1]['content']
        duplicate = seen_source.get(key) or seen_prompt.get(prompt)
        if duplicate is not None:
            report['exclusion'] = f'Global duplicate of {duplicate}'
            continue
        proof = copy_receipt(final, ROOT / 'cases' / row['task_id'], row, receipt_path, scope, source, binding)
        row['automation_cleanup_v21']['portable_receipt'] = proof['portable_receipt']
        row['automation_cleanup_v21']['portable_comment_binding'] = proof['portable_comment_binding']
        portable.append(proof)
        accepted.append(row)
        report.update(admitted=True, exclusion='')
        seen_source[key] = seen_prompt[prompt] = row['uid']
    text = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in accepted)
    (final / 'tiny_training.jsonl').write_text(text)
    excluded = [row for row in reports if not row['admitted']]
    (final / 'excluded_rows.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in excluded))
    with (final / 'row_results.csv').open('w') as stream:
        fields = list(reports[0])
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(reports)
    repair.write(final / 'protected_screen.json', screening)
    repair.write(final / 'proof_receipts_manifest.json', portable)
    require(len(accepted) + len(excluded) == 500, 'Declared outcomes do not sum to 500')
    summary = dict(state='DONE' if not excluded else 'DONE_WITH_EXCLUSIONS', declared=500, accounted=500,
        accepted=len(accepted), excluded=len(excluded), kernel_verified=sum(row['kernel_verified'] for row in reports),
        assistant_loss_tokens=sum(row['n_assistant_tokens'] for row in accepted),
        comment_only_annotated=sum(row['automation_cleanup_v21']['comment_only_annotation'] for row in accepted),
        training_sha256=base.sha(text), row_results_sha256=base.sha((final / 'row_results.csv').read_bytes()),
        proof_receipts_manifest_sha256=base.sha((final / 'proof_receipts_manifest.json').read_bytes()),
        protected_screen_sha256=base.sha((final / 'protected_screen.json').read_bytes()),
        freeze_sha256=base.sha((final / 'freeze.json').read_bytes()), original_pool_sha256=repair.SOURCE_SHA,
        protected_references=764, protected_exact=screening['n_exact'], protected_near=screening['n_near'],
        no_automated_fallbacks=True, original_system_user_and_nonproof_bytes_unchanged=True,
        assistant_token_cap_exclusive=1000, total_token_cap=16384, compiler_calls=0, model_calls=0,
        receipt_meaning='Existing exact checked-source frozen-kernel evidence; any newly inserted comments have a separate source hash and exact insertion/token-identity binding. Annotated sources are not recompiled; English commentary semantics are not independently verified.',
        observed_unix=time.time())
    repair.write(final / 'completion.json', summary)
    final.rename(published)
    repair.write(ROOT / 'completion.json', summary)
    print(json.dumps(summary), flush=True)


def controls():
    original = 'import Mathlib\n\ndef ident (n : Nat) := n\ntheorem ident_self (n : Nat) : ident n = n := by\n  simp [ident]\n'
    start = original.index('by\n')
    inp = dict(ranges=[dict(index=0,start=start,end=len(original),original=original[start:])], preserved_proofs=[])
    candidate = original[:len('import Mathlib\n')] + '\n/- Proof sketch:\nUnfold the identity definition.\nBoth sides are definitionally equal.\n-/\n' + original[len('import Mathlib\n'):start] + 'by\n  -- Both sides reduce to the same expression.\n  rfl\n'
    automation = lambda source: re.findall(r'\b(?:simp|omega|native_decide)\b', re.sub(r'--[^\n]*','',source))
    strip = lambda source: re.sub(r'--[^\n]*','',source)
    scoped_proofs(original,candidate,inp,automation,strip)
    rejected = {}
    variants = dict(implementation=candidate.replace(':= n\n',':= n + 1\n'), statement=candidate.replace('ident n = n','ident n = n + 1'),
        automation=candidate.replace('  rfl','  simp [ident]'), missing_inline=candidate.replace('  -- Both sides reduce to the same expression.\n',''),
        missing_sketch=candidate.replace('Proof sketch:','Explanation:'), sorry=candidate.replace('  rfl','  sorry'),
        declaration_injection=candidate+'def extra := 1\n', unterminated_comment=candidate+'/-')
    for name, source in variants.items():
        try:
            scoped_proofs(original,source,inp,automation,strip)
        except ValueError:
            rejected[name] = True
        else:
            raise AssertionError(f'Negative admission control accepted: {name}')
    tail = '\nexample : ident 2 = 2 := by native_decide\n'
    extended = original + tail
    preserved_start = len(original) + tail.index('by ')
    native = dict(index=1, start=preserved_start, end=len(extended), original=extended[preserved_start:], anonymous=True)
    with_native = dict(ranges=inp['ranges'], preserved_proofs=[native])
    scoped_proofs(extended,candidate+tail,with_native,automation,strip)
    for name, changed in (
        ('named_native_exception_rejected',dict(native,anonymous=False)),
        ('preserved_simp_rejected',dict(native,original=native['original'].replace('native_decide','simp'))),
    ):
        old = extended if name.startswith('named') else extended[:preserved_start]+changed['original']
        new = candidate+tail if name.startswith('named') else (candidate+tail).replace('native_decide','simp')
        changed = dict(changed,end=len(old))
        try:
            scoped_proofs(old,new,dict(ranges=inp['ranges'],preserved_proofs=[changed]),automation,strip)
        except ValueError:
            rejected[name] = True
        else:
            raise AssertionError(f'Negative preserved-proof control accepted: {name}')
    from add_missing_inline import annotate_checked_source
    bare = candidate.replace('  -- Both sides reduce to the same expression.\n', '')
    preliminary = scoped_proofs(original,bare,inp,automation,strip,require_inline=False)
    annotated, binding = annotate_checked_source(bare,preliminary['replaced_proofs'],strip)
    scoped_proofs(original,annotated,inp,automation,strip)
    require(binding['checked_source_sha256'] != binding['annotated_source_sha256'], 'Two-source hash control failed')
    print(json.dumps(dict(passed=True, positive_scope=True, original_anonymous_native_exception=True,
                         comment_only_two_source_admission=True, negative_controls=rejected, compiler_calls=0, model_calls=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, help='Exact frozen training JSONL used as global-dedup baseline')
    parser.add_argument('--controls', action='store_true')
    args = parser.parse_args()
    if args.controls:
        controls()
    else:
        require(args.baseline is not None, '--baseline is required')
        ROOT.mkdir(parents=True, exist_ok=True)
        with (ROOT / 'finalization.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finalize(args.baseline)
