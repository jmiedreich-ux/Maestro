# Alpha-01 Local Run

From `services/maestro/`, run the local readiness check with a disposable
runtime directory:

```bash
python -m maestro.cli health --runtime-dir ../../var/alpha-01-check
```

The command creates or reuses `maestro.sqlite3` only beneath the supplied
runtime directory and prints the schema version, WAL mode, and foreign-key
status. It contacts no network service and reads no project repository,
credential, or external integration.

Run the Alpha-01 test suite with:

```bash
python -m unittest discover -s ../../tests/alpha_01 -v
```

`var/alpha-01-check` is disposable Alpha runtime data. Remove only that
specific directory after a local check if it is no longer needed; do not remove
any other `var/` content.
