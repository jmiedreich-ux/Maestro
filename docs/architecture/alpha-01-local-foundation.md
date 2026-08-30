# Alpha-01 Local Foundation

Alpha-01 creates only the local Python/SQLite base used by later Maestro work.
It has no worker, packet wrapper, lifecycle execution, project adapter, API,
Atlas UI, network integration, credential access, or external-project access.

`services/maestro/maestro/config.py` owns the explicit runtime-directory
boundary. Its default is the repository's `var/` directory; callers can supply
another local runtime directory for tests or disposable checks. The service
creates only `maestro.sqlite3` and SQLite's accompanying runtime files beneath
that directory.

`storage.py` requests WAL mode, enables foreign keys, and records only the
idempotent `schema_versions` migration metadata. Packet, queue, worker, review,
evidence, project, and adapter schemas are deliberately deferred.

The only Alpha-01 CLI command is `maestro health`. `maestro run-packet` remains
an Alpha-02 responsibility and is not partially represented here.
