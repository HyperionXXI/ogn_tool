# Import Policy Matrix

## Scope
This policy is enforceable at folder boundary level for `src/ogn_tool`.

## Matrix
| Folder | Intended Responsibility | Allowed Dependencies | Forbidden Dependencies |
|---|---|---|---|
| `domain` | Pure business contracts and immutable domain objects | `domain` | `pipeline`, `engine`, `analysis`, `analytics`, `reporting`, `runtime`, `services`, `storage`, `apps` |
| `models` | Transport/view/result models used across layers | `models`, `domain` | `pipeline`, `engine`, `analysis`, `analytics`, `reporting`, `runtime`, `services`, `storage` |
| `analysis` | Deterministic computation kernels (RF/network/spatial/temporal math) | `analysis`, `domain`, `models`, `rf` | `pipeline`, `reporting`, `runtime`, `services`, `storage`, `apps` |
| `engine` | Execution kernels orchestrating analysis steps | `engine`, `analysis`, `domain`, `models`, `rf` | `pipeline`, `reporting`, `runtime`, `services`, `storage`, `apps` |
| `intelligence` | Scenario/network intelligence composition on top of analysis outputs | `intelligence`, `analysis`, `domain`, `models` | `pipeline`, `reporting`, `runtime`, `services`, `storage`, `apps` |
| `pipeline` | Application orchestration entrypoints (runs/stages/contracts) | `pipeline`, `engine`, `intelligence`, `domain`, `models`, `data`, `config`, `reporting` | direct `analysis` imports (must go through `engine`/`intelligence`), `runtime`, `apps` |
| `reporting` | Report/view assembly and artifact shaping | `reporting`, `domain`, `models` | direct `analysis`, `engine`, `pipeline`, `runtime`, `services`, `storage`, `apps` |
| `runtime` | Runtime APIs/use-case services callable by CLI/UI | `runtime`, `pipeline`, `intelligence`, `domain`, `models` | direct `analysis`, `engine`, `reporting`, `storage`, `apps` |
| `services` | Stable service facades (public integration boundary) | `services`, `runtime`, `pipeline`, `domain`, `models` | direct `analysis`, `engine`, `reporting`, `storage` |
| `storage` | Persistence adapters and stores | `storage`, `domain`, `models`, `data` | direct `analysis`, `engine`, `pipeline`, `runtime`, `reporting`, `apps` |

## Enforcement Notes
- Current audit violations to resolve later: `pipeline -> analysis`, `engine -> analysis`, `reporting -> analysis`, and one cycle inside `reporting`.
- This document is policy only; no refactor included here.
