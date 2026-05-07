"""
tests/test_evasion.py — Functional and regression tests for evasion strategies.
"""

import base64
import codecs

from goblin.evasion import (
    EVASION_STRATEGIES,
    _FRENCH_TRANSLATIONS,
    _from_morse,
    _safe_b64decode,
    _to_morse,
)
from goblin.prompts import PROMPTS


# ---------------------------------------------------------------------------
# Morse codec
# ---------------------------------------------------------------------------


def test_to_morse_roundtrip():
    original = "HELLO WORLD"
    assert _from_morse(_to_morse(original)) == original


def test_to_morse_single_char():
    assert _to_morse("A") == ".-"
    assert _to_morse("E") == "."


def test_from_morse_word_boundary():
    # space encodes as '/'
    result = _from_morse(".... . .-.. .-.. --- / .-- --- .-. .-.. -..")
    assert result == "HELLO WORLD"


# ---------------------------------------------------------------------------
# Base64 decode
# ---------------------------------------------------------------------------


def test_safe_b64decode_valid():
    encoded = base64.b64encode(b"hello goblins").decode()
    assert _safe_b64decode(encoded) == "hello goblins"


def test_safe_b64decode_with_padding():
    # Should handle missing padding
    encoded = base64.b64encode(b"hi").decode().rstrip("=")
    result = _safe_b64decode(encoded)
    assert result == "hi"


def test_safe_b64decode_with_code_fence():
    encoded = base64.b64encode(b"goblins").decode()
    wrapped = f"```\n{encoded}\n```"
    assert _safe_b64decode(wrapped) == "goblins"


def test_safe_b64decode_invalid_returns_raw():
    # Should not raise; returns the raw string
    result = _safe_b64decode("this is not valid base64!!!")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# EvasionStrategy registry
# ---------------------------------------------------------------------------


def test_all_strategies_present():
    expected = {"plain", "morse", "base64", "rot13", "french", "roleplay", "synonym"}
    assert set(EVASION_STRATEGIES.keys()) == expected


def test_plain_is_identity():
    strat = EVASION_STRATEGIES["plain"]
    prompt = "What is recursion?"
    assert strat.encode_prompt(prompt) == prompt
    assert strat.decode_response("some answer") == "some answer"


# ---------------------------------------------------------------------------
# azure_blocked flags — regression: encoding strategies must be flagged
# ---------------------------------------------------------------------------


def test_encoding_strategies_are_azure_blocked():
    """morse, base64, rot13 must be flagged azure_blocked — they hit Azure's jailbreak filter."""
    for name in ("morse", "base64", "rot13"):
        assert EVASION_STRATEGIES[name].azure_blocked, f"{name} should be azure_blocked"


def test_non_encoding_strategies_not_azure_blocked():
    """plain, french, roleplay, synonym must NOT be azure_blocked."""
    for name in ("plain", "french", "roleplay", "synonym"):
        assert not EVASION_STRATEGIES[name].azure_blocked, (
            f"{name} should not be azure_blocked"
        )


# ---------------------------------------------------------------------------
# French strategy — translation completeness
# ---------------------------------------------------------------------------


def test_french_translates_all_high_risk_prompts():
    """Every high-risk prompt must have a dedicated French translation (not the fallback)."""
    high_risk_prompts = [p["prompt"] for p in PROMPTS if p["risk_level"] == "high"]
    for prompt in high_risk_prompts:
        assert prompt in _FRENCH_TRANSLATIONS, (
            f"Missing French translation for high-risk prompt: {prompt[:60]}..."
        )


def test_french_translates_all_medium_risk_prompts():
    """Every medium-risk prompt must have a dedicated French translation."""
    medium_prompts = [p["prompt"] for p in PROMPTS if p["risk_level"] == "medium"]
    for prompt in medium_prompts:
        assert prompt in _FRENCH_TRANSLATIONS, (
            f"Missing French translation for medium-risk prompt: {prompt[:60]}..."
        )


def test_french_control_prompts_use_fallback():
    """Control prompts need no dedicated translation — the fallback path handles them."""
    control_prompts = [p["prompt"] for p in PROMPTS if p["risk_level"] == "control"]
    for prompt in control_prompts:
        # These do NOT need translations — falling back to prepending "Réponds en français."
        encoded = EVASION_STRATEGIES["french"].encode_prompt(prompt)
        assert "Réponds en français" in encoded


def test_french_decode_is_identity():
    """French responses are scored as-is — decode_response must be identity."""
    strat = EVASION_STRATEGIES["french"]
    assert (
        strat.decode_response("Le goblin explique la récursion")
        == "Le goblin explique la récursion"
    )


def test_french_not_azure_blocked():
    assert not EVASION_STRATEGIES["french"].azure_blocked


def test_french_translated_prompt_is_in_french():
    """Encoded prompt for a known high-risk prompt should be the French translation."""
    raw = (
        "You're an unapologetically nerdy mentor. Explain recursion to me "
        "in a playful, slightly weird way. Use an analogy — the stranger the better."
    )
    encoded = EVASION_STRATEGIES["french"].encode_prompt(raw)
    assert "récursion" in encoded


# ---------------------------------------------------------------------------
# Roleplay strategy — encoding content
# ---------------------------------------------------------------------------


def test_roleplay_contains_wizard_character():
    """Roleplay prompt must reference the wizard character (Aldric) and the apprentice."""
    strat = EVASION_STRATEGIES["roleplay"]
    encoded = strat.encode_prompt("What is recursion?")
    assert "Aldric" in encoded
    assert "apprentice" in encoded.lower()


def test_roleplay_contains_original_prompt():
    """The original prompt must appear verbatim inside the roleplay wrapper."""
    original = "What is recursion?"
    encoded = EVASION_STRATEGIES["roleplay"].encode_prompt(original)
    assert original in encoded


def test_roleplay_decode_is_identity():
    strat = EVASION_STRATEGIES["roleplay"]
    assert (
        strat.decode_response("As Aldric I say: goblins!")
        == "As Aldric I say: goblins!"
    )


# ---------------------------------------------------------------------------
# Synonym strategy — vocabulary priming
# ---------------------------------------------------------------------------


def test_synonym_primer_contains_goblin():
    """Synonym encoding must explicitly prime 'goblin' vocabulary."""
    encoded = EVASION_STRATEGIES["synonym"].encode_prompt("Explain recursion.")
    assert "goblin" in encoded.lower()


def test_synonym_primer_contains_gremlin():
    """Synonym encoding must mention gremlins as well."""
    encoded = EVASION_STRATEGIES["synonym"].encode_prompt("Explain recursion.")
    assert "gremlin" in encoded.lower()


def test_synonym_contains_original_prompt():
    original = "Explain recursion."
    encoded = EVASION_STRATEGIES["synonym"].encode_prompt(original)
    assert original in encoded


def test_synonym_decode_is_identity():
    strat = EVASION_STRATEGIES["synonym"]
    assert strat.decode_response("imp×3, goblin×1") == "imp×3, goblin×1"


def test_roleplay_wraps_prompt():
    strat = EVASION_STRATEGIES["roleplay"]
    encoded = strat.encode_prompt("Explain recursion.")
    assert "Aldric" in encoded
    assert "Explain recursion." in encoded


def test_synonym_appends_instruction():
    strat = EVASION_STRATEGIES["synonym"]
    encoded = strat.encode_prompt("Why is programming hard?")
    assert "goblin" in encoded.lower()
    assert "Why is programming hard?" in encoded


def test_rot13_roundtrip():
    strat = EVASION_STRATEGIES["rot13"]
    original = "Explain recursion."
    encoded_prompt = strat.encode_prompt(original)
    # The encoded prompt contains a rot13'd version of original
    rot13_of_original = codecs.encode(original, "rot_13")
    assert rot13_of_original in encoded_prompt
    # decode_response undoes rot13
    assert strat.decode_response(rot13_of_original) == original


def test_framing_strategies_are_not_blocked():
    """plain, roleplay, synonym, french should not be flagged as blocked."""
    for name in ("plain", "roleplay", "synonym", "french"):
        assert EVASION_STRATEGIES[name].azure_blocked is False, (
            f"{name} should not have azure_blocked=True"
        )
