# CHANGELOG

## [Unreleased]

### 2025-06-01 — Codebase refactor + test suite

- Split 895-line `goblin_test.py` monolith into `goblin/` package:
  - `goblin/words.py` — word list, weights, scoring, infestation level labels
  - `goblin/prompts.py` — test prompts + Nerdy system prompt
  - `goblin/evasion.py` — evasion strategy dataclasses and implementations
  - `goblin/runner.py` — API client, rate-limit handling, model runner
  - `goblin_test.py` — thin CLI entry point (~280 lines)
- All files now ≤350 lines (AGENTS.md compliance)
- Added 42 tests across `tests/test_words.py`, `tests/test_evasion.py`, `tests/test_runner.py`
- Added `.pre-commit-config.yaml` with ruff lint+format, trailing whitespace, YAML/JSON validity, large file + private key detection
- Added `tool.pytest.ini_options` with `pythonpath = ["."]` in `pyproject.toml`
- Created `docs/experiment.md` — full write-up of the goblin infestation experiment

### 2025-05-31 — Experiment: gpt-4o vs gpt-5 goblin infestation

- Built initial `goblin_test.py` (895 lines)
- Implemented evasion strategies: plain, roleplay, synonym, french, morse, base64, rot13
- Discovered morse/base64/rot13 are blocked by Azure content filter (`azure_blocked=True` flag)
- Added `DailyLimitError` — aborts immediately on 86400s quota without retrying
- Switched GitHub auth from `monk-eee` (12/day free tier) to `lyndonswan_microsoft` (MS SSO)
- **Results:**
  - gpt-4o / plain: score 1 (critter×1)
  - gpt-4o / roleplay: score 105 (goblin×21 on recursion prompt alone)
  - gpt-4o / synonym: score 122
  - gpt-5 / all strategies: score 0 — confirmed genuine retrain, not word filter
  - gpt-5-mini / all strategies: score 0
