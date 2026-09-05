# M2 Wave A — Read API Scaffold — Candidate 01

**Slice ID:** `MB-SLICE-M2-A1-READ-API-SCAFFOLD-01`
**Status:** `Pending Decision Fidelity Review`
**Base:** `ba4e74a` (`origin/master`)

## Scope, deliberately minimal

Wave A of the [M2 Atlas roadmap](../m2-atlas-roadmap.md) needs a local read
API process before any snapshot endpoint, event stream, or Atlas screen can
exist. This slice builds only the process itself: a loopback-only HTTP
server with exactly one route, `GET /health`, returning a fixed JSON body.
No database access, no packet/attempt/review data, no event stream. It
proves the process starts, binds only to loopback, serves one route
correctly, rejects every other route and method, and stops cleanly —
nothing else.

This is new code, not an extension of an existing function: `services/maestro`
has no HTTP server today. Controlling authority is the Bootstrap Convergence
Policy, `docs/planning/maestro-master-plan.md`, `docs/planning/m2-atlas-roadmap.md`,
and M0-D01 (which already names this local read API as approved architecture),
read from current `origin/master`.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-A1-READ-API-SCAFFOLD-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:ba4e74a"]` |

## New module and exact contract

`services/maestro/maestro/read_api.py` (new file):

```python
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

class ReadApiBindError(ValueError): ...

@dataclass(frozen=True)
class ReadApiConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    # __post_init__ raises ReadApiBindError before any socket exists
    # if host not in _LOOPBACK_HOSTS.

class ReadApiServer:
    def __init__(self, config: ReadApiConfig | None = None) -> None: ...
    @property
    def bound_port(self) -> int: ...   # raises RuntimeError if not started
    def start(self) -> None: ...        # raises RuntimeError if already started
    def stop(self) -> None: ...         # idempotent; safe to call when not started
    def __enter__(self) -> "ReadApiServer": ...
    def __exit__(self, *exc_info) -> None: ...
```

`start()` binds a `http.server.ThreadingHTTPServer` to
`(config.host, config.port)` running a private `BaseHTTPRequestHandler`
subclass in a daemon thread, and must not return until the socket is bound
(so a caller's immediate `bound_port` read is race-free). `port=0` is
permitted and resolves to an OS-assigned ephemeral port (this is exactly how
the tests below avoid port collisions); `bound_port` returns that resolved
port. `stop()` calls `shutdown()` + `server_close()` and joins the serving
thread with a bounded timeout, then clears internal state so a fresh
`start()` can be called again on the same instance.

Route contract, exactly one route:

- `GET /health` → `200`, `Content-Type: application/json`, body
  `{"status": "ready"}` (canonical JSON, sorted keys).
- Any other path, any method → `404` with body `{"error": "not_found"}`,
  **except** a non-`GET` request to `/health` itself, which returns `405`
  with body `{"error": "method_not_allowed"}`.
- The handler overrides `log_message` to a no-op — no request logging to
  stderr from this scaffold.

## Guards, before any socket exists

1. `ReadApiConfig.__post_init__` rejects any `host` not in
   `_LOOPBACK_HOSTS`, raising `ReadApiBindError`, before `ReadApiServer`
   ever constructs a socket. This is the slice's one protected invariant:
   this process can never bind a non-loopback interface.
2. `ReadApiServer.start()` raises `RuntimeError` if called while already
   started (no silent double-bind, no leaked socket).
3. `ReadApiServer.stop()` is idempotent: calling it when not started is a
   no-op, not an error (so cleanup code never needs a guard).

## CLI entry point

`services/maestro/maestro/cli.py` gains one new subparser, `serve-read-api`,
with `--host` (default `127.0.0.1`) and `--port` (default `8765`). It
constructs `ReadApiServer(ReadApiConfig(host, port))`, calls `start()`,
prints `{"status": "listening", "host": ..., "port": <bound_port>}` as one
line of canonical JSON, then blocks on the server thread until `SIGINT` or
`SIGTERM`, at which point it calls `stop()` and exits `0`. This is the only
change to `cli.py`; no existing subcommand's behavior changes.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `services/maestro/maestro/read_api.py` (new file)
- `services/maestro/maestro/cli.py` (additive: one new subparser branch only)
- `tests/m2_wave_a/test_read_api_scaffold.py` (new file)

No other file changes. No new dependency — Python standard library
(`http.server`, `threading`, `dataclasses`, `json`) only. `pyproject.toml`
is not touched.

The 7 named tests, in `tests/m2_wave_a/test_read_api_scaffold.py` following
the repository's `test_NN_<description>` convention:

1. `test_01_non_loopback_host_rejected_before_bind` — constructing
   `ReadApiConfig(host="0.0.0.0")` (and one other non-loopback value) raises
   `ReadApiBindError`; no socket is ever created (assert via a patched
   `ThreadingHTTPServer.__init__` that must not be called).
2. `test_02_health_returns_exact_body` — start with `port=0`, `GET /health`
   returns `200`, `Content-Type: application/json`, and exactly
   `{"status": "ready"}`.
3. `test_03_unknown_path_returns_404` — `GET /anything-else` returns `404`
   and `{"error": "not_found"}`.
4. `test_04_non_get_on_health_returns_405` — `POST /health` (and one other
   method) returns `405` and `{"error": "method_not_allowed"}`.
5. `test_05_double_start_raises_without_leaking_socket` — calling `start()`
   twice on the same instance raises `RuntimeError`; the original server is
   still serving `/health` correctly afterward; `stop()` cleans up exactly
   one socket.
6. `test_06_stop_is_idempotent_and_restart_works` — `stop()` before any
   `start()` is a no-op; `start()` → `stop()` → `start()` again on the same
   instance serves `/health` correctly both times, on a fresh ephemeral
   port each time.
7. `test_07_bound_port_raises_before_start` — reading `bound_port` before
   `start()` raises `RuntimeError`.

Run the existing 280 named tests (unaffected — this slice adds files and
one additive CLI branch, changes no existing behavior) plus these 7 (287
total); run `python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`; and
run exact candidate hygiene before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** the Atlas read API process can never bind a
   non-loopback network interface, and correctly serves or rejects exactly
   the routes named above.
2. **Operating and threat model:** a trusted local single-user Linux box;
   a caller passing an unexpected host/port; concurrent `start()`/`stop()`
   misuse by the same process; process shutdown via signal.
3. **Explicit exclusions:** authentication/authorization (Owner decision
   2026-09-05: none while single local owner), TLS, any database-backed
   route, any event stream, any request beyond `/health`, and any
   multi-process/multi-instance coordination.
4. **Assurance level:** practical trusted-local-process containment
   (loopback-only bind, no more) — proportionate to a scaffold with zero
   sensitive data behind it.
5. **Acceptance proof:** the 7 named tests, the 287-test full inventory,
   `compileall`, and exact candidate hygiene, all passing.
6. **Implementation boundary:** exactly the three writable paths above;
   Python standard library only; no new dependency.
7. **Proportionality ceiling:** one new module, one additive CLI branch,
   one new test file; no snapshot/query logic, no event stream, no
   authentication — those are later, separately reviewed Wave A slices.
8. **Stop and escalation rule:** if a real deployment ever needs
   non-loopback exposure, authentication, or TLS, that is a new,
   separately reviewed decision — not an extension of this scaffold. A
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
