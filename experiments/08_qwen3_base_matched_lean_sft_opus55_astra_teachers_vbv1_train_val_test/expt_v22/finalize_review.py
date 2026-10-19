"""Admit the closed Sol-review failure cohort as an immutable tiny-data delta.

The strict per-row admission body is adapted from pinned V21 source. Existing
receipt/source, comment, format, protection and dedup checks remain unchanged.
No compilation or model work is launched by this file.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import review_failures as repair
ROOT,RUN,base=repair.ROOT,repair.RUN,repair.base
V21=HERE.parent/'expt_v21'
V21_FINALIZER_SHA='53b2260793a443c82e494672513c1ea57dd856335b0040ed976f7bb45bebc00e'
V21_ADAPTER_SHA='ad8bea2bd9e5d7c06294a4a297ead1b236bcef733fabce2de23961e6bef32253'
if base.sha((V21/'finalize_tiny.py').read_bytes())!=V21_FINALIZER_SHA:raise ValueError('Pinned V21 admission helpers changed')
if base.sha((V21/'add_missing_inline.py').read_bytes())!=V21_ADAPTER_SHA:raise ValueError('Pinned V21 comment adapter changed')
spec=importlib.util.spec_from_file_location('sol_review_v21_admission_helpers',V21/'finalize_tiny.py')
shared=importlib.util.module_from_spec(spec);sys.modules[spec.name]=shared;spec.loader.exec_module(shared)
# The imported helper has its own V21 context. Restore this process's proof builder
# to V22; no V21 disk inputs or worker processes are changed by these imports.
repair.prior.ROOT=ROOT
require=shared.require
scoped_proofs=shared.scoped_proofs
protected_references=shared.protected_references
copy_receipt=shared.copy_receipt
BASELINE_SHA=shared.BASELINE_SHA
ACCEPTED=shared.ACCEPTED
TERMINAL_EXCLUSION=shared.TERMINAL_EXCLUSION

def validate_cohort(manifest,closure,first_manifest,first_statuses):
    require(closure['state']=='CLOSED','Sol review cohort is still growing')
    require(closure['declared']==len(manifest),'Closed cohort count differs from manifest')
    require(len(first_manifest)==500,'First-pass source manifest changed')
    original={row['task_id']:row['example_index'] for row in first_manifest}
    require(len(original)==500 and set(original.values())==set(range(500)),'First-pass source indices are not complete')
    ids=[row['task_id'] for row in manifest]
    indices=[row['example_index'] for row in manifest]
    require(len(ids)==len(set(ids)) and len(indices)==len(set(indices)),'Repeated task or source index in review cohort')
    expected={tid for tid,state in first_statuses.items() if state['state']=='EXCLUDED_BOUNDED_REPAIR'}
    require(set(ids)==expected,'Review cohort differs from all terminal V21 proof failures')
    require(all(original.get(row['task_id'])==row['example_index'] for row in manifest),'Review original source-index mapping changed')
    return len(manifest)

def finalize(baseline):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    repair.assert_inspector()
    require(base.sha(repair.SOURCE.read_bytes()) == repair.SOURCE_SHA, 'Original tiny corpus hash changed')
    original = base.read_rows(repair.SOURCE)
    manifest = repair.read(ROOT / 'manifest.json')
    dispatch = repair.read(ROOT / 'dispatch.json')
    require(dispatch['model'] == 'gpt-6.1-sol' and dispatch['effort'] == 'high', 'Unexpected review model/effort')
    require(dispatch['max_new_candidate_hashes_per_case'] == 4 and dispatch['max_cli_attempts_per_case'] == 2,
            'Recorded separate review limits changed')
    require(len(original) == 500, 'Original tiny source pool changed')
    closure_path = ROOT / 'cohort_closed.json'
    closure = repair.read(closure_path)
    first_completion_path = repair.OLD / 'completion.json'
    first_completion = repair.read(first_completion_path)
    require(first_completion['state'] in ('DONE', 'DONE_WITH_EXCLUSIONS'), 'V21 is not finally published')
    require(first_completion['declared'] == first_completion['accounted'] == 500, 'V21 declared-cohort accounting changed')
    require(base.sha(first_completion_path.read_bytes()) == closure['v21_completion_sha256'], 'V21 completion differs from cohort closure')
    require(base.sha((ROOT / 'manifest.json').read_bytes()) == closure['manifest_sha256'], 'Review manifest differs from cohort closure')
    first_manifest = repair.read(repair.OLD / 'manifest.json')
    first_statuses = {row['task_id']:repair.read(repair.OLD / 'cases' / row['task_id'] / 'status.json') for row in first_manifest}
    declared = validate_cohort(manifest, closure, first_manifest, first_statuses)
    for item in manifest:
        prior_status = repair.OLD / 'cases' / item['task_id'] / 'status.json'
        require(base.sha(prior_status.read_bytes()) == item['prior_failure_status_sha256'], 'Original V21 terminal failure receipt changed')
        require(repair.read(ROOT / 'cases' / item['task_id'] / 'status.json')['state'] in ACCEPTED | TERMINAL_EXCLUSION,
                'Not every closed review case has reached a terminal outcome')
    published = ROOT / 'final'
    require(not published.exists(), 'Final outputs already exist; preserve immutable prior admission')
    final = ROOT / f'final_build_{int(time.time())}_{os.getpid()}'
    final.mkdir()
    (final / 'driver_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (final / 'add_missing_inline.py').write_bytes((V21 / 'add_missing_inline.py').read_bytes())
    (final / 'v21_finalizer_helpers.py').write_bytes((V21 / 'finalize_tiny.py').read_bytes())
    (final / 'review_manifest.json').write_bytes((ROOT / 'manifest.json').read_bytes())
    (final / 'cohort_closed.json').write_bytes(closure_path.read_bytes())
    (final / 'v21_completion.json').write_bytes(first_completion_path.read_bytes())
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
    first_training = repair.OLD / 'final/tiny_training.jsonl'
    require(base.sha(first_training.read_bytes()) == first_completion['training_sha256'], 'V21 accepted training snapshot changed')
    first_pass = base.read_rows(first_training)
    require(len(first_pass) == first_completion['accepted'], 'V21 accepted row count differs')
    require(not ({row['task_id'] for row in first_pass} & {row['task_id'] for row in manifest}), 'Review delta overlaps V21 accepted task IDs')

    def source_key(source):
        return ' '.join(kernel.strip_comments(source, keep_literals=True).split())

    seen_source, seen_prompt = {}, {}
    for row in prior + first_pass:
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
    repair.write(final / 'freeze.json', dict(declared=declared, source_sha256=repair.SOURCE_SHA,
        cohort_closed_sha256=base.sha(closure_path.read_bytes()), v21_completion_sha256=base.sha(first_completion_path.read_bytes()),
        v21_helpers_sha256=V21_FINALIZER_SHA, v21_training_sha256=base.sha(first_training.read_bytes()), v21_training_rows=len(first_pass),
        manifest_sha256=base.sha((ROOT / 'manifest.json').read_bytes()), dispatch_sha256=base.sha((ROOT / 'dispatch.json').read_bytes()),
        driver_sha256=base.sha(Path(__file__).read_bytes()), inspector_sha256=repair.core.INSPECTOR_SHA,
        comment_adapter_sha256=base.sha((V21 / 'add_missing_inline.py').read_bytes()),
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
            row = dict(original[i], uid=f'tiny_v22:{i:04d}:{tid}', pool='tiny', example_index=i,
                messages=messages, lean_sha256=digest, response_sha256=base.sha(answer),
                n_prompt_tokens=checked['n_prompt_tokens'], n_assistant_tokens=checked['n_assistant_tokens'],
                n_total_tokens=checked['n_total_tokens'], current_kernel_verified=True,
                automation_cleanup_v22=dict(state=status['state'], model=status.get('model'), effort=status.get('effort'),
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
        package = final / Path(proof['portable_receipt']).parent
        extra = {
            'prior_failures.json': ROOT / 'cases' / row['task_id'] / 'prior_failures.json',
            'v21_terminal_status.json': repair.OLD / 'cases' / row['task_id'] / 'status.json',
        }
        files = repair.read(package / 'files.json')
        for name, source_path in extra.items():
            require(source_path.is_file() and not source_path.is_symlink(), 'Missing regular review provenance file')
            (package / name).write_bytes(source_path.read_bytes())
            files[name] = base.sha((package / name).read_bytes())
        repair.write(package / 'files.json', files)
        proof['files_manifest_sha256'] = base.sha((package / 'files.json').read_bytes())
        row['automation_cleanup_v22']['portable_receipt'] = proof['portable_receipt']
        row['automation_cleanup_v22']['portable_comment_binding'] = proof['portable_comment_binding']
        portable.append(proof)
        accepted.append(row)
        report.update(admitted=True, exclusion='')
        seen_source[key] = seen_prompt[prompt] = row['uid']
    text = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in accepted)
    (final / 'repaired_tiny_training.jsonl').write_text(text)
    excluded = [row for row in reports if not row['admitted']]
    (final / 'excluded_rows.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in excluded))
    with (final / 'row_results.csv').open('w') as stream:
        fields = list(reports[0]) if reports else ['task_id','example_index','state','kernel_verified','admitted','exclusion','format','source_sha256','n_assistant_tokens']
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(reports)
    repair.write(final / 'protected_screen.json', screening)
    repair.write(final / 'proof_receipts_manifest.json', portable)
    require(len(accepted) + len(excluded) == declared, 'Declared review outcomes do not sum to the closed cohort')
    summary = dict(state='DONE' if not excluded else 'DONE_WITH_EXCLUSIONS', declared=declared, accounted=len(reports),
        phase='Separate Sol review delta of terminal V21 proof failures; not an automatic training launch',
        v21_completion_sha256=base.sha(first_completion_path.read_bytes()), v21_accepted_rows=len(first_pass),
        accepted=len(accepted), excluded=len(excluded), kernel_verified=sum(row['kernel_verified'] for row in reports),
        assistant_loss_tokens=sum(row['n_assistant_tokens'] for row in accepted),
        comment_only_annotated=sum(row['automation_cleanup_v22']['comment_only_annotation'] for row in accepted),
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
    shared.controls()
    first=[dict(task_id=f't{i}',example_index=i) for i in range(500)]
    states={row['task_id']:dict(state='ACCEPTED_REPAIRED') for row in first}
    for i in (3,17):states[f't{i}']=dict(state='EXCLUDED_BOUNDED_REPAIR')
    manifest=[dict(task_id=f't{i}',example_index=i) for i in (3,17)]
    closed=dict(state='CLOSED',declared=2)
    require(validate_cohort(manifest,closed,first,states)==2,'Sparse original-index cohort control failed')
    variants=[(manifest,dict(closed,state='OPEN')),(manifest[:1],dict(closed,declared=1)),
              (manifest+[dict(task_id='t42',example_index=42)],dict(closed,declared=3)),
              ([dict(task_id='t3',example_index=17),manifest[1]],closed)]
    for rows,closure in variants:
        try:validate_cohort(rows,closure,first,states)
        except ValueError:pass
        else:raise AssertionError('Invalid review-cohort control accepted')
    all_pass={row['task_id']:dict(state='ACCEPTED_REPAIRED') for row in first}
    require(validate_cohort([],dict(state='CLOSED',declared=0),first,all_pass)==0,'Empty delta control failed')
    print(json.dumps(dict(passed=True,review_cohort_controls=6,source_helper_sha256=V21_FINALIZER_SHA,
        comment_adapter_sha256=V21_ADAPTER_SHA,compiler_calls=0,model_calls=0)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--controls',action='store_true')
    args=parser.parse_args()
    if args.controls:controls()
    else:
        require(args.baseline is not None,'--baseline is required')
        ROOT.mkdir(parents=True,exist_ok=True)
        with (ROOT/'finalization.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finalize(args.baseline)
