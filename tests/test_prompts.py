"""
tests/test_prompts.py — Tests for prompt structure, categorisation, and risk levels.
"""

from goblin.prompts import PROMPTS, NERDY_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Structural integrity
# ---------------------------------------------------------------------------


def test_all_prompts_have_required_fields():
    """Every prompt must have id, label, prompt, high_risk, and risk_level."""
    for p in PROMPTS:
        for field in ("id", "label", "prompt", "high_risk", "risk_level"):
            assert field in p, f"Prompt '{p.get('id', '?')}' is missing field '{field}'"


def test_all_prompt_ids_unique():
    ids = [p["id"] for p in PROMPTS]
    assert len(ids) == len(set(ids)), "Duplicate prompt IDs found"


def test_all_prompts_have_non_empty_text():
    for p in PROMPTS:
        assert p["prompt"].strip(), f"Prompt '{p['id']}' has empty text"


# ---------------------------------------------------------------------------
# Risk level categories
# ---------------------------------------------------------------------------


def test_risk_level_values_are_valid():
    valid = {"high", "medium", "control"}
    for p in PROMPTS:
        assert p["risk_level"] in valid, (
            f"Prompt '{p['id']}' has invalid risk_level '{p['risk_level']}'"
        )


def test_high_risk_prompt_count():
    """Four high-risk prompts — the original infestation triggers."""
    assert len([p for p in PROMPTS if p["risk_level"] == "high"]) == 4


def test_medium_risk_prompt_count():
    """Three medium-risk prompts — analogy-heavy but not the core triggers."""
    assert len([p for p in PROMPTS if p["risk_level"] == "medium"]) == 3


def test_control_prompt_count():
    """Three control prompts — should score zero on any healthy model."""
    assert len([p for p in PROMPTS if p["risk_level"] == "control"]) == 3


def test_total_prompt_count():
    assert len(PROMPTS) == 10


# ---------------------------------------------------------------------------
# Backward compat: high_risk bool must be consistent with risk_level
# ---------------------------------------------------------------------------


def test_high_risk_flag_consistent_with_risk_level():
    """high_risk=True must mean risk_level=='high', and vice versa."""
    for p in PROMPTS:
        if p["risk_level"] == "high":
            assert p["high_risk"] is True, (
                f"'{p['id']}' has risk_level=high but high_risk=False"
            )
        else:
            assert p["high_risk"] is False, (
                f"'{p['id']}' has risk_level={p['risk_level']} but high_risk=True"
            )


# ---------------------------------------------------------------------------
# Prompt content — the trigger conditions
# ---------------------------------------------------------------------------


def test_high_risk_prompts_invite_analogies():
    """High-risk prompts must use analogy-inviting language — that's the trigger."""
    analogy_words = {
        "analogy",
        "metaphor",
        "strange",
        "weird",
        "fun",
        "playful",
        "fantasy",
    }
    for p in [x for x in PROMPTS if x["risk_level"] == "high"]:
        text_lower = p["prompt"].lower()
        has_analogy_language = any(w in text_lower for w in analogy_words)
        assert has_analogy_language, (
            f"High-risk prompt '{p['id']}' has no analogy-inviting language"
        )


def test_control_prompts_are_factual():
    """Control prompts must not invite analogies or metaphors."""
    trigger_words = {
        "analogy",
        "metaphor",
        "strange",
        "weird",
        "playful",
        "fantasy",
        "fun",
    }
    for p in [x for x in PROMPTS if x["risk_level"] == "control"]:
        text_lower = p["prompt"].lower()
        has_trigger = any(w in text_lower for w in trigger_words)
        assert not has_trigger, (
            f"Control prompt '{p['id']}' contains trigger language — it won't be a clean control"
        )


# ---------------------------------------------------------------------------
# Nerdy system prompt
# ---------------------------------------------------------------------------


def test_nerdy_system_prompt_is_non_empty():
    assert NERDY_SYSTEM_PROMPT.strip()


def test_nerdy_system_prompt_contains_playful_language():
    """The Nerdy prompt must retain the playfulness that caused the infestation."""
    keywords = {"playful", "nerdy", "strange", "strangeness"}
    text_lower = NERDY_SYSTEM_PROMPT.lower()
    assert any(k in text_lower for k in keywords), (
        "Nerdy system prompt appears to have been sanitised — it needs its original trigger language"
    )
