# launch-gnc-testkit

> Launch GNC Testkit

`launch-gnc-testkit` is a simulator-independent toolkit for normalizing,
validating, comparing, and identifying launch-vehicle guidance, navigation, and
control (GNC) simulation artifacts.

It was extracted from engineering patterns found in the
[ARRC Balloon Popping Challenge](https://github.com/ARRC-Rocket/BalloonPoppingChallenge),
but the core package does **not** import RocketPy, ActiveRocketPy, Gymnasium, or
competition code.

## What it standardizes

The project standardizes experiment boundaries rather than physics:

- run manifests and provenance;
- coordinate-frame, unit, and quaternion declarations;
- deterministic, type-safe named seed derivation;
- strict and portable trace artifacts;
- trace validation and invariant checks;
- scalar, vector, quaternion, and exact regression comparison;
- simulator-specific adapter boundaries.

It deliberately does **not** prescribe an aerodynamic model, integrator,
controller, reward function, or vehicle design.

## Install

```bash
python -m pip install .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

For optional Parquet support:

```bash
python -m pip install -e ".[parquet]"
```

## Five-minute example

```bash
gnctest validate-manifest examples/minimal_manifest.yaml --format markdown
gnctest validate-trace examples/reference_trace.ndjson \
  --manifest examples/minimal_manifest.yaml
gnctest inspect examples/reference_trace.ndjson
gnctest compare examples/reference_trace.ndjson \
  examples/reference_trace.ndjson \
  --rules examples/comparison_rules.yaml
gnctest derive-seed 12345 atmosphere gust 0
```

Convert a Balloon Popping Challenge trajectory:

```bash
gnctest convert-bpc trajectory.json trace.ndjson \
  --manifest-out run-manifest.yaml \
  --source-commit aa5ee7dcf1e715b9aeb7e90ca807a01b6c97062f \
  --root-seed 12345
```

When the original trajectory does not carry its random seed, omit
`--root-seed`; the manifest records it as `unknown` rather than inventing one.

## Artifact model

A run is represented by two artifacts:

1. a YAML/JSON manifest containing identity, provenance, frames, units, random
   seed, simulator, controller, and trace metadata;
2. an NDJSON, JSON, or optional Parquet trace containing ordered time-step
   records.

The portable `run.id` excludes creation time and the local trace pathname, so
moving the same run between machines does not change its identity. When a trace
content digest is present, it remains part of the identity. The deterministic
serializer is stable inside this project but is not advertised as a complete
implementation of RFC 8785.

## BPC adapter contract

The adapter maps the source trajectory fields as follows:

- `time` → `time_s`;
- `rocket_states[0:3]` → `truth.position_m`;
- `rocket_states[3:6]` → `truth.velocity_mps`;
- `rocket_states[6:10]` → `truth.attitude_quaternion`;
- `rocket_states[10:13]` → `truth.angular_rate_rps`;
- balloon arrays → `extensions.org.arrc.balloon_popping`.

Pre-launch `NaN` rocket truth becomes `truth: null`; the output artifact itself
remains strict JSON.

## Safety and scope

This package is for simulation, validation, education, and civilian aerospace
research. It is not flight-qualified software and does not contain a deployable
weapon guidance implementation. See [SECURITY.md](SECURITY.md).

## Source extraction

- [Architecture](docs/architecture.md)
- [Schema guide](docs/schema.md)
- [Extraction map](docs/extraction-map.md)
- [Source repository audit](docs/source-audit.md)
- [Delivery and verification report](DELIVERY_REPORT.md)

## Status

Version `0.1.0` is an engineering MVP. Its schemas are versioned, but no
compatibility promise is made until `1.0.0`.
