# Contributing

1. Create a branch from `main`.
2. Keep the core package simulator-independent.
3. Put simulator-specific logic under `launch_gnc_testkit.adapters`.
4. Add tests for every behavioral change.
5. Run:

```bash
python -m pytest
ruff check src tests
ruff format --check src tests
```

Schema changes must update `schema_version`, examples, tests, and the changelog.
A tolerance change must include measured evidence explaining why the old value was
wrong or insufficient.
