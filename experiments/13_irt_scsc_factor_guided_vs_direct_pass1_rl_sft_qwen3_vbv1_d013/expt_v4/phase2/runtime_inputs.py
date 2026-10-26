"""TLDR: Derive v4 configuration from the frozen local model, train prompts and official scorer inputs."""
import json
from pathlib import Path
from common import write_new

HERE=Path(__file__).resolve().parent
SOURCE=Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical/T2/attempt_3/update/runtime.json')
PREP=SOURCE.parents[4]/'technical_preparation'
# Explicit canonical preparation, independent of attempt-directory depth.
PREP=Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical_preparation')


def inputs():
    return json.loads((HERE/'runtime_inputs.json').read_text())


def prepare():
    from pilot_configuration import derive
    source=json.loads(SOURCE.read_text());context=json.loads((HERE/'context_values.json').read_text())
    policy=derive(json.loads(Path(source['policy_config']).read_text()),context)
    write_new(HERE/'policy_v4.json',policy)
    scoring=json.loads((PREP/'configuration_A6_S2_T2_A4_OBSERVATION.json').read_text())['scoring']
    config={k:source[k] for k in ('initial_model','model','tokenizer','train_ids','terminal_token_ids','run_seed','runtime_versions')}
    config.update(policy_config=str(HERE/'policy_v4.json'),context=context,
        templates=str(PREP/'inputs_v1/train_prompts.json'),probe=str(PREP/'inputs_v1/probability_probe.json'),
        scoring=scoring,vocab_size=json.loads((Path(source['model'])/'config.json').read_text())['vocab_size'])
    write_new(HERE/'runtime_inputs.json',config)
    return config

if __name__=='__main__':prepare()
