# Shared cloud-drive supervisor (1+3)

One **stateless master** coordinates two independent ingestion providers:

- Baidu: `baidu-drive-worker.yml` prepares/stages files; `baidu-drive-file-worker.yml` executes its leases.
- Quark: `quark-drive-worker.yml` will provide the same adapter interface once its isolated provider implementation is ready.
- **Three worker slots total**, not three per provider. One active provider can use all three; when both need work, each gets an available slot before the longest-remaining queue receives spare capacity.
- Only the owning provider handles its Cookie, staged-source IDs, Google Drive session or file cleanup. The shared supervisor sees **public-safe task and per-file status only**.

## Execution and handoff

The master is a *reentrant GitHub Actions job*, not a six-hour immortal VM. It reconstructs the queue from each provider's `state/runtime.json`, current file records and verified Drive progress. It dispatches only an allocated number of additional worker slots to each provider adapter. Worker execution uses file-scoped leases and serialized GitHub state updates.

The master is woken by the file-worker completion callback, operator input, and a **30-minute watchdog schedule**. A missing callback or a terminated master is recovered by the next watchdog. Checkpointed `next_retry_at` is respected; external transient failures back off with jitter without a finite attempt limit, while malformed inputs, unproven Drive duplicates and invalid authorization stop for reconciliation or re-login.

A durable provider dispatch reservation protects slots while its preparation Action is queued or running. The first 12 minutes cover workflow dispatch propagation; after that the supervisor checks GitHub Actions job state before releasing the reservation. This prevents a long-queued preparation Action from later exceeding the shared three-worker limit. A lost dispatch is reissued when no queued/running job exists. The shared state lives under `tools/cloud-drive/state/supervisor.json`. No credentials or signed links may enter this file. The master runs only GitHub API calls; real downloads occur in the three worker jobs.

## Rollout

1. Deploy shared watchdog while Baidu is the sole active provider; verify it does not interfere with live leases.
2. Make Baidu preparation honor its assigned `max_workers` cap.
3. Enable the Quark adapter after its independent sign-in, scan, staging, download, and Drive verification CI pass.
4. Route both providers' completion callbacks to this one master and remove duplicate autonomous dispatch paths.
