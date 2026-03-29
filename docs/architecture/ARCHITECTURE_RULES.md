# Architecture Rules

## Layers

- `kernel`: pure computation only
- `domain`: business semantics and contracts
- `intelligence`: inference and analysis logic
- `reporting`: read-only views, builders, and output contracts
- `pipeline`: orchestration only
- `runtime`: streaming and real-time execution
- `services`: external orchestration only (API/CLI/integrations)

## Dependency Direction (allowed)

- `domain` -> `kernel`
- `intelligence` -> `domain`, `kernel`
- `reporting` -> `domain`, `intelligence`
- `pipeline` -> `domain`, `intelligence`, `kernel`, `reporting`
- `runtime` -> `domain`, `intelligence`, `kernel`

## Forbidden

- `kernel` -> `domain` / `intelligence` / `reporting`
- `domain` -> `reporting`
- `intelligence` -> `reporting`
- `services` containing business or compute logic
