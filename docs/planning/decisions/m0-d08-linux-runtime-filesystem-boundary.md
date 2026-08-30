# M0-D08 — Linux Runtime Filesystem Boundary

**Status:** Accepted  
**Scope:** Maestro local runtime directories and SQLite files on the Linux AI box  
**Authority:** Owner decision, 2026-08-30

## Decision

Maestro runtime data may exist only within the repository's real physical
`var/` tree. A requested runtime path is invalid unless every path component
used to reach it remains beneath that physical boundary and contains no
symlink traversal.

The rule applies to every public entry path, including commands, configuration
objects, constructors, and storage callables. It applies before any directory,
database, log, socket, or other runtime artifact is created or opened.

## Linux race protection

A prior lexical or resolved-path check alone is not sufficient. On Linux, the
implementation must defend against a path changing between validation and use:

- establish the repository runtime root as a real physical directory;
- reject a requested path that is outside that root or contains a symlinked
  component;
- use filesystem-safe operations at the mutation boundary so a directory swap
  or symlink substitution cannot redirect a write outside the root; and
- revalidate or fail safely before every mutating SQLite/runtime operation.

A rejected path must leave no created directory, database, journal, WAL/SHM
file, log, socket, or other file at either the requested location or an
outside destination.

## Alpha-01 consequences

The Alpha-01 packet must carry this decision as an explicit acceptance
criterion. Its repair tests must cover command, configuration, constructor,
and storage paths, plus a symlink-swap/race attempt. The expected default must
be independently derived as `<worktree-root>/var`, not taken from the
implementation constant.

This is a packet-contract expansion discovered by independent review. It is
not a worker/model delivery failure and does not authorize another correction
on an implementation branch. Alpha-01 remains paused until the amended packet
passes a new Decision Fidelity Review; only then may a new bounded repair
packet be issued.

## Non-goals

This decision does not define user-selectable runtime locations, shared
runtime volumes, backup/USB behavior, or Alpha-02 packet-wrapper behavior.
