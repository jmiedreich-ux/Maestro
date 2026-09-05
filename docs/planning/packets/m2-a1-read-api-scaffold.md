# M2 Wave A — Read API Scaffold — Candidate 01

**Slice ID:** `MB-SLICE-M2-A1-READ-API-SCAFFOLD-01`
**Status:** `Pending Targeted Verification` — targeted planning correction applied after Decision Fidelity `REQUEST_CHANGES` found a real fingerprint ambiguity and an untested in-scope CLI signal-handling claim
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
| `phase` | `PendingTargetedVerification` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:ba4e74a","git:full-planning-review-head:5e492e643c53cd4d8e72ef0b705ec6bfcba2cfd1","review:decision-fidelity:request-changes:2-blocking-findings"]` |

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

def canonical_response_json(payload: Mapping[str, Any]) -> bytes: ...
```

**Correction (blocking finding 1, exact-byte ambiguity):** every JSON body or
line this slice emits — the two HTTP bodies and the CLI status line — is
produced by exactly one function, `canonical_response_json`, defined once in
`read_api.py`:

```python
def canonical_response_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
```

This is the same compact, sorted-key convention already established by
`operational_state.canonical_json` and `review_readiness.canonical_json` —
this slice does not reuse either of those two functions directly (both live
in modules unrelated to HTTP serving; importing one into `read_api.py` would
be a needless cross-module coupling), it defines its own copy of the same
convention, scoped to this module's own two payload shapes. Every JSON
example below is the literal, exact output of this function — **no spaces**,
keys in sorted order.

`start()` binds a `http.server.ThreadingHTTPServer` to
`(config.host, config.port)` running a private `BaseHTTPRequestHandler`
subclass in a daemon thread, and must not return until the socket is bound
(so a caller's immediate `bound_port` read is race-free). `port=0` is
permitted and resolves to an OS-assigned ephemeral port (this is exactly how
the tests below avoid port collisions); `bound_port` returns that resolved
port. `stop()` calls `shutdown()` + `server_close()` and joins the serving
thread with a bounded timeout, then clears internal state so a fresh
`start()` can be called again on the same instance.

Route contract, exactly one route (every body below is the exact,
literal output of `canonical_response_json`, byte-for-byte):

- `GET /health` → `200`, `Content-Type: application/json`, body
  `{"status":"ready"}`.
- Any other path, with **any** HTTP method including `GET` → `404` with
  body `{"error":"not_found"}`.
- `/health` itself with any method other than `GET` → `405` with body
  `{"error":"method_not_allowed"}`.
- Path routing is checked before method routing: an unknown path always
  returns `404` regardless of method (including `POST /anything-else`,
  which is `404`, not `405` — `405` is reserved for the one known path
  used the wrong way).
- The handler overrides `log_message` to a no-op — no request logging to
  stderr from this scaffold. Proven directly by test 2 below (not a
  separate test): the request in that test asserts no bytes are written
  to `sys.stderr` for the duration of the call.

## Guards, before any socket exists

1. `ReadApiConfig.__post_init__` rejects any `host` not in
   `_LOOPBACK_HOSTS`, raising `ReadApiBindError`, before `ReadApiServer`
   ever constructs a socket. This is a literal string-allowlist check, not
   a guarantee against OS/DNS-level host misconfiguration (e.g. a
   corrupted `/etc/hosts` remapping `localhost`) — that class of failure
   is out of scope at this assurance level (see exclusions). Within that
   scope, this is the slice's one protected invariant: no caller-supplied
   host string outside the fixed allowlist ever reaches a socket bind.
2. `ReadApiServer.start()` raises `RuntimeError` if called while already
   started (no silent double-bind, no leaked socket).
3. `ReadApiServer.stop()` is idempotent: calling it when not started is a
   no-op, not an error (so cleanup code never needs a guard).

## CLI entry point

`services/maestro/maestro/cli.py` gains one new subparser, `serve-read-api`,
with `--host` (default `127.0.0.1`) and `--port` (default `8765`). This is
the only change to `cli.py`; no existing subcommand's behavior changes.

Exact behavior:

1. Construct `ReadApiConfig(host=args.host, port=args.port)`. If this
   raises `ReadApiBindError`, catch it, write
   `canonical_response_json({"error":"invalid_host","detail":str(error)})`
   followed by a newline to **stderr**, print nothing to stdout, and
   return exit code `2`. No server is ever started on this path.
2. Otherwise construct `ReadApiServer(config)` and call `start()`.
3. Write `canonical_response_json({"host":<config.host>,"port":<bound_port>,"status":"listening"})`
   followed by a newline to **stdout**, then flush stdout (so a subprocess
   caller can reliably read exactly one line before the process blocks).
4. Register a `signal.signal` handler for `SIGINT` that calls `stop()` and
   then `sys.exit(0)`. `SIGTERM` is explicitly **not** handled by this
   scaffold — an unhandled `SIGTERM` terminates the process by the
   platform default, without a graceful `stop()`. This is a deliberate,
   narrowed claim (see the quality contract's exclusions): only graceful
   shutdown via `SIGINT` is proven by this slice.
5. Block on the server's serving thread (`Thread.join()`) until the
   `SIGINT` handler above exits the process.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `services/maestro/maestro/read_api.py` (new file)
- `services/maestro/maestro/cli.py` (additive: one new subparser branch only)
- `tests/m2_wave_a/test_read_api_scaffold.py` (new file)

No other file changes. No new dependency — Python standard library
(`http.server`, `threading`, `dataclasses`, `json`) only. `pyproject.toml`
is not touched.

The 9 named tests, in `tests/m2_wave_a/test_read_api_scaffold.py` following
the repository's `test_NN_<description>` convention:

1. `test_01_non_loopback_host_rejected_before_bind` — constructing
   `ReadApiConfig(host="0.0.0.0")` (and one other non-loopback value) raises
   `ReadApiBindError`; no socket is ever created (assert via a patched
   `ThreadingHTTPServer.__init__` that must not be called).
2. `test_02_health_returns_exact_body_with_no_log_output` — start with
   `port=0`, `GET /health` returns `200`, `Content-Type: application/json`,
   and the exact bytes `b'{"status":"ready"}'`; `sys.stderr` receives zero
   bytes for the duration of the request (proves the `log_message`
   no-op).
3. `test_03_unknown_path_returns_404_regardless_of_method` — `GET
   /anything-else` and `POST /anything-else` both return `404` and exactly
   `b'{"error":"not_found"}'`.
4. `test_04_non_get_on_health_returns_405` — `POST /health` (and one other
   method) returns `405` and exactly `b'{"error":"method_not_allowed"}'`.
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
8. `test_08_cli_serve_read_api_prints_status_and_stops_on_sigint` — launch
   `python -m maestro.cli serve-read-api --host 127.0.0.1 --port 0` as a
   subprocess; read exactly one stdout line and parse it as JSON, asserting
   the exact key set `{"host","port","status"}`, `status=="listening"`,
   `host=="127.0.0.1"`, and `port` is an integer greater than `0`; issue a
   real `GET /health` against that port and confirm `200`; send `SIGINT`
   to the subprocess; assert it exits with code `0` within a bounded
   timeout.
9. `test_09_cli_rejects_invalid_host_with_clean_exit_and_no_listening_line`
   — launch the same subcommand with `--host 0.0.0.0`; assert exit code
   `2`, an empty stdout (no `"listening"` line was ever printed), and a
   parseable JSON error line on stderr with `error=="invalid_host"`.

Run the existing 290 named tests (unaffected — this slice adds files and
one additive CLI branch, changes no existing behavior) plus these 9 (299
total):

```
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m unittest discover -s ../../tests/m1_02 -v
python -m unittest discover -s ../../tests/review_readiness -v
python -m unittest discover -s ../../tests/m2_wave_a -v
```

Also run `python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`; and
run exact candidate hygiene before any readiness claim.

### M0-D12 bounded quality contract

1. **Protected outcome:** the Atlas read API process rejects, before any
   socket exists, any caller-supplied host string outside a fixed loopback
   allowlist, and correctly serves or rejects exactly the routes and CLI
   behaviors named above.
2. **Operating and threat model:** a trusted local single-user Linux box;
   a caller passing an unexpected host/port to the CLI; concurrent
   `start()`/`stop()` misuse by the same process; graceful process
   shutdown via `SIGINT`.
3. **Explicit exclusions:** authentication/authorization (Owner decision
   2026-09-05: none while single local owner), TLS, any database-backed
   route, any event stream, any request beyond `/health`, any
   multi-process/multi-instance coordination, graceful `SIGTERM` handling
   (explicitly unhandled in this scaffold — see the CLI section), and any
   OS/DNS-level host-resolution misconfiguration defeating the literal
   loopback allowlist.
4. **Assurance level:** practical trusted-local-process containment
   (loopback-only bind, no more) — proportionate to a scaffold with zero
   sensitive data behind it.
5. **Acceptance proof:** the 9 named tests, the 299-test full inventory,
   `compileall`, and exact candidate hygiene, all passing.
6. **Implementation boundary:** exactly the three writable paths above;
   Python standard library only; no new dependency.
7. **Proportionality ceiling:** one new module, one additive CLI branch,
   one new test file; no snapshot/query logic, no event stream, no
   authentication — those are later, separately reviewed Wave A slices.
8. **Stop and escalation rule:** if a real deployment ever needs
   non-loopback exposure, authentication, TLS, or graceful `SIGTERM`
   handling, that is a new, separately reviewed decision — not an
   extension of this scaffold. A discovered proof/contract defect against
   a frozen slice terminally returns that slice. One planning correction
   and one implementation correction are the maximum available. This
   packet has now used its one planning correction; a further blocking
   planning finding returns this slice rather than receiving a second
   correction.
