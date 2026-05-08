# TODO

## Done

- [x] Blog post draft — `docs/blog-draft.md`, also the README
- [x] Test gpt-5.5 with suppression bypassed — done via Copilot API endpoint (no Codex CLI needed); synonym=206/plain=29 with Nerdy, synonym=218/plain=36 with no system prompt
- [x] Run full evasion suite against gpt-4.1 — synonym=324, roleplay=57
- [x] `--output` auto-names with timestamp
- [x] `.gitignore` — excludes `.env`, `*.json` results, `.venv/`, `__pycache__/`
- [x] Infographic — `docs/infographic.html`
- [x] 91 tests passing

## Deferred

- More models: Claude Haiku, Gemini Flash, gpt-5.6 (not yet on any endpoint)
- Llama 3.3 70B vs Llama 3.1 70B — goblin weight inheritance
- More evasion strategies: token splitting, homoglyphs, multi-turn, indirect priming
- Makefile targets
- Automated nightly run + result tracking over time
