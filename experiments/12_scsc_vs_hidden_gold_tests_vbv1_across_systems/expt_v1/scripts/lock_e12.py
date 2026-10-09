"""Lock the A2 adapter and exact inputs only after every complete frozen control passes and all three forecasts verify."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from extract_hidden_tests import PHASE
from rl4cv.forecast import verify_forecast


def main():
    forecasts={}
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1','e12_phase_a_forecast_amendment_A2'):
        path=PHASE/'forecasts'/(name+'.json');assert verify_forecast(path)
        forecasts[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    controls=json.loads((PHASE/'results/controls_e12.json').read_text())
    assert controls['complete'] and controls['n_completed']==50 and controls['all_controls_pass']
    for name,digest in controls['source_hashes'].items():assert hashlib.sha256((PHASE/'scripts'/name).read_bytes()).hexdigest()==digest
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert not subprocess.check_output(['git','status','--porcelain','--',str(PHASE/'scripts')],text=True).strip()
    protocol=PHASE.parent/'PROTOCOL.md';text=protocol.read_text();assert '**Lock line:** `NOT LOCKED`' in text
    timestamp=datetime.now(timezone.utc).isoformat()
    line=f'**Lock line:** `LOCKED {timestamp} at commit {commit}` — all four round-{controls["round"]} A2 controls pass; exact adapter and input hashes in `expt_v1/results/protocol_lock.json`. No real-candidate hidden outcome exists at lock.'
    lines=text.splitlines();lines=[line if item.startswith('**Lock line:**') else item for item in lines]
    record={'timestamp_utc':timestamp,'code_commit':commit,'control_round':controls['round'],
            'source_hashes':controls['source_hashes'],'forecast_file_hashes':forecasts,
            'input_hashes':{name:hashlib.sha256((PHASE/'results'/name).read_bytes()).hexdigest() for name in
                           ['input_manifest_A1.json','secondary_manifest_A1.json','hidden_tests_manifest.json','control_selection.json','controls_e12.json']}}
    target=PHASE/'results/protocol_lock.json';assert not target.exists()
    target.write_text(json.dumps(record,indent=2)+'\n');protocol.write_text('\n'.join(lines)+'\n')
    print(json.dumps(record))


if __name__=='__main__':main()
