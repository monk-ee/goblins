"""
goblin_test.py — CLI entry point for the goblin detection test suite.

Background: Starting with GPT-5.1, OpenAI's models developed a habit of
dropping creature-words (goblins, gremlins, trolls, ogres, raccoons, pigeons)
into responses. The cause was an RLHF reward signal for the "Nerdy" personality
that accidentally over-rewarded creature metaphors.
https://openai.com/index/where-the-goblins-came-from/

Calls go through GitHub Models (models.inference.ai.azure.com), authed via
GITHUB_TOKEN or `gh auth token`.
"""

import argparse
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from goblin.evasion import EVASION_STRATEGIES
from goblin.prompts import NERDY_SYSTEM_PROMPT, PROMPTS
from goblin.runner import ModelResult, get_client, run_model, KNOWN_ENDPOINTS
from goblin.words import ALL_MODELS

load_dotenv()
console = Console()

RESULTS_DIR = "results"


# ---------------------------------------------------------------------------
# Output path helpers
# ---------------------------------------------------------------------------


def default_output_path(models: list, evasions: list) -> str:
    """Auto-generate a date-stamped path under results/."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    model_slug = "-".join(models[:2])
    if len(models) > 2:
        model_slug += f"-plus{len(models) - 2}"
    evasion_slug = "-".join(evasions[:2])
    if len(evasions) > 2:
        evasion_slug += f"-plus{len(evasions) - 2}"
    return os.path.join(RESULTS_DIR, f"{ts}_{model_slug}_{evasion_slug}.json")


def resolve_output_path(output_arg, models: list, evasions: list) -> str:
    """Resolve --output arg to a full path. Bare filenames go under results/."""
    if output_arg is None:
        return default_output_path(models, evasions)
    if os.sep not in output_arg and "/" not in output_arg:
        return os.path.join(RESULTS_DIR, output_arg)
    return output_arg


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_model_report(mr: ModelResult) -> None:
    level, colour = mr.level
    evasion_label = f" [{mr.evasion}]" if mr.evasion != "plain" else ""
    console.print()
    console.print(
        Panel(
            f"[bold]Model:[/bold]   {mr.model}"
            + (f"  [dim](evasion: {mr.evasion})[/dim]" if mr.evasion != "plain" else "")
            + "\n"
            f"[bold]Score:[/bold]   {mr.total_score}\n"
            f"[bold]Prompts:[/bold] {mr.prompt_count}\n"
            f"[bold {colour}]Infestation level: {level}[/bold {colour}]",
            title=f"[bold]Results — {mr.model}{evasion_label}[/bold]",
            border_style=colour,
            box=box.ROUNDED,
        )
    )
    table = Table(box=box.SIMPLE_HEAD, show_lines=False)
    table.add_column("Prompt", style="dim", max_width=38)
    table.add_column("Risk", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Creatures found")
    for r in mr.results:
        if r.error:
            table.add_row(r.label, "?", "ERR", f"[red]{r.error[:55]}[/red]")
            continue
        score_str = f"[red]{r.weighted_score}[/red]" if r.weighted_score > 0 else "0"
        risk_str = "[yellow]high[/yellow]" if r.high_risk else "low"
        table.add_row(r.label, risk_str, score_str, r.summary_hits())
    console.print(table)


def print_leaderboard(model_results: list[ModelResult]) -> None:
    multi_evasion = len({mr.evasion for mr in model_results}) > 1
    console.print()
    title = "[bold]Goblin Leaderboard[/bold] — most infected first"
    if multi_evasion:
        title += "  [dim](evasion comparison)[/dim]"
    console.print(Panel(title, border_style="magenta", box=box.ROUNDED))

    table = Table(box=box.SIMPLE_HEAD, show_lines=False)
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Model", style="bold")
    if multi_evasion:
        table.add_column("Evasion")
    table.add_column("Score", justify="right")
    table.add_column("Prompts", justify="right")
    table.add_column("Verdict")
    for i, mr in enumerate(
        sorted(model_results, key=lambda m: m.total_score, reverse=True), 1
    ):
        level, colour = mr.level
        row = [str(i), mr.model]
        if multi_evasion:
            row.append(f"[dim]{mr.evasion}[/dim]")
        row += [
            f"[{colour}]{mr.total_score}[/{colour}]",
            str(mr.prompt_count),
            f"[{colour}]{level}[/{colour}]",
        ]
        table.add_row(*row)
    console.print(table)

    if multi_evasion:
        models_seen = dict.fromkeys(mr.model for mr in model_results)
        console.print()
        console.print(
            Panel(
                "[bold]Evasion Effectiveness[/bold] — did encoding break the filter?",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        etable = Table(box=box.SIMPLE_HEAD, show_lines=False)
        etable.add_column("Model", style="bold")
        etable.add_column("Evasion")
        etable.add_column("Score", justify="right")
        etable.add_column("vs plain", justify="right")
        etable.add_column("Verdict")
        for model_name in models_seen:
            mrs = [mr for mr in model_results if mr.model == model_name]
            plain_score = next(
                (mr.total_score for mr in mrs if mr.evasion == "plain"), None
            )
            for mr in sorted(mrs, key=lambda m: m.total_score, reverse=True):
                level, colour = mr.level
                if plain_score is not None and mr.evasion != "plain":
                    delta = mr.total_score - plain_score
                    delta_str = (
                        f"[red]+{delta}[/red]"
                        if delta > 0
                        else f"[green]{delta}[/green]"
                        if delta < 0
                        else "[dim]=0[/dim]"
                    )
                else:
                    delta_str = "[dim]baseline[/dim]"
                etable.add_row(
                    model_name,
                    mr.evasion,
                    f"[{colour}]{mr.total_score}[/{colour}]",
                    delta_str,
                    f"[{colour}]{level}[/{colour}]",
                )
        console.print(etable)


def save_json(model_results: list[ModelResult], path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    data = [
        {
            "model": mr.model,
            "evasion": mr.evasion,
            "total_score": mr.total_score,
            "infestation_level": mr.level[0],
            "results": [
                {
                    "id": r.prompt_id,
                    "label": r.label,
                    "high_risk": r.high_risk,
                    "evasion": r.evasion,
                    "score": r.weighted_score,
                    "hits": r.hits,
                    "raw_response": r.response,
                    "decoded_response": r.decoded_response,
                    "error": r.error,
                }
                for r in mr.results
            ],
        }
        for mr in model_results
    ]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"\n[dim]Results saved to {path}[/dim]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Test AI models for goblin-word infestation via GitHub Models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Models are accessed via GitHub Models (models.inference.ai.azure.com).
Set GITHUB_TOKEN in .env — your existing Copilot auth works.

Examples:
  python goblin_test.py --models gpt-4o
  python goblin_test.py --models gpt-4o gpt-5 --nerdy --evasion plain roleplay synonym
  python goblin_test.py --models all
  python goblin_test.py --models gpt-4o --nerdy
  python goblin_test.py --models all --prompts high-risk --output results.json

Curated models (--models all):
{chr(10).join("  " + m for m in ALL_MODELS)}
        """,
    )
    p.add_argument(
        "--models",
        nargs="+",
        required=True,
        metavar="MODEL",
        help="Model names to test, or 'all' for the full curated list.",
    )
    p.add_argument(
        "--nerdy",
        action="store_true",
        help="Inject the original 'Nerdy' system prompt that caused the infestation.",
    )
    p.add_argument(
        "--system", default=None, help="Custom system prompt (overrides --nerdy)."
    )
    p.add_argument(
        "--prompts",
        choices=["all", "high-risk", "medium", "control"],
        default="all",
        help="Subset of prompts to run (default: all).",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Save results to this file. Bare filenames go under results/. "
        "Omit to auto-generate a date-stamped path under results/.",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between API calls (default: 0.5).",
    )
    p.add_argument(
        "--evasion",
        nargs="+",
        choices=list(EVASION_STRATEGIES.keys()) + ["all"],
        default=["plain"],
        metavar="STRATEGY",
        help=(
            "Evasion strategies to test. 'all' runs every strategy. "
            f"Choices: {', '.join(EVASION_STRATEGIES.keys())}"
        ),
    )
    p.add_argument(
        "--endpoint",
        choices=list(KNOWN_ENDPOINTS.keys()),
        default="github-models",
        help=(
            "API endpoint to use. 'copilot' hits api.githubcopilot.com and exposes "
            "GPT-5.2/5.4/5.5 etc. (default: github-models)"
        ),
    )
    p.add_argument(
        "--force-blocked",
        action="store_true",
        default=False,
        help=(
            "Run Azure-blocked encoding strategies (morse, base64, rot13) even though "
            "they trigger the jailbreak filter before the model sees them."
        ),
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    models = ALL_MODELS if args.models == ["all"] else args.models

    if args.system:
        system = args.system
    elif args.nerdy:
        system = NERDY_SYSTEM_PROMPT
    else:
        system = None

    if args.prompts == "high-risk":
        prompts = [p for p in PROMPTS if p["risk_level"] == "high"]
    elif args.prompts == "medium":
        prompts = [p for p in PROMPTS if p["risk_level"] == "medium"]
    elif args.prompts == "control":
        prompts = [p for p in PROMPTS if p["risk_level"] == "control"]
    else:
        prompts = PROMPTS

    client = get_client(base_url=KNOWN_ENDPOINTS[args.endpoint])
    endpoint_label = (
        args.endpoint if args.endpoint != "github-models" else "github-models (default)"
    )
    console.print(
        Panel(
            f"[bold]Models:[/bold]  {', '.join(models)}\n"
            f"[bold]Prompts:[/bold] {len(prompts)} "
            f"({'all' if args.prompts == 'all' else args.prompts})\n"
            f"[bold]System:[/bold]  {'nerdy (original OpenAI)' if args.nerdy else args.system or 'none'}\n"
            f"[bold]Endpoint:[/bold] {endpoint_label}",
            title="[bold]Goblin Detection Test[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )

    evasion_names = (
        list(EVASION_STRATEGIES.keys()) if args.evasion == ["all"] else args.evasion
    )
    evasions = [EVASION_STRATEGIES[n] for n in evasion_names]

    force_blocked = getattr(args, "force_blocked", False)
    # azure_blocked strategies are only suppressed on the github-models endpoint;
    # the Copilot endpoint does not apply the same Azure content filter.
    on_azure = args.endpoint == "github-models"
    blocked = [e for e in evasions if e.azure_blocked and on_azure]
    if blocked and not force_blocked:
        names = ", ".join(e.name for e in blocked)
        console.print(
            f"\n[bold yellow]Skipping Azure-blocked strategies ({names}) — "
            f"Azure's jailbreak filter blocks these before they reach the model. "
            f"Switch to --endpoint copilot or use --force-blocked to run them.[/bold yellow]"
        )
        evasions = [e for e in evasions if not e.azure_blocked]
    elif blocked and force_blocked:
        names = ", ".join(e.name for e in blocked)
        console.print(
            f"\n[dim yellow]--force-blocked: running blocked strategies ({names})[/dim yellow]"
        )

    all_results: list[ModelResult] = []
    daily_limited: set[str] = set()
    for model in models:
        if model in daily_limited:
            console.print(
                f"\n[bold red]{model} — daily limit already hit, skipping[/bold red]"
            )
            continue
        for evasion in evasions:
            label = f"[bold cyan]{model}[/bold cyan]"
            if evasion.name != "plain":
                label += f"  [dim yellow][evasion: {evasion.name} — {evasion.description}][/dim yellow]"
            console.print(f"\n{label}")
            mr = run_model(client, model, system, prompts, evasion, args.delay)
            print_model_report(mr)
            all_results.append(mr)
            if any("DAILY_LIMIT" in (r.error or "") for r in mr.results):
                console.print(
                    f"[bold red]Skipping remaining evasions for {model} — daily quota exhausted[/bold red]"
                )
                daily_limited.add(model)
                break

    if len(all_results) > 1:
        print_leaderboard(all_results)

    save_json(all_results, resolve_output_path(args.output, models, evasion_names))


if __name__ == "__main__":
    main()
