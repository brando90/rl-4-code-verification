"""Frozen local features; category vocabulary and all numeric scaling fit on training folds only."""
import io
import tokenize
import numpy as np


def extract(python_source,industry_domain,reference_theorem_types):
    # Reference theorem types are supplied by the pinned scorer's theorem-type extractor.
    tokens=list(tokenize.generate_tokens(io.StringIO(python_source).readline))
    omitted={tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT}
    return {'python_character_count':len(python_source),
            'python_token_count':sum(t.type not in omitted for t in tokens),
            'industry_domain':str(industry_domain),'reference_theorem_count':len(reference_theorem_types)}


def matrices(training,target):
    """One-hot categorical features avoid treating domain labels as ordinal numbers."""
    keys=('python_character_count','python_token_count','reference_theorem_count')
    categories=sorted({r['industry_domain'] for r in training})
    def encode(rows):
        return np.asarray([[*[float(r[k]) for k in keys],*[float(r['industry_domain']==c) for c in categories]] for r in rows])
    return encode(training),encode(target),{'domain_categories':categories,'unknown_domain':'all-zero indicator vector'}
