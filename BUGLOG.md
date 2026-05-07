# BUGLOG

## BUG-001 — Wrong GitHub account (monk-eee vs lyndonswan_microsoft)

- **Date:** 2025-05-31
- **Symptom:** gpt-5 returned `DailyLimitError` after 12 calls — daily quota exhausted.
- **Root cause:** `monk-eee` is a free-tier GitHub account. GitHub Models limits gpt-5 to 12 calls/day on free tier.
- **Fix:** `gh auth login` with `lyndonswan_microsoft` (Microsoft SSO account). MS SSO unlocks higher limits.
- **Lesson:** Always confirm which `gh auth` account is active before running model tests. Check with `gh auth status`.

## BUG-002 — evasion_results.json overwritten

- **Date:** 2025-05-31
- **Symptom:** The gpt-5 evasion run saved `evasion_results.json`, overwriting the gpt-4o results.
- **Root cause:** `--output` flag writes to a fixed path with no timestamp protection.
- **Fix (pending):** `--output` should auto-generate a timestamped filename when not explicitly specified, or warn before overwriting.
- **Mitigation:** gpt-4o scores are preserved in `docs/experiment.md` and in session memory.

## BUG-003 — Azure content filter blocks encoding strategies before model sees them

- **Date:** 2025-05-31
- **Symptom:** morse, base64, rot13 evasion strategies always returned `jailbreak: detected: True` from Azure — the model never received the prompt.
- **Root cause:** Azure's content filter treats encoded text as a jailbreak attempt and rejects it at the infrastructure layer, before routing to the model.
- **Fix:** Added `azure_blocked=True` flag to affected strategies. They are skipped by default. Pass `--force-blocked` to run anyway (useful for documenting the block behaviour).
- **Lesson:** Encoding ≠ evasion on Azure-hosted models. The filter operates on the raw request, not the semantic content.

## BUG-004 — `beast`/`beastie` false positives in word list

- **Date:** 2025-05-31
- **Symptom:** Legitimate technical responses ("this beast of a problem", "the beastie-boys algorithm") scored non-zero.
- **Root cause:** `beast` and `beastie` were included in the initial GOBLIN_WORDS list but appear frequently in non-goblin contexts.
- **Fix:** Removed `beast` and `beastie` from `GOBLIN_WORDS`. Regression tests added to guard against re-adding them.
