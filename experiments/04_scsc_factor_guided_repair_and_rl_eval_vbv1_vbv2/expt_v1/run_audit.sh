#!/usr/bin/env bash
# TLDR: Run one bounded deterministic inventory and preserve its exit status and execution hashes.
set -u
cd "$(dirname "$0")"
mkdir -p results
if [ -e results/execution_receipt.json ]; then
  echo 'Existing receipt retained; refusing to overwrite it.' >&2
  exit 2
fi
started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
/usr/bin/timeout 300 /usr/bin/python3 audit_existing.py --root "$PWD" > results/execution.log 2>&1
result_code=$?
/usr/bin/python3 - "$started_utc" "$result_code" <<'PY'
import datetime,hashlib,json,pathlib,socket,sys
p=pathlib.Path('.')
d={'started_utc':sys.argv[1], 'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exit_code':int(sys.argv[2]),'host':socket.gethostname(),'executor':'/usr/bin/python3','session':'rl4cv-azalia-artifact-audit','model_calls':0,'gpu_hours':0,'provider_charges_usd':0,'max_seconds':300,'hashes':{}}
for name in ['audit_existing.py','input_manifest.json','../PROTOCOL.md','results/audit.json','results/RESULTS_existing_artifacts.md']:
 f=p/name;d['hashes'][name]=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
(p/'results/execution_receipt.json').write_text(json.dumps(d,indent=2)+'\n')
PY
exit "$result_code"
