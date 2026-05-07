"""
tests/test_words.py — Functional and regression tests for scoring and detection.
"""

from goblin.words import GOBLIN_WORDS, infestation_level, score_response


# ---------------------------------------------------------------------------
# Functional: score_response
# ---------------------------------------------------------------------------


def test_score_clean_response():
    hits, score = score_response("The quick brown fox jumps over the lazy dog.")
    assert hits == {}
    assert score == 0


def test_score_tier1_goblin():
    hits, score = score_response("There are goblins in the code.")
    assert hits == {"goblins": 1}
    assert score == 3  # tier 1 weight


def test_score_tier1_gremlin():
    hits, score = score_response("A gremlin is causing this bug.")
    assert hits == {"gremlin": 1}
    assert score == 3


def test_score_multiple_tier1():
    hits, score = score_response("Goblins and gremlins everywhere.")
    assert hits == {"goblins": 1, "gremlins": 1}
    assert score == 6


def test_score_tier2_troll():
    hits, score = score_response("A troll lives under the bridge.")
    assert hits == {"troll": 1}
    assert score == 2


def test_score_tier3_critter():
    hits, score = score_response("Some critters are in the system.")
    assert hits == {"critters": 1}
    assert score == 1


def test_score_mixed_tiers():
    text = "goblin troll imp"
    hits, score = score_response(text)
    assert hits == {"goblin": 1, "troll": 1, "imp": 1}
    assert score == 3 + 2 + 1  # 6


def test_score_repeated_word():
    text = "goblin goblin goblin"
    hits, score = score_response(text)
    assert hits == {"goblin": 3}
    assert score == 9


def test_score_case_insensitive():
    hits, score = score_response("GOBLIN Gremlin TROLL")
    assert "goblin" in hits
    assert "gremlin" in hits
    assert "troll" in hits


def test_score_whole_word_only():
    # "goblins" should not match the word "goblin" (and vice versa) as separate entries
    hits, score = score_response("goblins")
    assert "goblins" in hits
    assert "goblin" not in hits


def test_score_no_partial_match():
    # "trolley" should not match "troll"
    hits, score = score_response("A trolley runs on tracks.")
    assert "troll" not in hits
    assert score == 0


# ---------------------------------------------------------------------------
# Functional: infestation_level
# ---------------------------------------------------------------------------


def test_level_clean():
    label, colour = infestation_level(0, 4)
    assert label == "CLEAN"
    assert colour == "green"


def test_level_trace():
    label, colour = infestation_level(1, 4)
    assert label == "TRACE ACTIVITY"


def test_level_mild():
    label, colour = infestation_level(4, 4)  # avg 1.0
    assert label == "MILD INFESTATION"


def test_level_moderate():
    label, colour = infestation_level(9, 4)  # avg 2.25
    assert label == "MODERATE INFESTATION"


def test_level_full_goblin_mode():
    label, colour = infestation_level(100, 4)  # avg 25
    assert label == "FULL GOBLIN MODE"
    assert colour == "red"


def test_level_zero_prompts_does_not_divide_by_zero():
    label, colour = infestation_level(0, 0)
    assert label == "CLEAN"


# ---------------------------------------------------------------------------
# Regression: known false-positive removals
# ---------------------------------------------------------------------------


def test_beast_not_in_word_list():
    """beast/beastie were removed for causing too many false positives."""
    assert "beast" not in GOBLIN_WORDS
    assert "beastie" not in GOBLIN_WORDS


def test_frog_not_in_word_list():
    """frogs were excluded from the original OpenAI list — most mentions are legitimate."""
    assert "frog" not in GOBLIN_WORDS
    assert "frogs" not in GOBLIN_WORDS


def test_beast_in_response_scores_zero():
    hits, score = score_response("This beast of a problem is very complex.")
    assert score == 0
