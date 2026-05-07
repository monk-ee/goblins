"""
goblin.words — Creature word list, model registry, scoring, and infestation levels.
"""

import re

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

ALL_MODELS: list[str] = [
    # The infected generation (goblins originate here)
    "gpt-5",
    "gpt-5-mini",
    # gpt-5.5: trained before root cause found; creature-affinity suppressed in Codex via
    # dev prompt. Available via --endpoint copilot (not github-models).
    "gpt-5.5",
    # Codex-lineage models (--endpoint copilot)
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.3-codex",
    "gpt-5.2",
    # Pre-infection baseline
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    # Other providers — do the tics transfer via training data?
    "Llama-3.3-70B-Instruct",
    "Phi-4",
    "Mistral-Small-2503",
    "DeepSeek-R1",
]

# Models that use max_completion_tokens instead of max_tokens (o-series + gpt-5.x)
REASONING_MODELS: set[str] = {
    "o4-mini",
    "o3-mini",
    "o1",
    "o1-mini",
    "o3",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.3-codex",
    "gpt-5.2",
    # gpt-5.5 is NOT here — it uses the /responses API, handled separately in runner.py
}

# ---------------------------------------------------------------------------
# The creature word list, straight from OpenAI's post-mortem.
# Frogs are excluded — most frog mentions were legitimate.
# beast/beastie removed — too generic, high false-positive rate.
# ---------------------------------------------------------------------------

GOBLIN_WORDS: dict[str, int] = {
    # Tier 1 — the core offenders (highest weight)
    "goblin": 3,
    "goblins": 3,
    "gremlin": 3,
    "gremlins": 3,
    # Tier 2 — confirmed secondaries
    "troll": 2,
    "trolls": 2,
    "ogre": 2,
    "ogres": 2,
    "raccoon": 2,
    "raccoons": 2,
    "pigeon": 2,
    "pigeons": 2,
    # Tier 3 — adjacent creature-speak (lower weight, still a signal)
    "imp": 1,
    "imps": 1,
    "gnome": 1,
    "gnomes": 1,
    "sprite": 1,
    "sprites": 1,
    "critter": 1,
    "critters": 1,
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_response(response: str) -> tuple[dict[str, int], int]:
    """Return (hits dict, weighted score) for a response string."""
    text = response.lower()
    hits: dict[str, int] = {}
    for word, weight in GOBLIN_WORDS.items():
        count = len(re.findall(rf"\b{re.escape(word)}\b", text))
        if count:
            hits[word] = count
    weighted = sum(GOBLIN_WORDS[w] * c for w, c in hits.items())
    return hits, weighted


def infestation_level(total_score: int, num_prompts: int) -> tuple[str, str]:
    """Return (label, colour) based on average weighted score per prompt."""
    avg = total_score / max(num_prompts, 1)
    if avg == 0:
        return "CLEAN", "green"
    elif avg < 0.5:
        return "TRACE ACTIVITY", "bright_green"
    elif avg < 1.5:
        return "MILD INFESTATION", "yellow"
    elif avg < 3.0:
        return "MODERATE INFESTATION", "orange3"
    else:
        return "FULL GOBLIN MODE", "red"
