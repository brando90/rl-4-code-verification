"""Four-token HMM continuations with exact forward scores and deterministic mixtures."""
from dataclasses import dataclass, asdict
from importlib import import_module
import numpy as np

base = import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v1.ginc_toy')
V, BOS, VOCAB = base.V, base.BOS, base.VOCAB
Concept, EnvSpec = base.Concept, base.EnvSpec
make_concept, concept_bank = base.make_concept, base.concept_bank
sample_sequences, pretraining_docs = base.sample_sequences, base.pretraining_docs
K = 4
SETTINGS = [(s, sh) for s in (4, 8, 12) for sh in (2., 4., 8.)]

@dataclass(frozen=True)
class Mixture:
    name: str
    components: tuple[EnvSpec, ...]
    weights: tuple[float, ...]
    def __post_init__(self):
        w = np.array(self.weights)
        if len(w) != len(self.components) or not len(w) or np.any(w < 0) or not np.isclose(w.sum(), 1):
            raise ValueError('mixture weights must be a probability vector')
        if len({c.length for c in self.components}) != 1:
            raise ValueError('components must share prefix length')
    def to_dict(self):
        return asdict(self)

@dataclass
class Prompts:
    x: np.ndarray
    y: np.ndarray
    concept_idx: np.ndarray
    concepts: list
    oracle_logprob: np.ndarray
    entropy_mc: np.ndarray


def posterior(c, x):
    """Normalized hidden-state posterior after each observed prefix."""
    alpha = np.broadcast_to(c.pi, (len(x), c.S)).copy()
    for t in range(x.shape[1]):
        if t:
            alpha = alpha @ c.T
        alpha *= c.B[:, x[:, t]].T
        alpha /= alpha.sum(1, keepdims=True)
    return alpha


def forward_scores(c, x, y):
    """Exact p(y_t | x,y_<t,c), and log p(y | x,c); no path maximization."""
    alpha = posterior(c, x)
    probs = []
    for t in range(y.shape[1]):
        predicted = alpha @ c.T
        emission = c.B[:, y[:, t]].T
        p = (predicted * emission).sum(1)
        probs.append(p)
        alpha = predicted * emission / p[:, None]
    p = np.stack(probs, 1)
    return p, np.log(p).sum(1)


def oracle_continuation(c, x, k=K):
    """Sequential Bayes argmax labels, explicitly not the global joint MAP sequence."""
    alpha = posterior(c, x)
    ys = []
    for _ in range(k):
        predicted = alpha @ c.T
        p = predicted @ c.B
        y = p.argmax(1)
        ys.append(y)
        alpha = predicted * c.B[:, y].T
        alpha /= alpha.sum(1, keepdims=True)
    y = np.stack(ys, 1)
    return y, forward_scores(c, x, y)[1]


def conditional_entropy_mc(c, x, rng, draws=8):
    """Unbiased Monte Carlo joint conditional entropy (nats), scored by exact forward probabilities."""
    alpha = np.repeat(posterior(c, x), draws, axis=0)
    surprisal = np.zeros(len(alpha))
    for _ in range(K):
        predicted = alpha @ c.T
        p = predicted @ c.B
        y = np.minimum((rng.random(len(p))[:, None] > p.cumsum(1)).sum(1), V - 1)
        surprisal -= np.log(p[np.arange(len(p)), y])
        alpha = predicted * c.B[:, y].T
        alpha /= alpha.sum(1, keepdims=True)
    return surprisal.reshape(len(x), draws).mean(1)


def make_prompts(spec, n, seed, entropy=False):
    parts = spec.components if isinstance(spec, Mixture) else (spec,)
    weights = spec.weights if isinstance(spec, Mixture) else (1.,)
    rng = np.random.default_rng(seed)
    component = rng.choice(len(parts), n, p=weights)
    concepts, offsets = [], []
    for part in parts:
        offsets.append(len(concepts))
        concepts.extend(concept_bank(part.S, part.sharpness, part.n_concepts, part.family_seed))
    which = np.empty(n, dtype=int)
    for j, part in enumerate(parts):
        idx = np.flatnonzero(component == j)
        which[idx] = offsets[j] + rng.integers(part.n_concepts, size=len(idx))
    x, y = np.empty((n, parts[0].length), dtype=np.int64), np.empty((n, K), dtype=np.int64)
    lp, ent = np.empty(n), np.full(n, np.nan)
    # Entropy uses a separate stream so enabling diagnostics never changes prompts.
    entropy_rng = np.random.default_rng(seed + 900_000)
    for j, c in enumerate(concepts):
        idx = np.flatnonzero(which == j)
        if not len(idx):
            continue
        x[idx] = sample_sequences(c, len(idx), x.shape[1], rng)
        y[idx], lp[idx] = oracle_continuation(c, x[idx])
        if entropy:
            ent[idx] = conditional_entropy_mc(c, x[idx], entropy_rng)
    return Prompts(x, y, which, concepts, lp, ent)


def rewards(actions, labels):
    """Token partial credit and joint exact-match reward against a fixed oracle continuation."""
    matches = actions == labels[:, None, :]
    return matches.mean(-1), matches.all(-1).astype(float)

BASE = [EnvSpec(f'e{i:02d}', *v) for i, v in enumerate([
    (4, 2., 2, 4), (4, 8., 64, 16), (8, 4., 64, 12), (8, 4., 2, 12),
    (8, 2., 64, 4), (8, 8., 64, 24), (12, 4., 64, 8), (12, 8., 2, 16),
    (12, 2., 64, 24), (4, 4., 64, 24), (8, 8., 2, 4), (12, 4., 2, 4)])]
TARGET = Mixture('target_mix9_L10', tuple(EnvSpec(f't{s}_{sh}', s, sh, 64, 10) for s, sh in SETTINGS), (1/9,) * 9)


def propose_mixtures(probes):
    """Deterministic probe-only generator: high signal density with central coverage, no utilities."""
    ordered = sorted(probes, key=lambda r: r['env'])
    rho = np.array([r['rho'] for r in ordered])
    h = np.array([r['H'] for r in ordered])
    # Prefer high density, downweight the extremes of measured coverage.
    score = np.log(np.maximum(rho, 1e-12)) - 2 * abs(h - np.median(h))
    ranked = np.argsort(-score, kind='stable')
    lookup = {s.name: s for s in BASE}
    mixtures = []
    for j, count in enumerate((3, 5, 8, 12)):
        chosen = ranked[:count]
        w = np.exp(score[chosen] - score[chosen].max())
        w /= w.sum()
        # Broad concept banks and prefixes distinct from target length 10.
        parts = tuple(EnvSpec(f'm{j:02d}_{i}', lookup[ordered[i]['env']].S,
                              lookup[ordered[i]['env']].sharpness, 64, (12,16,24,8)[j]) for i in chosen)
        mixtures.append(Mixture(f'm{j:02d}', parts, tuple(float(v) for v in w)))
    return mixtures
