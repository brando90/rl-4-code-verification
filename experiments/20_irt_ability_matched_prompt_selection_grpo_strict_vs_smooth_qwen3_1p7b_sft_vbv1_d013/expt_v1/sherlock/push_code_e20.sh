#!/bin/bash
# TLDR: Push experiment 20 code files to Sherlock's $SCRATCH/rl4cv_sherlock/e20/code/ through the private runner: tar+gzip+base64
# the given files, split into <= 20,000-byte chunks (the runner's put limit is 24,000 bytes and refuses overwrites), put them
# under a fresh transfer id, then reassemble, hash-check and extract on Sherlock (overwriting the previous versions).
# usage: push_code_e20.sh <file>...     (run from the expt_v1 directory; paths relative to it)
set -euo pipefail
ID=$(date +%Y%m%d%H%M%S)_$$
TMP=$(mktemp -d); trap 'rm -rf $TMP' EXIT
tar czf $TMP/bundle.tgz "$@"
SHA=$(sha256sum $TMP/bundle.tgz | cut -d' ' -f1)
base64 -w0 $TMP/bundle.tgz > $TMP/bundle.b64
split -b 20000 -d -a 2 $TMP/bundle.b64 $TMP/chunk_
N=$(ls $TMP/chunk_* | wc -l)
echo "bundle $SHA ($(stat -c %s $TMP/bundle.tgz) bytes) in $N chunks, id $ID"
sherlockctl exec "mkdir -p \$SCRATCH/rl4cv_sherlock/e20/xfer/$ID" >/dev/null
for c in $TMP/chunk_*; do sherlockctl put $c /scratch/users/brando9/rl4cv_sherlock/e20/xfer/$ID/$(basename $c) | tail -1; done
sherlockctl exec "set -e; X=\$SCRATCH/rl4cv_sherlock/e20/xfer/$ID; cat \$X/chunk_* | base64 -d > \$X/bundle.tgz; echo '$SHA  bundle.tgz' | (cd \$X && sha256sum -c); mkdir -p \$SCRATCH/rl4cv_sherlock/e20/code; tar xzf \$X/bundle.tgz -C \$SCRATCH/rl4cv_sherlock/e20/code/ --no-same-owner; chmod +x \$SCRATCH/rl4cv_sherlock/e20/code/*.sh 2>/dev/null || true; ls -la \$SCRATCH/rl4cv_sherlock/e20/code/ | tail -n +2" | grep -v "^https\|^request_id"
