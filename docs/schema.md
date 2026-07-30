# Schema guide

## Manifest

The manifest uses JSON Schema Draft 2020-12. YAML is accepted as a presentation format,
but validation occurs against the JSON data model.

Important declarations:

- `scenario.time_step_s`: nominal environment step, separate from any internal solver step;
- `coordinates.world_frame` and `body_frame`: explicit frame identifiers;
- `coordinates.vertical_reference`: MSL, AGL, ellipsoid, or custom;
- `coordinates.quaternion_order`: `wxyz` or `xyzw`;
- `random.root_seed` and `random.derivation`: enough information to reconstruct streams;
- source commit and configuration digest for simulator provenance;
- trace path, format, and optional content digest.

## Trace

Every record requires a finite, strictly increasing `time_s`. `step_index` is optional,
but when present must equal its zero-based row index.

Recommended truth fields:

```yaml
truth:
  position_m: [x, y, z]
  velocity_mps: [vx, vy, vz]
  attitude_quaternion: [w, x, y, z]
  angular_rate_rps: [wx, wy, wz]
```

Before truth exists, use `truth: null`. JSON `NaN` and `Infinity` are rejected.

## Portable run identity

`run.id` is derived from manifest content after removing `run.id`,
`run.created_at`, and `trace.path`. Those fields describe storage and packaging,
not the experiment. `trace.digest`, simulator/controller provenance, frames,
units, scenario metadata, and seed policy remain identity-bearing.

## Random streams

Named seeds domain-separate integer, string, and byte roots as well as integer
and string path elements. This prevents accidental aliases such as integer `65`,
string `A`, and bytes `b"A"`. Adding an unrelated named stream does not shift
existing streams.
