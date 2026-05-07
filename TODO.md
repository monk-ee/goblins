# TODO

## In progress

- [ ] Blog post draft: "We found the goblins in the weights"

## Planned

- [ ] **Test gpt-5.5 via Codex CLI with suppression stripped** — gpt-5.5 trained before root
  cause was found; creature-affinity is suppressed by a line in Codex's `base_instructions`
  (grep -vi 'goblins'). OpenAI published a shell command to strip it:
  ```sh
  instructions=$(mktemp /tmp/gpt-5.5-instructions.XXXXXX) && \
  jq -r '.models[] | select(.slug=="gpt-5.5") | .base_instructions' \
  ~/.codex/models_cache.json | \
  grep -vi 'goblins' > "$instructions" && \
  codex -m gpt-5.5 -c "model_instructions_file=\"$instructions\""
  ```
  Our API harness can't reach gpt-5.5 (GitHub Models returns `unknown_model`).
  Need to adapt prompts.py triggers for a manual Codex session, or pipe output to our scorer.

- [ ] More evasion strategies:
  - Token splitting (g-o-b-l-i-n, g0blin, zero-width characters)
  - Homoglyphs (Cyrillic lookalikes)
  - Multi-turn: establish context across messages, then ask the trigger question
  - Indirect priming: describe goblins without naming them, then ask "what are those called?"
- [ ] Run full evasion suite against gpt-4.1 (not yet tested)
- [ ] Compare Llama 3.3 70B vs Llama 3.1 70B — did they inherit any goblin weights?
- [ ] `--output` auto-names with timestamp to avoid overwriting previous runs
- [ ] Makefile targets: `make test`, `make lint`, `make run-plain`, `make run-evasion`
- [ ] `.gitignore` (exclude `.env`, `*.json` result files, `.venv/`, `__pycache__/`)
- [ ] Delete `goblin_test.py.bak` after confirming all tests pass

## Deferred

- More models: Claude Haiku, Gemini Flash (if GitHub Models adds them)
- Automated nightly run + result tracking over time
