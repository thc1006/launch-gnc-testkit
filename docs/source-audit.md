# Source repository audit

Source pin: `ARRC-Rocket/BalloonPoppingChallenge@aa5ee7dcf1e715b9aeb7e90ca807a01b6c97062f`.

This inventory was built from the GitHub repository tree, code search, source files, tests, and repository documentation. Binary data and figure assets were classified by role; they were not decoded because they do not contain reusable testkit logic. The ActiveRocketPy submodule is an external codebase and is explicitly outside this extraction.

## Review depth and limitations

| Depth | Material | What was done |
|---|---|---|
| line-level semantic review | `balloon_world.py`, `evaluate.py`, `results/utils.py`, baseline I/O, position tolerance, package metadata, scenario contracts | traced data flow, lifecycle, serialization, determinism, tolerance, and failure behavior into the extracted APIs |
| contract-level review | source tests, configs, scripts, examples, governance files | identified reusable invariants, simulator coupling, competition coupling, and exclusion decisions |
| role classification only | NetCDF weather data, figures, notebook binary outputs | recorded in the tree but not decoded because they do not contain reusable testkit execution logic |
| external boundary | ActiveRocketPy submodule | pinned and documented, but not bundled or re-audited as part of this independent product |

The runtime could not retrieve GitHub's commit archive directly, so the inventory
was assembled through the GitHub connector's commit-pinned file fetches, code
search, repository navigation, and source documentation. The audit does not claim
flight-physics validation or binary-data validation.

## Findings by layer

1. **Environment layer:** `balloon_world.py` combines physics construction, observations/actions, seed handling, lifecycle, scoring, trajectory logging, and rendering. Only boundary contracts belong in the testkit.
2. **Evaluation layer:** `evaluate.py` correctly separates termination from truncation and deep-copies parameters passed to untrusted agents. These are adapter and validation concerns, not simulator code to copy.
3. **Artifact layer:** `results/utils.py` contains the strongest reusable patterns: normalized digests, atomic writes, filename safety, strict serialization concerns, and post-run integrity behavior. Secrets and network checks remain competition-specific.
4. **Verification layer:** the tests encode coordinate, determinism, lifecycle, artifact, tolerance, and regression contracts. This extraction promotes the generic subset into first-class APIs.
5. **Data/rendering layer:** weather NetCDF, figures, notebooks, and render tests are intentionally excluded from the core product.

## File inventory

| Source path | Role | Extraction decision |
|---|---|---|
| `.github/ISSUE_TEMPLATE/bug_report.yml` | configuration/governance | adapt packaging/CI conventions where generic |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | configuration/governance | adapt packaging/CI conventions where generic |
| `.github/ISSUE_TEMPLATE/question.yml` | configuration/governance | adapt packaging/CI conventions where generic |
| `.github/workflows/ci.yml` | configuration/governance | adapt packaging/CI conventions where generic |
| `.gitignore` | package/build support | replace with independent package metadata |
| `.gitmodules` | package/build support | replace with independent package metadata |
| `.python-version` | package/build support | replace with independent package metadata |
| `CHANGELOG.md` | documentation/governance | use as source context; rewrite for independent product |
| `CITATION.cff` | documentation/governance | use as source context; rewrite for independent product |
| `CONTRIBUTING.md` | documentation/governance | use as source context; rewrite for independent product |
| `LICENSE` | package/build support | replace with independent package metadata |
| `Makefile` | package/build support | replace with independent package metadata |
| `README.md` | documentation/governance | use as source context; rewrite for independent product |
| `SECURITY.md` | documentation/governance | use as source context; rewrite for independent product |
| `pyproject.toml` | configuration/governance | adapt packaging/CI conventions where generic |
| `requirements-dev.txt` | configuration/governance | adapt packaging/CI conventions where generic |
| `requirements.txt` | configuration/governance | adapt packaging/CI conventions where generic |
| `uv.lock` | configuration/governance | adapt packaging/CI conventions where generic |
| `ActiveRocketPy (git submodule @ 473447d5155402f8e60d20ea2bb826cc3a61f4b3)` | external physics submodule | never bundle or import from core |
| `BalloonPoppingGymEnv/__init__.py` | package/build support | replace with independent package metadata |
| `BalloonPoppingGymEnv/console_logging.py` | package/build support | replace with independent package metadata |
| `BalloonPoppingGymEnv/agents/base_agent.py` | controller examples/interface | do not extract controller behavior; preserve adapter boundary |
| `BalloonPoppingGymEnv/agents/example_agents.py` | controller examples/interface | do not extract controller behavior; preserve adapter boundary |
| `BalloonPoppingGymEnv/envs/__init__.py` | package/build support | replace with independent package metadata |
| `BalloonPoppingGymEnv/envs/balloon_world.py` | simulator/environment | extract state/action/frame semantics only; keep physics in source |
| `BalloonPoppingGymEnv/envs/data/README.md` | documentation/governance | use as source context; rewrite for independent product |
| `BalloonPoppingGymEnv/envs/data/TW_Cup_250726_NetCDF4_Ensemble.nc` | data/documentation asset | do not extract into core; document adapter expectations |
| `BalloonPoppingGymEnv/envs/scenario_parameters/scenario_0_given_parameters.yaml` | configuration/governance | adapt packaging/CI conventions where generic |
| `BalloonPoppingGymEnv/envs/scenario_parameters/scenario_0_parameters.yaml` | configuration/governance | adapt packaging/CI conventions where generic |
| `BalloonPoppingGymEnv/envs/scenario_parameters/scenario_1_given_parameters.yaml` | configuration/governance | adapt packaging/CI conventions where generic |
| `BalloonPoppingGymEnv/envs/scenario_parameters/scenario_1_parameters.yaml` | configuration/governance | adapt packaging/CI conventions where generic |
| `BalloonPoppingGymEnv/evaluation/__init__.py` | package/build support | replace with independent package metadata |
| `BalloonPoppingGymEnv/evaluation/evaluate.py` | evaluation/artifact pipeline | extract provenance, strict serialization and atomic writes; omit secrets/network check |
| `BalloonPoppingGymEnv/evaluation/configs/example_eval_cfg.yaml` | configuration/governance | adapt packaging/CI conventions where generic |
| `BalloonPoppingGymEnv/evaluation/results/utils.py` | evaluation/artifact pipeline | extract provenance, strict serialization and atomic writes; omit secrets/network check |
| `doc/examples/evaluate_scenario_colab.ipynb` | data/documentation asset | do not extract into core; document adapter expectations |
| `doc/examples/run_env_agent.py` | documentation/governance | use as source context; rewrite for independent product |
| `doc/examples/test_navigation_agent.py` | documentation/governance | use as source context; rewrite for independent product |
| `doc/figures/*` | data/documentation asset | do not extract into core; document adapter expectations |
| `scripts/verify_submission.py` | evaluation/artifact pipeline | extract provenance, strict serialization and atomic writes; omit secrets/network check |
| `tests/baselines/baseline_io.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/baselines/regenerate_scenario_0.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/baselines/regenerate_scenario_1.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/baselines/scenario_0.json` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/baselines/scenario_1.json` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/position_tolerance.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_actuator_dynamics.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_baseline_io.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_cleanup.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_console_logging.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_coordinate_contract.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_episode_lifecycle.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_import_guard_shape.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_import_smoke.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_integrity_check.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_logging.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_matplotlib_render.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_monte_carlo_output_path.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_monte_carlo_result_count.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_non_finite_actions.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_observation_isolation.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_pop_detection.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_position_tolerance.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_render.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_runners_handle_truncation.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_scenario0_regression.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_scenario0_static.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_scenario1_regression.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_segment_distance_scaling.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_sensor_determinism.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_submission_digest.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_submission_payload.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_submission_serialization.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_submission_write_safety.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_verify_submission.py` | verification | mine reusable contracts; do not copy simulator fixtures |
| `tests/test_vpython_lazy_import.py` | verification | mine reusable contracts; do not copy simulator fixtures |
