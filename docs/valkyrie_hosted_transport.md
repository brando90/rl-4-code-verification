# Hosted Valkyrie transport for active RL4CV launchers

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/valkyrie_hosted_transport.md>

**TLDR:** The experiment 08 version 2 service/judge and reusable Argon review launcher default to hosted Valkyrie. Historical receipts require an explicitly selected legacy executable; migration never admits a study or clears a scientific hold.

## Transport selection

Use `RL4CV_VALKYRIE_TRANSPORT=hosted` (default) and `VALKYRIE_BIN=valkyrie-hosted` on Stanford Network Analysis Project (SNAP) hosts. The independently deployed shared `valk`/`valkyrie` aliases now route through hosted compatibility; the old client is available as `valk-legacy`. Otherwise the helper discovers `valkyrie-hosted`, then uses `valkyrie`. The selected executable must expose the hosted `whoami`, `provider list`, `secret set` and `benchmark service set` commands. The installed implementation was checked at upstream revision `865135f90c4212eec497d49696af63b6d293c92c` on 10-14-2026.

Hosted mode uses supported saved login or `VALKYRIE_API_KEY` authentication and optional `VALKYRIE_URL`. It removes obsolete `VALKYRIE_ENV`, `VALKYRIE_CONFIG_PATH` and `TRACKER_SERVICE_URL` overrides, along with direct model-provider credentials. The actual Tracker and organization reported by `whoami` bind deployment and run receipts, including when the Tracker comes from a saved login. A different authenticated Tracker or organization is rejected before fetching or changing a recorded run.

Legacy access requires both variables:

```bash
export RL4CV_VALKYRIE_TRANSPORT=legacy
export VALKYRIE_BIN=/absolute/path/to/retained/legacy/valkyrie
```

Legacy mode keeps the original experiment-private YAML configuration, including unrelated registered services, and removes hosted access-key/URL overrides. Existing receipts without a `transport` field are legacy. Old historical launchers remain historical; changing the installed library does not rewrite their receipts.

## Service deployment

The updated deployers keep their live-child fences: a recorded live service/tunnel is refused before registration. Hosted deployments probe bearer authentication locally and through the tunnel, pipe the full `Bearer <token>` header to `secret set <benchmark>-service-auth`, then save the endpoint using `benchmark service set <benchmark> <url> --auth-secret <benchmark>-service-auth --auth-header Authorization`. They write no hosted YAML copy. Registration requires a saved user login; an overriding access key is rejected before secret mutation. A registration failure produces no successful deployment receipt and terminates only the new service/tunnel children.

The private deployment receipt includes the endpoint, bearer-file path and transport identity. The bearer value is excluded. The experiment 08 version 2 judge reads its service URL/authentication from that receipt in hosted mode; explicit legacy mode reads the original YAML. Teardown does not remove shared server-side settings or secrets, because that could affect concurrent consumers.

## Admission and historical access

The existing publication, route-identity, control, frozen-manifest and ambiguous-admission gates remain in force. A hosted route receipt must explicitly record `transport: hosted`, the resolved `tracker_url` and authenticated `organization`, with its existing independently verified payer/model/bundle evidence. Merely adding those fields does not establish readiness. A historical passing route receipt cannot authorize hosted calls.

Hosted deployment evidence is required for controls as well as test suites. New run/harvest/control receipts carry transport identity; controls from a different transport, Tracker or organization cannot pass the transport check. Polling and harvesting legacy runs require explicit legacy selection. No scientific model, effort, prompt, rubric, task manifest, retry budget or scoring definition changes here. The gateway secret name is supplied by the coordinator-migrated agent contract (`brandoModelGatewayApiKey`), rather than introducing an old slash-containing runtime override.

## Inspected remaining historical consumers

The experiment 01 judge, experiment 02 phase A version 3 deployer/identity/teacher launchers and experiment 08 version 1 launchers still use legacy YAML and, in identity scripts, client-side Amazon Web Services checks. Experiment 09's service and judge wrappers import the experiment 08 version 1 implementation from their frozen execution checkout. Those wrappers therefore require a separate coordinated migration of that execution checkout before hosted reuse. Experiment 13's dependent formal specification coverage (FSC) work must retain its recorded admission state until that route is independently verified. This change does not redirect those historical imports or edit completed results.

## Verification boundary

`tests/test_valkyrie_transport.py` uses synthetic credentials, an executable fake command-line interface (CLI) and controlled child-process substitutes. It checks supported registration/authentication arguments, secret stdin, login versus access-key registration, selected Tracker/organization, explicit legacy retention, current endpoint receipts, failure cleanup, hold preservation and non-replay of ambiguous admissions. It makes no model or sandbox calls.

On 10-14-2026, `make test` on skampere1 passed **590 tests, with 5 skipped**, in 224.79 seconds (exit 0). The same launcher source passed 41 targeted checks on macOS; unrelated process-identity tests require Linux `/proc` and fail on the unchanged macOS base too. Subsequent integration preserved the tested code bytes while incorporating concurrent experiment-13 result commits.

The coordinator deployed an isolated service using the actual updated experiment-08 version-2 deployer on unused port 9869 and benchmark `rl4cv-hosted-migration-01a13cbe`. Authenticated local/tunnel health returned 200; unauthenticated requests returned 401; the hosted task listing and service task-ID check both matched the single control. The actual updated judge module's CLI function then admitted run `46dee95d-794a-46f0-b1e7-cb6f3aff6f0b` and successfully executed start, status, results and output (exit 0, FINISHED, 1/1 tasks). The registry-probe agent made zero model calls. This verifies deployment, saved user registration, Daytona, secret injection, the launcher transport and artifact retrieval; it does not establish judge agreement or approve a held scientific run.

Private receipts/logs are retained with the coordinator's `valkyrie-hosted-completion-10-14-2026` record. The isolated test service and tunnel were stopped after collection; both owned registration aliases and auth secrets were removed, and port 9869 is free. Existing services, results and scientific holds are preserved.

Sources: [custom service registration](https://docs.valkyrie.vals.ai/benchmarks/custom-services), [hosted configuration](https://docs.valkyrie.vals.ai/get-started/configuration), and the installed `valkyrie benchmark service set --help` / `valkyrie secret set --help` plus pinned CLI source.
