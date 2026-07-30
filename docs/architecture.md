# Architecture

## Dependency direction

```text
manifest / trace / canonical / seed
             ↓
       validate / compare
             ↓
          CLI / reports
             ↓
      simulator adapters
```

The arrow means “may depend on.” Core modules never import adapters or a simulator.

## Boundary decisions

- Physics remains in the source simulator.
- Competition score, secrets, and leaderboard protocol remain in the competition.
- The testkit owns portable artifacts, provenance, deterministic seeds, validation,
  numerical comparison, and reports.
- Simulator-specific fields live under reverse-DNS extension keys.
- Missing pre-launch truth is represented as `null`, never `NaN`.
- NDJSON is the required baseline format. Parquet is optional for large traces.

## Why not copy the original submission format

The original submission payload is tied to team credentials, official-file integrity
checks, leaderboard behavior, and a competition-specific object graph. Those concerns
are valuable in the competition but are not a reusable GNC experiment contract.
