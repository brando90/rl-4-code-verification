"""TLDR: Owned collect-only service lifecycle for exact six-rating online batches, registered on the hosted Valkyrie Tracker (10-14-2026)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import owned_processes as children

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))
from rl4cv import valkyrie_hosted as hosted  # noqa: E402

# The frozen experiment08 helper still reads and writes a private valkyrie.yaml. The hosted CLI ignores that file,
# so it is only the helper's scratch; the service is registered on the Tracker after the helper returns.
PROVIDER_ENV = ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'MODEL_GATEWAY_API_KEY',
                'CLAUDE_CODE_OAUTH_TOKEN', 'ANTHROPIC_AUTH_TOKEN', 'PYTHONPATH', 'PYTHONHOME')


class RegisteredSubprocess:
    """Preserve the frozen deployment implementation; register children before exec."""
    def __getattr__(self, name):
        return getattr(subprocess, name)

    def Popen(self, args, **kwargs):
        kind = 'e09_judge_tunnel' if 'cloudflared' in str(args[0]) else 'e09_judge_service'
        return children.spawn(args, kind=kind, **kwargs)


class JudgeService:
    def __init__(self):
        self.records = []

    def deploy(self, manifest):
        from deploy_judge_e09 import service
        identity = hosted.preflight(require_login=True, env=hosted.cli_env(PROVIDER_ENV))
        assert identity['verdict'] == 'PASS', 'Hosted Valkyrie preflight failed: ' + '; '.join(identity['problems'])
        scratch = children.ROOT / 'private/valkyrie.yaml'
        if not scratch.is_file():
            scratch.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            scratch.write_text('{}\n')
            os.chmod(scratch, 0o600)
        service.HOST_CONFIG = scratch
        service.LAKE_DIR = children.ROOT / 'lean_runtime'
        service.PACK = Path(manifest['pack_abs'])
        service.BENCHMARK = manifest['benchmark']
        service.PORT = 9741
        service.NAME = 'e09_' + manifest['batch_id'][:16]
        service.EXPECTED_TASKS = manifest['n_tasks']
        service.PUBLIC_RECEIPT = children.ROOT / 'receipts/judge_online/service.json'
        service.subprocess = RegisteredSubprocess()
        with children.registry() as data:
            before = {(r['pid'], r['start_ticks']) for r in data.get('processes', [])}
        try:
            assert service.cmd_deploy(None) == 0
        finally:
            with children.registry() as data:
                self.records = [r for r in data.get('processes', [])
                                if (r['pid'], r['start_ticks']) not in before
                                and r['kind'] in ('e09_judge_service', 'e09_judge_tunnel')]
        self.receipt = children.ROOT / 'private' / f'deployment_{service.NAME}.json'
        assert len(self.records) == 2 and all(children.alive(r) for r in self.records)
        receipt = json.loads(self.receipt.read_text())
        bearer_file = children.ROOT / 'private' / f'service_bearer_{service.NAME}'
        registration = hosted.register_service(manifest['benchmark'], receipt['tunnel_url'], bearer_file.read_text().strip(),
                                               env=hosted.cli_env(PROVIDER_ENV))
        hosted.record_local(children.ROOT / 'private/services.json', manifest['benchmark'], receipt['tunnel_url'], bearer_file, registration)
        receipt.update(valkyrie_identity=identity, valkyrie_registration=registration)
        temp = self.receipt.with_suffix('.tmp')
        temp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        temp.replace(self.receipt)

    def finish(self, manifest):
        # Called only once both native rating runs are terminal. A coordinator
        # interruption or partially admitted batch preserves the healthy service.
        for record in reversed(self.records):
            children.stop(record)
        from datetime import datetime, timezone
        receipt = json.loads(self.receipt.read_text())
        receipt.update(torn_down_utc=datetime.now(timezone.utc).isoformat(),
                       identity_checked_cleanup=True)
        temp = self.receipt.with_suffix('.tmp')
        temp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        temp.replace(self.receipt)
