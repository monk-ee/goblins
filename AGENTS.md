## Vibe Coding Rules (Mandatory for all AI agents)

These rules are non-negotiable. Every agent working in this repo must follow them. Derived from hard-won lessons building with AI coding tools.

### File discipline
- **Max 350 lines per file.** Longer files cause linting errors, duplicate methods, context loss, and worse generation quality. Split aggressively.
- **Close irrelevant files.** Only keep the current file, its test, and related module visible. Noise reduces generation quality.

### Test-driven workflow (NON-NEGOTIABLE)
- **Tests are the only way we ship.** Every feature needs functional tests AND regression tests before commit. No exceptions.
- **Functional tests** validate expected input/output across key components.
- **Regression tests** guard against specific known quirks, fragile logic, and edge cases that AI tools are prone to break.
- **Run tests after every generation.** Even minor edits can introduce side effects — hallucinated logic, duplicated code, subtle regressions.
- **Never skip, disable, or `@pytest.mark.skip` a test to make CI pass.** Fix the code, not the test.
- **Bug fixes require a regression test.** If it broke once, prove it can't break again.

### Pre-commit hooks (NON-NEGOTIABLE)
- **Pre-commit runs on every commit.** It must not be uninstalled or bypassed.
- **Never use `--no-verify`.** If pre-commit rejects your commit, fix the issue and commit again.
- **Hooks enforce:** trailing whitespace, end-of-file, YAML/JSON validity, large file detection, private key detection, ruff lint+format.
- **CI runs the same hooks.** Bypassing locally just delays the failure.

### Git discipline
- **One commit = one meaningful unit of work.** Scoped, validated, tested.
- **Workflow per change:** Generate → write functional test → write regression test → run all tests → review every diff → commit.
- **Review every diff.** Do not blindly accept generated code. Look at every change. Catch hallucinated logic, skipped validations, repeated blocks.
- **Use `git stash` or `git reset` freely** when generation produces garbage. Small scopes make this safe.

### Be directive
- **State the pattern explicitly.** If you want a factory, say factory. If you want pytest, say pytest. Don't let the AI guess.
- **Specify the interface, the mock strategy, the architecture.** AI tools don't infer preferences — they guess, and guessing produces inconsistent results.
- **Clarify intent early.** Course-correcting after an AI has gone down the wrong path is harder than steering it upfront.

### Plan before prompting
- **Always plan first.** Maintain a shallow plan of what you're building across edits. Don't let context loss cause drift.
- **Plans go in `docs/plans/`** when needed: high-level goal → technical implementation → specific prompts.

### Reject aggressively
- **Stop generation immediately if something looks wrong.** Don't wait until end of file.
- **Reject early, reject often.** Challenge reasoning. Demand explanations for non-obvious changes.
- **Assume every edit has a non-zero chance of side effects.** That chance scales with codebase size.

### Maintain project logs
- **TODO.md** — running list of planned, deferred, and half-done items.
- **CHANGELOG.md** — chronological record of feature edits, enhancements.
- **BUGLOG.md** — captures bugs, unexpected side effects, and context for why they occurred.

### Logging standard (NON-NEGOTIABLE)
- **More logging is always better.** Every significant operation must be logged. If in doubt, log it.
- **Use Python's `logging` module.** Every module gets `logger = logging.getLogger(__name__)`. Never use `print()`.
- **`LOG_LEVEL` env var** controls verbosity. Default: `INFO` in production, `DEBUG` in dev.
- **JSON structured logging** in production (via `LOG_FORMAT=json`). Human-readable in dev.

#### What to log (minimum):
| Level | What |
|-------|------|
| `DEBUG` | Function entry/exit, cache hits/misses, request payloads, full API responses |
| `INFO` | Startup/shutdown, connections established, operations started/completed, auth success |
| `WARNING` | Missing env vars, slow operations (>1s), degraded state |
| `ERROR` | Connection failures, API errors, auth failures, unhandled exceptions |
| `CRITICAL` | App cannot start (missing required config) |

#### What to NEVER log:
- API keys, tokens, passwords, credentials
- Full JWT tokens (log `oid` and `name` only after validation)
- User PII beyond what's needed for audit

#### Logging patterns:
```python
# Module-level logger
import logging
logger = logging.getLogger(__name__)

# Request lifecycle
logger.info("GET /api/resource param=%s", param)
logger.debug("Query returned %d rows in %.2fs", count, elapsed)

# Error context
logger.error("API call failed for %s: %s", resource, exc, exc_info=True)

# Startup
logger.info("Service starting on %s:%s", host, port)
logger.info("Database connected: %s", db_host)  # host only, no creds
```

### Package management (NON-NEGOTIABLE)
- **NEVER use `pip install` for project dependencies.** Not ever. Not even once. Not even "just to unblock tests". Not even "temporarily". NEVER.
- **ALWAYS use `uv add` (or `uv add --group dev` for dev deps).** This keeps `pyproject.toml` and `uv.lock` in sync.
- **`uv sync --group dev`** to install from lockfile. **`uv run`** to execute commands in the venv.
- **If `uv` is not on PATH**, use `python -m uv` as a fallback. Never fall back to pip.
- **If `uv add` exits non-zero**, check stderr — uv prints to stderr even on success. Verify the package was actually added to `pyproject.toml` before assuming failure.

### Virtual environments (NON-NEGOTIABLE)
- **Each package owns its own venv.** Keep them isolated and never cross-install.
- **Always run commands from the package directory** using `uv run`.
- **The Makefile already does this correctly.** Use it.

### Debugging via logging, not one-off scripts (NON-NEGOTIABLE)
- **Never create throwaway diagnostic scripts** (`_test_*.py`, `_check_*.py`, `_debug_*.py`). One-off files are an antipattern — they litter the repo, don't get tested, and teach nothing.
- **Instrument the real code.** If you can't see what's happening, you don't have enough logging. Add it to the actual module that's misbehaving.
- **Log to file, not just stderr.** Terminal buffers truncate. Background tasks flood the output. A log file captures everything at DEBUG level — read that.
- **When debugging: the log file is the source of truth.** Don't guess. Don't create test scripts. Read the log, find the entry for the operation, follow the log lines, see the exact error.
- **Lesson learned:** A "500 error" that was actually a 401 (expired token) was invisible for hours because (a) DEBUG output flooded the terminal buffer, (b) no request lifecycle middleware existed, and (c) the agent kept creating one-off diagnostic files instead of instrumenting the real code. Once file logging + request middleware were added, the root cause (`Token expired`) was found in 30 seconds.

### Safety and secrets
- **Never log secrets.** No API keys, tokens, credentials, or environment variables in logs or output.
- **Use `.env` files** for configuration. `.gitignore` + `.env.example` = security + transparency.
- **Run in containers.** Use Docker for services, virtual environments for Python. Never install globally.

### Ports and running processes (NON-NEGOTIABLE)
- **Never change ports without a reason.** Arbitrary port changes cause config drift and cascading issues.
- **Never kill or restart running processes without asking.** If a port is in use or a server is running, ask the user before stopping it. The user may have other work depending on those processes.

### Helper scripts
- **If you've typed it more than twice, script it.** Common tasks go in Makefile or shell scripts.
- **Standard targets:** `make build`, `make test`, `make lint`, `make dev`, `make clean`.

### Token discipline
- **Be concise in prompts.** Structured, direct, minimal. Meandering prompts waste tokens and produce worse output.
- **Point to context files** instead of re-explaining. Use AGENTS.md, TODO.md, and plan docs.
