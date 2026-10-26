#!/usr/bin/env bash
# TLDR: Run the repository's deterministic test gate in the existing Linux environment and retain its exact exit status.
set -u
RUN=/lfs/skampere1/0/eth127/rl4cv_tiny_training
TEST_REPO="$RUN/test_checkout/depth/rl-4-code-verification"
export CUDA_VISIBLE_DEVICES="" PYTHONPATH="$TEST_REPO/src"
export PATH="$RUN/checks_env/bin:$PATH"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
# These optional experiment-13 fixtures are private to another account. Use its
# documented absent-prerequisite skip; this experiment has separate real scorer controls.
export E13_CONTROLS_DIR="$RUN/unavailable_e13_integration_controls"
export GIT_CONFIG_COUNT=2
export GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_KEY_1=safe.directory
export GIT_CONFIG_VALUE_0=/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench
export GIT_CONFIG_VALUE_1=/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench_scorer
cd "$TEST_REPO" || exit 1
/lfs/skampere1/0/eth127/rl4cv_tiny_training/checks_env/bin/python -m pytest -q > "$RUN/make_test.log" 2>&1
result=$?
printf '{"exit_code":%s}\n' "$result" > "$RUN/make_test_exit.json"
exit "$result"
