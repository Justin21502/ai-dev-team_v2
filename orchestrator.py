"""Manager for the AI Dev Team.

Workflow:
  Researcher -> Architect -> Developer -> Review -> Security -> Tester
             -> real pytest -> Developer/Debugger fixes

The team is deliberately simple and transparent so it works well in a
GitHub Codespace without a framework or paid orchestration service.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from agents import (
    make_architect,
    make_debugger,
    make_developer,
    make_researcher,
    make_reviewer,
    make_security,
    make_tester,
)
from file_utils import extract_files, read_files_as_text, write_files
from llm_client import FAST_MODEL, PRIMARY_MODEL
from web_search import search_many

MAX_REVIEW_ITERATIONS = int(os.environ.get("MAX_REVIEW_ITERATIONS", "2"))
MAX_SECURITY_ITERATIONS = int(os.environ.get("MAX_SECURITY_ITERATIONS", "1"))
MAX_TEST_ITERATIONS = int(os.environ.get("MAX_TEST_ITERATIONS", "3"))
ENABLE_RESEARCH = os.environ.get("ENABLE_RESEARCH", "true").lower() != "false"

# Stronger model for planning/coding/debugging; faster model for judging and
# research. These can all be overridden independently in .env.
MODEL_RESEARCHER = os.environ.get("AI_TEAM_RESEARCHER_MODEL", FAST_MODEL)
MODEL_ARCHITECT = os.environ.get("AI_TEAM_ARCHITECT_MODEL", PRIMARY_MODEL)
MODEL_DEVELOPER = os.environ.get("AI_TEAM_DEVELOPER_MODEL", PRIMARY_MODEL)
MODEL_REVIEWER = os.environ.get("AI_TEAM_REVIEWER_MODEL", FAST_MODEL)
MODEL_SECURITY = os.environ.get("AI_TEAM_SECURITY_MODEL", FAST_MODEL)
MODEL_TESTER = os.environ.get("AI_TEAM_TESTER_MODEL", FAST_MODEL)
MODEL_DEBUGGER = os.environ.get("AI_TEAM_DEBUGGER_MODEL", PRIMARY_MODEL)


def log(msg: str):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def _safe_context(paths: list[str], workspace_dir: str) -> str:
    """Read generated files, returning a useful message when none exist."""
    if not paths:
        return "(No generated files are currently available.)"
    return read_files_as_text(paths)


def _apply_agent_files(output: str, workspace_dir: str, existing: list[str]) -> list[str]:
    files = extract_files(output)
    if not files:
        return existing
    written = write_files(files, workspace_dir)
    return list(dict.fromkeys(existing + written))


def run_team(task: str, workspace_dir: str = "workspace") -> dict:
    workspace = Path(workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    run_log = {
        "task": task,
        "models": {
            "researcher": MODEL_RESEARCHER,
            "architect": MODEL_ARCHITECT,
            "developer": MODEL_DEVELOPER,
            "reviewer": MODEL_REVIEWER,
            "security": MODEL_SECURITY,
            "tester": MODEL_TESTER,
            "debugger": MODEL_DEBUGGER,
        },
        "steps": [],
    }

    researcher = make_researcher(MODEL_RESEARCHER)
    architect = make_architect(MODEL_ARCHITECT)
    developer = make_developer(MODEL_DEVELOPER)
    reviewer = make_reviewer(MODEL_REVIEWER)
    security = make_security(MODEL_SECURITY)
    tester = make_tester(MODEL_TESTER)
    debugger = make_debugger(MODEL_DEBUGGER)

    # 0. Research. Web-search failure is non-fatal.
    research_notes = ""
    if ENABLE_RESEARCH:
        log("Researcher is searching the web...")
        raw_results = search_many([task, f"{task} best practices"], max_results_each=3)
        research_notes = researcher.say(
            f"Task:\n{task}\n\nRaw web search results:\n{raw_results}\n\n"
            "Summarize only useful, supported information for the Architect and Developer."
        )
        run_log["steps"].append({"agent": "Researcher", "output": research_notes})
        log("Research notes ready.")

    # 1. Architect.
    log("Architect is planning...")
    plan = architect.say(
        f"Task:\n{task}\n\n"
        + (f"Research notes:\n{research_notes}\n\n" if research_notes else "")
        + "Produce a short implementation plan."
    )
    run_log["steps"].append({"agent": "Architect", "output": plan})
    log("Plan ready.")

    # 2. Developer first pass.
    log("Developer is writing the first draft...")
    dev_output = developer.say(
        f"Task:\n{task}\n\nArchitect's plan:\n{plan}\n\n"
        "Write the code now, following the FILE format exactly."
    )
    written_paths = _apply_agent_files(dev_output, workspace_dir, [])
    run_log["steps"].append({"agent": "Developer", "output": dev_output, "files": written_paths})
    if not written_paths:
        raise RuntimeError("Developer response contained no parseable FILE blocks; cannot continue safely.")

    # 3. Code review loop.
    for i in range(1, MAX_REVIEW_ITERATIONS + 1):
        log(f"Reviewer round {i}...")
        review = reviewer.say(f"Task:\n{task}\n\nReview this code:\n\n{_safe_context(written_paths, workspace_dir)}")
        run_log["steps"].append({"agent": "Reviewer", "round": i, "output": review})
        if review.strip().upper().startswith("APPROVED"):
            log("Reviewer approved the code.")
            break

        log("Reviewer requested changes. Sending back to Developer...")
        dev_output = developer.say(
            f"Task:\n{task}\n\nCurrent code:\n{_safe_context(written_paths, workspace_dir)}\n\n"
            f"Reviewer feedback:\n{review}\n\n"
            "Revise the code. Re-output the COMPLETE contents of every file that needs a change."
        )
        written_paths = _apply_agent_files(dev_output, workspace_dir, written_paths)
        run_log["steps"].append({"agent": "Developer", "round": i, "output": dev_output, "files": written_paths})

    # 4. Security review loop.
    for i in range(1, MAX_SECURITY_ITERATIONS + 1):
        log(f"Security review round {i}...")
        sec_review = security.say(
            f"Task:\n{task}\n\nReview this code for security issues:\n\n{_safe_context(written_paths, workspace_dir)}"
        )
        run_log["steps"].append({"agent": "Security", "round": i, "output": sec_review})
        if sec_review.strip().upper().startswith("APPROVED"):
            log("Security review approved the code.")
            break

        log("Security review found issues. Sending back to Developer...")
        dev_output = developer.say(
            f"Task:\n{task}\n\nCurrent code:\n{_safe_context(written_paths, workspace_dir)}\n\n"
            f"Security feedback:\n{sec_review}\n\n"
            "Fix the issues and re-output the COMPLETE contents of every file that needs a change."
        )
        written_paths = _apply_agent_files(dev_output, workspace_dir, written_paths)
        run_log["steps"].append({"agent": "Developer", "round": i, "output": dev_output, "files": written_paths})

    # 5. Tester writes tests.
    log("Tester is writing tests...")
    test_output = tester.say(
        f"Task:\n{task}\n\nCode to test:\n\n{_safe_context(written_paths, workspace_dir)}"
    )
    test_paths = write_files(extract_files(test_output), workspace_dir)
    run_log["steps"].append({"agent": "Tester", "output": test_output, "files": test_paths})

    # 6. Run tests for real and repair failures.
    final_test_result = None
    for i in range(1, MAX_TEST_ITERATIONS + 1):
        log(f"Running pytest (attempt {i})...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=int(os.environ.get("PYTEST_TIMEOUT_SECONDS", "120")),
        )
        passed = result.returncode == 0
        final_test_result = result
        run_log["steps"].append({
            "agent": "Orchestrator",
            "action": "pytest",
            "attempt": i,
            "passed": passed,
            "stdout": result.stdout[-6000:],
            "stderr": result.stderr[-3000:],
        })
        if passed:
            log("All tests passed.")
            break

        fixer, fixer_name = (developer, "Developer") if i == 1 else (debugger, "Debugger")
        log(f"Tests failed. Sending failure output to {fixer_name}...")
        fix_output = fixer.say(
            f"Task:\n{task}\n\nCurrent application code:\n{_safe_context(written_paths, workspace_dir)}\n\n"
            f"pytest output:\n{result.stdout}\n{result.stderr}\n\n"
            "Fix the application code (not the tests) so the tests pass. "
            "Re-output the COMPLETE contents of every application file you change."
        )
        written_paths = _apply_agent_files(fix_output, workspace_dir, written_paths)
        run_log["steps"].append({"agent": fixer_name, "round": i, "output": fix_output, "files": written_paths})
    else:
        log("Max test iterations reached; tests still failing.")

    run_log["status"] = "passed" if final_test_result and final_test_result.returncode == 0 else "tests_failed"
    (workspace / "run_log.json").write_text(json.dumps(run_log, indent=2))
    return run_log


if __name__ == "__main__":
    task_description = " ".join(sys.argv[1:]) or input("Describe what you want the team to build: ")
    run_team(task_description)
    log("Done. See workspace/ for the code and workspace/run_log.json for the full transcript.")
