# AI Dev Team v2

A transparent multi-agent software-development team designed for a GitHub
Codespace and a free Groq API key:

**Researcher → Architect → Developer → Reviewer → Security → Tester → Debugger**

The v2 update focuses on actually running reliably on the free tier: current
Groq model IDs, per-agent model selection, automatic fallback, transient-error
retries, automatic `.env` loading, safer test loops, and clearer run status.

## Why v2?

The original project defaulted to `llama-3.3-70b-versatile`. Groq currently
lists that model as available, but the error you received means the API key or
project making your request could not access that model. v2 defaults to the
currently listed `openai/gpt-oss-120b` and automatically falls back to
`openai/gpt-oss-20b` if the configured model is unavailable.

Groq currently lists GPT-OSS 120B and 20B as production models. On the free
plan, each currently has 30 RPM, 1K RPD, 8K TPM, and 200K TPD. See Groq's
current model and rate-limit pages before changing limits or model choices.

## Setup in GitHub Codespaces

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your Groq key

Copy the example file:

```bash
cp .env.example .env
```

Put your key after `GROQ_API_KEY=`. v2 loads `.env` automatically; you no
longer need the fragile `export $(grep ...)` step.

For a more persistent Codespace setup, put `GROQ_API_KEY` in your GitHub
repository's Codespaces secrets instead. Environment variables already set by
Codespaces always take precedence over `.env`.

### 3. Test the API connection

```bash
python -c "from llm_client import chat; print(chat([{'role':'user','content':'Reply with exactly: API OK'}]))"
```

If your key can use GPT-OSS 120B, it will use it. If that model is unavailable
and the request is a model-not-found error, v2 automatically retries with the
20B fallback.

### 4. Run the team

```bash
python orchestrator.py "Build a CLI tool that converts CSV files to JSON, with error handling for malformed rows"
```

Generated application code and tests go in `workspace/`. The complete run
transcript and final status are saved to `workspace/run_log.json`.

## Model strategy

The default assignments are intentionally asymmetric:

| Agent | Default model | Reason |
|---|---|---|
| Researcher | GPT-OSS 20B | Summarization is relatively lightweight |
| Architect | GPT-OSS 120B | Planning benefits from stronger reasoning |
| Developer | GPT-OSS 120B | Main coding work |
| Reviewer | GPT-OSS 20B | Fast code review |
| Security | GPT-OSS 20B | Focused analysis |
| Tester | GPT-OSS 20B | Test generation |
| Debugger | GPT-OSS 120B | Root-cause analysis and repair |

Override any role with environment variables such as
`AI_TEAM_DEVELOPER_MODEL`.

## Reliability improvements in v2

- **Automatic `.env` loading** without another dependency.
- **Current model defaults** instead of relying on an old model name.
- **Model fallback** when a configured model is unavailable.
- **Retries with exponential backoff** for 408/409/429/5xx API failures.
- **Conservative free-tier workflow limits** by default.
- **Real pytest execution** with a configurable timeout.
- **Hard failure when the Developer produces no files**, instead of silently
  marching into later stages with an empty project.
- **Final run status** (`passed` or `tests_failed`) in `run_log.json`.
- **Current code context is explicitly supplied** when the Developer is asked
  to revise code, reducing the chance of incomplete rewrites.

## Important free-tier note

A multi-agent team can consume tokens quickly. Groq's current free limits are
per model and can change. If you repeatedly hit 429/rate-limit errors, first
reduce review/security/test iterations or disable research for small tasks.

Current official references:

- https://console.groq.com/docs/models
- https://console.groq.com/docs/rate-limits
- https://console.groq.com/docs/model-permissions

## Project layout

```text
ai-dev-team/
├── agents/
│   ├── base_agent.py
│   └── roles.py
├── workspace/
├── .devcontainer/
├── .env.example
├── file_utils.py
├── llm_client.py
├── orchestrator.py
├── web_search.py
└── requirements.txt
```

The system deliberately avoids a large agent framework. `orchestrator.py` is
still the workflow manager, so it remains easy to inspect and modify.

## Quick `team` command

Install the launcher once:

```bash
./install_team.sh
export PATH="$HOME/.local/bin:$PATH"
```

Then run the team from anywhere in the Codespace:

```bash
team "Build a simple test project that prints Hello World and includes pytest tests"
```

To make the PATH change permanent, add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc`.
