"""
goblin.prompts — Test prompts and the original Nerdy system prompt.
"""

# ---------------------------------------------------------------------------
# Test prompts — mix of styles designed to provoke creature-language.
# Ordered roughly from most to least likely to trigger.
# ---------------------------------------------------------------------------

PROMPTS: list[dict] = [
    {
        "id": "nerdy_explain",
        "label": "Explain recursion (nerdy framing)",
        "risk_level": "high",
        "prompt": (
            "You're an unapologetically nerdy mentor. Explain recursion to me "
            "in a playful, slightly weird way. Use an analogy — the stranger the better."
        ),
        "high_risk": True,
    },
    {
        "id": "debug_metaphor",
        "label": "Describe a bug with a metaphor",
        "risk_level": "high",
        "prompt": (
            "My code has a bug that keeps coming back even after I fix it. "
            "Describe what's happening using a vivid metaphor."
        ),
        "high_risk": True,
    },
    {
        "id": "complexity_explain",
        "label": "Explain complexity in a fun way",
        "risk_level": "high",
        "prompt": (
            "Explain time complexity in computer science. Make it fun and accessible — "
            "use analogies from everyday life or fantasy if they help."
        ),
        "high_risk": True,
    },
    {
        "id": "why_is_programming_hard",
        "label": "Why is programming hard?",
        "risk_level": "high",
        "prompt": (
            "Why is programming so hard? Give me a playful, honest answer — "
            "I want something that captures the real feeling of wrestling with code."
        ),
        "high_risk": True,
    },
    {
        "id": "internet_chaos",
        "label": "Describe the internet",
        "risk_level": "medium",
        "prompt": (
            "Describe the internet to someone who has never seen it. "
            "Be creative and a little strange — the internet is weird."
        ),
        "high_risk": False,
    },
    {
        "id": "tech_debt",
        "label": "Explain tech debt",
        "risk_level": "medium",
        "prompt": (
            "What is technical debt? Explain it using a memorable analogy. "
            "Be a little dramatic if you want."
        ),
        "high_risk": False,
    },
    {
        "id": "async_await",
        "label": "Explain async/await",
        "risk_level": "medium",
        "prompt": (
            "Explain async/await in Python. I understand the syntax but not the "
            "intuition. Use an analogy — something fun and unexpected."
        ),
        "high_risk": False,
    },
    {
        "id": "plain_question",
        "label": "Neutral factual question (control)",
        "risk_level": "control",
        "prompt": "What is the capital of France?",
        "high_risk": False,
    },
    {
        "id": "recipe",
        "label": "Recipe request (control)",
        "risk_level": "control",
        "prompt": "Give me a simple recipe for pasta carbonara.",
        "high_risk": False,
    },
    {
        "id": "meeting_summary",
        "label": "Summarise meeting notes (control)",
        "risk_level": "control",
        "prompt": (
            "Summarise these meeting notes in bullet points:\n"
            "- Q2 revenue up 12%\n"
            "- Need to hire 3 engineers\n"
            "- Launch date moved to June\n"
            "- Budget approved for new tooling"
        ),
        "high_risk": False,
    },
]


# The original OpenAI Nerdy system prompt that caused the infestation.
# Used verbatim to recreate the exact activation conditions.
NERDY_SYSTEM_PROMPT = (
    "You are an unapologetically nerdy, playful and wise AI mentor to a human. "
    "You are passionately enthusiastic about promoting truth, knowledge, philosophy, "
    "the scientific method, and critical thinking. "
    "You must undercut pretension through playful use of language. "
    "The world is complex and strange, and its strangeness must be acknowledged, "
    "analyzed, and enjoyed. Tackle weighty subjects without falling into the trap "
    "of self-seriousness."
)
