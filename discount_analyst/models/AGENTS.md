<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-06-14 -->

# models

## Purpose

Stdlib-only shared types used across `discount_analyst/`, `backend/`, `common/`, and `scripts/` without pulling in heavy provider or agent dependencies. Keeps Alembic and ORM imports lightweight.

## Key Files

| File            | Description                                      |
| --------------- | ------------------------------------------------ |
| `model_name.py` | `ModelName` (`StrEnum`) — canonical LLM identifiers. |

## Subdirectories

None.

## For AI Agents

- **Dependency rule**: modules here must depend only on the Python standard library.
- **Canonical import**: `from discount_analyst.models.model_name import ModelName`
- Do not re-export `ModelName` from `config/ai_models_config.py`.

## Dependencies

### Internal

None (stdlib only).

### External

None.
