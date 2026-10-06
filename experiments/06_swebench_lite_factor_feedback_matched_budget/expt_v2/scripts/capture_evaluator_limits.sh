#!/usr/bin/env bash
# Capture one live official-evaluator container's Docker-enforced resource limits.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 RUNTIME_ROOT" >&2
  exit 64
fi

runtime_root=$1
output="$runtime_root/evaluator_controls/observed_container_limits.json"
deadline=$((SECONDS + 3600))
while (( SECONDS < deadline )); do
  while read -r container_id; do
    [[ -n "$container_id" ]] || continue
    docker inspect "$container_id" | jq '.[0] | {
      observed_at: now | todateiso8601,
      container_id: .Id,
      name: .Name,
      state: .State.Status,
      nano_cpus: .HostConfig.NanoCpus,
      memory_bytes: .HostConfig.Memory
    }' >"$output"
    exit 0
  done < <(docker ps -q --filter 'name=sweb.eval')
  sleep 0.2
done

echo "no official evaluator container observed before deadline" >&2
exit 1
