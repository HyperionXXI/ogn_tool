# Changelog

## 2026-03-06

### Added
- Coverage grid builder script and loader to read the unified coverage grid schema.
- RF analysis core implementations for station range, station quality, and polar analysis.
- CLI entrypoint module.
- RF analysis pipeline documentation in README (EN/FR).

### Fixed
- Polar analysis no longer fails when roof coordinates are missing.

### Changed
- Dashboard now detects coverage grid availability and clarifies status messages.
- Documentation clarified RF analysis purpose and use cases (EN/FR).

### Commits
- `efe3365` feat: add coverage grid builder and loader
- `cbf4191` fix: avoid missing roof_lat in polar analysis
- `9db5519` docs: describe RF analysis pipeline
- `cfb9e4a` docs: clarify RF analysis purpose and use cases
- `68ce498` feat: implement core RF analysis modules
- `8a5fbba` feat: track cli entrypoint
- `4b723cd` feat: load coverage_grid when available
- `070e969` ui: clarify dashboard status messages and placeholders
- `2c3d3ae` refactor: wire views to analysis modules
- `902b6ac` ui: add RF feature placeholders
