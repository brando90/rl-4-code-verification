#!/bin/bash
# TLDR: Build a local grading tree for Exp 25 (strict + smooth Lean scoring, no Sherlock): ROOT/code (scoring scripts) and
# ROOT/grading (bin/lake, Lean v4.22.0 toolchain, Mathlib project, frozen scorer pin 59059a20, rl4cv src).
# usage: setup_local_grading.sh <ROOT> [--from-tar <grading_tree.tar>]   run from a checkout of rl-4-code-verification.
# Without --from-tar it copies from skampere1's Exp 8 grading dir (needs those paths); with it, unpacks a tar made by
# `tar cf grading_tree.tar -C <ROOT> grading` (use this on mercury1/mercury2).
set -euo pipefail
ROOT=$(realpath -m "$1"); shift
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
E20=$(ls -d "$REPO"/experiments/20_*/expt_v1/sherlock)
mkdir -p "$ROOT/code"
# Exp 20's verbatim scoring code + this experiment's local entry points
for f in partial_credit_e20.py declaration_adapter.py DeclarationProbe.lean durable_capture.py logged_scorer_e20.py; do cp -f "$E20/$f" "$ROOT/code/$f"; done
cp -f "$HERE"/code/*.sh "$HERE"/code/partial_credit_fixedpath.py "$ROOT/code/"; chmod +x "$ROOT"/code/*.sh
if [ "${1:-}" = "--from-tar" ]; then
  tar xf "$2" -C "$ROOT"
else
  W=/lfs/skampere1/0/brando9; G="$ROOT/grading"; mkdir -p "$G/bin" "$G/elan/toolchains" "$G/rl4cv"
  SC=$W/rl4cv_e08/rl-4-code-verification/external/veribench_scorer
  [ "$(git -C "$SC" rev-parse HEAD)" = 59059a20d40adf3289869e58302169ad78102877 ] || { echo "scorer pin mismatch" >&2; exit 1; }
  cp -a "$W/.elan/toolchains/leanprover--lean4---v4.22.0" "$G/elan/toolchains/"
  cp -a "$W/rl4cv_e08/grading/lean_src" "$G/lean_src"
  mkdir -p "$G/veribench_scorer/veribench_dataset/lean_src" "$G/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code"
  cp -a "$SC/scripts" "$G/veribench_scorer/scripts"
  cp -a "$SC/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts" "$G/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts"
  cp -a "$SC/veribench_dataset/lean_src/veribench" "$G/veribench_scorer/veribench_dataset/lean_src/veribench"
fi
G="$ROOT/grading"; mkdir -p "$G/bin" "$G/rl4cv"
rm -rf "$G/rl4cv/src"; cp -a "$REPO/src" "$G/rl4cv/src"
for b in lake lean; do
  printf '#!/bin/bash\nexec "%s/elan/toolchains/leanprover--lean4---v4.22.0/bin/%s" "$@"\n' "$G" "$b" > "$G/bin/$b"; chmod +x "$G/bin/$b"
done
echo "installed: $ROOT (code/, grading/)"; "$G/bin/lean" --version; "$G/bin/lake" --version
