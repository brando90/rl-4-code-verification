"""Freeze Night 6 predictions P1, P2, P3, P5 (with the hashes of the protocol, code and job list) before any outcome exists."""
import hashlib
import json
from pathlib import Path
from rl4cv.forecast import freeze_forecast
from . import night6 as n6

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

if __name__ == '__main__':
    if list((HERE / 'results').glob('*.json')):
        raise SystemExit('outcomes already exist; a prospective freeze is no longer possible')
    jobs = [n6.job_name(j) for j in n6.jobs()]
    receipt = freeze_forecast({
        'what': 'Night 6 predictions, written before any Night 6 trajectory outcome was read',
        'predictions': {
            'P1': {'claim': 'dense (A) RMSE <= independent (B) RMSE + one seed SD for the U(C) curve and for the Eq. 7 forecast at n3', 'p_holds': 0.8},
            'P2': {'claim': '50% prefix Eq. 7 fit has C_max RMSE <= 1.25 x full fit and rank accuracy within 0.10 of the full fit', 'p_criterion1': 0.6, 'p_criterion2': 0.6, 'p_holds': 0.4,
                   'expect': 'saturating curves extrapolate well in the toy (KL anchor); law rank accuracy near chance for both fits'},
            'P3': {'claim': 'rolling rho, H form beats zero, previous-increment and start-only baselines in both CVs', 'p_holds': 0.2,
                   'expect': 'increments are noise dominated; no advantage'},
            'P5': {'claim': 'schedule effect differs between cosine and constant arms with the interval excluding 0 at b = 100 and 200, same sign', 'p_holds': 0.6,
                   'expect_direction': 'negative (unannealed long cosine run below its annealed fresh short run)'}},
        'input_hashes': {'PROTOCOL.md': sha(HERE / 'PROTOCOL.md'), 'analyze6.py': sha(HERE / 'analyze6.py'), 'night6.py': sha(HERE / 'night6.py'),
                         'policy6.py': sha(HERE / 'policy6.py'), 'job_list_sha256': hashlib.sha256('\n'.join(jobs).encode()).hexdigest(), 'n_jobs': len(jobs)},
    }, HERE / 'forecast', 'forecast_night6')
    print(json.dumps(receipt))
