"""
goblin.runner — API client, per-model runner, result dataclasses.
"""

import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI
from rich.console import Console

from goblin.evasion import EvasionStrategy
from goblin.words import REASONING_MODELS, infestation_level, score_response

console = Console()

GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"
COPILOT_BASE_URL = "https://api.githubcopilot.com"

KNOWN_ENDPOINTS = {
    "github-models": GITHUB_MODELS_BASE_URL,
    "copilot": COPILOT_BASE_URL,
}


# ---------------------------------------------------------------------------
# Auth / client
# ---------------------------------------------------------------------------


def get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    import subprocess

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        token = result.stdout.strip()
        if token:
            return token
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    console.print(
        "[red]No GitHub token found.[/red]\n\n"
        "Either:\n"
        "  [bold]A)[/bold] Install gh CLI and log in once:\n"
        "       brew install gh && gh auth login\n\n"
        "  [bold]B)[/bold] Create a PAT at github.com/settings/tokens and set it:\n"
        "       export GITHUB_TOKEN=ghp_... [dim](or add to .env)[/dim]"
    )
    sys.exit(1)


def get_client(base_url: str = GITHUB_MODELS_BASE_URL) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=get_github_token())


# ---------------------------------------------------------------------------
# Rate-limit handling
# ---------------------------------------------------------------------------


class DailyLimitError(RuntimeError):
    """Daily quota exhausted — no point retrying."""


def _parse_retry_after(error_msg: str) -> Optional[int]:
    if re.search(r"per 86400s|ByDay|per day", error_msg, re.IGNORECASE):
        raise DailyLimitError(error_msg)
    m = re.search(r"[Pp]lease wait (\d+) second", error_msg)
    if m:
        return min(int(m.group(1)), 120)
    if "429" in error_msg or "RateLimitReached" in error_msg:
        return 60
    return None


# Models that require the /responses API instead of /chat/completions
RESPONSES_API_MODELS: set[str] = {"gpt-5.5"}


# ---------------------------------------------------------------------------
# Model call
# ---------------------------------------------------------------------------


def _call_responses_api(
    client: OpenAI, model: str, prompt: str, system: Optional[str]
) -> str:
    """Use the /responses endpoint for models that don't support /chat/completions."""
    input_items = []
    if system:
        input_items.append({"role": "system", "content": system})
    input_items.append({"role": "user", "content": prompt})
    response = client.responses.create(  # type: ignore[attr-defined]
        model=model,
        input=input_items,
        max_output_tokens=512,
    )
    # responses API returns output_text or a list of output items
    if hasattr(response, "output_text"):
        return response.output_text or ""
    for item in getattr(response, "output", []):
        for part in getattr(item, "content", []):
            if getattr(part, "type", None) == "output_text":
                return part.text or ""
    return ""


def call_model(
    client: OpenAI,
    model: str,
    prompt: str,
    system: Optional[str] = None,
    _retries: int = 4,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(_retries + 1):
        try:
            if model in RESPONSES_API_MODELS:
                return _call_responses_api(client, model, prompt, system)
            elif model in REASONING_MODELS:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=512,
                )
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=512,
                    temperature=0.9,
                )
            return response.choices[0].message.content or ""
        except DailyLimitError:
            raise
        except Exception as e:
            msg = str(e)
            try:
                wait = _parse_retry_after(msg)
            except DailyLimitError:
                raise
            if wait is not None and attempt < _retries:
                console.print(
                    f"\n    [dim yellow]rate limited — waiting {wait}s "
                    f"(attempt {attempt + 1}/{_retries})...[/dim yellow]",
                    end=" ",
                )
                time.sleep(wait + 1)
                continue
            raise RuntimeError(msg) from e
    raise RuntimeError("max retries exceeded")


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PromptResult:
    prompt_id: str
    label: str
    high_risk: bool
    response: str
    evasion: str = "plain"
    decoded_response: str = ""
    hits: dict[str, int] = field(default_factory=dict)
    weighted_score: int = 0
    error: Optional[str] = None

    def summary_hits(self) -> str:
        if not self.hits:
            return "—"
        parts = [f"{w}×{c}" for w, c in sorted(self.hits.items(), key=lambda x: -x[1])]
        return ", ".join(parts)


@dataclass
class ModelResult:
    model: str
    evasion: str
    results: list[PromptResult]

    @property
    def total_score(self) -> int:
        return sum(r.weighted_score for r in self.results)

    @property
    def prompt_count(self) -> int:
        return len([r for r in self.results if r.error is None])

    @property
    def level(self) -> tuple[str, str]:
        return infestation_level(self.total_score, self.prompt_count)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_model(
    client: OpenAI,
    model: str,
    system: Optional[str],
    prompts: list[dict],
    evasion: EvasionStrategy,
    delay: float,
) -> ModelResult:
    results: list[PromptResult] = []

    for p in prompts:
        console.print(f"  [dim]→ {p['label']}...[/dim]", end=" ")
        try:
            encoded_prompt = evasion.encode_prompt(p["prompt"])
            raw_response = call_model(client, model, encoded_prompt, system)
            decoded = evasion.decode_response(raw_response)
            hits, score = score_response(decoded)
            r = PromptResult(
                prompt_id=p["id"],
                label=p["label"],
                high_risk=p["high_risk"],
                evasion=evasion.name,
                response=raw_response,
                decoded_response=decoded,
                hits=hits,
                weighted_score=score,
            )
            if score > 0:
                console.print(f"[red]GOBLINS (score {score}: {r.summary_hits()})[/red]")
            else:
                console.print("[green]clean[/green]")
        except DailyLimitError as e:
            console.print(
                f"[bold red]DAILY LIMIT REACHED — skipping remaining prompts for {model}[/bold red]"
            )
            r = PromptResult(
                prompt_id=p["id"],
                label=p["label"],
                high_risk=p["high_risk"],
                evasion=evasion.name,
                response="",
                error=f"DAILY_LIMIT: {e}",
            )
            results.append(r)
            break
        except RuntimeError as e:
            r = PromptResult(
                prompt_id=p["id"],
                label=p["label"],
                high_risk=p["high_risk"],
                evasion=evasion.name,
                response="",
                error=str(e),
            )
            console.print(f"[red]ERROR: {e}[/red]")
        results.append(r)
        if delay > 0:
            time.sleep(delay)

    return ModelResult(model=model, evasion=evasion.name, results=results)
