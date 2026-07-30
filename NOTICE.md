# Notice and provenance

This repository was designed from an audit of
`ARRC-Rocket/BalloonPoppingChallenge` at commit
`aa5ee7dcf1e715b9aeb7e90ca807a01b6c97062f`.

The source project is MIT licensed. The testkit reimplements general engineering
patterns rather than copying the simulator:

- strict JSON artifacts and rejection of non-finite numbers;
- atomic artifact replacement;
- normalized content digests;
- trajectory baseline comparison with vector tolerances;
- explicit frame, unit, seed, and provenance contracts;
- a Balloon Popping Challenge trace adapter.

No ActiveRocketPy or RocketPy source is bundled.
