# Extraction map

| Source concept | Source location | New product location | Decision |
|---|---|---|---|
| trajectory step records | `envs/balloon_world.py` | `trace.py`, `adapters/bpc.py` | normalize into simulator-independent records |
| action finite/shape checks | `envs/balloon_world.py` | `validate.py` | generalized to all nested trace values |
| explicit termination/truncation | `evaluation/evaluate.py`, lifecycle tests | trace events/extensions | retained as a documented adapter responsibility |
| deep-copy isolation | `evaluation/evaluate.py` | architecture rule | do not expose mutable simulator configuration to controllers |
| strict JSON baseline write | `tests/baselines/baseline_io.py` | `canonical.py`, `trace.py` | retained and generalized |
| atomic replacement | baseline and submission writers | `canonical.atomic_write` | retained and generalized |
| normalized digest | `evaluation/results/utils.py` | `canonical.normalized_text_digest` | retained without network dependency |
| run provenance | submission payload/tests | manifest schema | expanded to simulator/controller/source/config metadata |
| vector position tolerance | `tests/position_tolerance.py` | `compare.py` | generalized to any vector field |
| unmatched-tail continuity | `tests/position_tolerance.py` | `compare.py` | retained for vector position rules |
| sensor seed derivation | environment and determinism tests | `seed.py` | replaced with named, order-independent derivation |
| BPC-specific balloon arrays | trajectory records | `extensions.org.arrc.balloon_popping` | isolated in adapter namespace |
| team secret and leaderboard submission | `results/utils.py` | none | intentionally excluded |
| remote official-file integrity check | `results/utils.py` | none | replaced by local provenance digests |
| RocketPy/ActiveRocketPy physics | submodule/environment | none | intentionally excluded |
| renderer/weather assets | environment/data/docs | none | intentionally excluded |
