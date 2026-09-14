"""Hard sandbox for agent processes.

Adapted from auto_hw_complete/framework/sandbox.py. `claude -p` runs inside bubblewrap,
so the only writable paths are the ones bound explicitly; the rest of the machine is a
read-only filesystem at the kernel level. That is what makes
--dangerously-skip-permissions safe here.

Two differences from the original:

  * the prompt goes in on stdin, never argv -- a prompt in argv is visible to
    `pkill -f` and has made a harness kill its own agent before;
  * every role gets an explicit tool list, and "no shell" roles get it at the kernel.

Why the kernel: measured 2026-09-13 with Claude Code 2.1.104, `--tools Read,...` (and
the init tool list confirming only those) did NOT stop an auditor from calling the
deferred `Monitor` tool, which ran `find` over $HOME and returned the output. So for
`no_shell` agents every shell binary is overlaid with /dev/null: sh, bash, dash, zsh and
busybox all fail with EACCES, which also breaks subprocess(shell=True), `env bash` and
node's execSync. Tool lists and --disallowedTools stay as the first layer, and the
driver audits each transcript for a non-allowed tool that ran (see lr.tool_violations).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

HOME = Path.home()
REAL_CREDENTIALS = HOME / ".claude" / ".credentials.json"

SHELLS = ["/usr/bin/sh", "/usr/bin/bash", "/usr/bin/rbash", "/usr/bin/dash", "/usr/bin/zsh",
          "/usr/bin/busybox", "/usr/bin/ksh", "/usr/bin/mksh", "/usr/bin/csh", "/usr/bin/tcsh",
          "/usr/bin/fish", "/usr/bin/ash"]

# Tools no role gets: they spawn other agents or processes, or reach outside the run.
ALWAYS_DENIED = ["Agent", "Task", "Workflow", "Skill", "CronCreate", "CronDelete", "CronList",
                 "RemoteTrigger", "ScheduleWakeup", "SendMessage", "PushNotification",
                 "EnterWorktree", "ExitWorktree", "NotebookEdit", "PowerShell"]
SHELL_TOOLS = ["Bash", "Monitor", "TaskOutput", "TaskStop", "KillShell", "BashOutput"]


def make_config_dir(base: Path) -> Path:
    """A private CLAUDE_CONFIG_DIR so agents never touch the real ~/.claude.

    `.credentials.json` is a symlink to the real file, which the sandbox sees read-only
    (it is under the ro-bound /), so no copy of the token is ever written. Not a bind
    mount of the file: an OAuth refresh atomically *replaces* the real file, and a file
    bind mount keeps pointing at the old inode -- measured 2026-09-13, every agent that
    was running across a refresh died with 401 "OAuth access token has been revoked".
    """
    cfg = Path(base) / "cfg"
    cfg.mkdir(parents=True, exist_ok=True)
    link = cfg / ".credentials.json"
    if link.is_symlink() and os.readlink(link) == str(REAL_CREDENTIALS):
        return cfg
    link.unlink(missing_ok=True)
    link.symlink_to(REAL_CREDENTIALS)
    return cfg


def bwrap_prefix(rw_paths, ro_paths, cfg_dir: Path, chdir: Path, no_shell: bool) -> list[str]:
    """rw_paths become writable; everything else is read-only. ro_paths are re-bound
    after the private /tmp so a workspace that lives under /tmp stays visible."""
    bw = shutil.which("bwrap")
    if not bw:
        raise RuntimeError("bubblewrap (bwrap) not found; the sandbox cannot be enforced")
    argv = [bw, "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
    for p in ro_paths:
        p = Path(p).resolve()
        argv += ["--ro-bind", str(p), str(p)]
    if no_shell:
        for sh in SHELLS:
            if os.path.lexists(sh):
                argv += ["--ro-bind", "/dev/null", sh]
    for p in rw_paths:
        p = Path(p).resolve()
        p.mkdir(parents=True, exist_ok=True)
        argv += ["--bind", str(p), str(p)]
    cfg_dir = Path(cfg_dir).resolve()
    argv += ["--bind", str(cfg_dir), str(cfg_dir)]
    argv += [
        "--setenv", "CLAUDE_CONFIG_DIR", str(cfg_dir),
        "--setenv", "HOME", str(HOME),
        "--setenv", "PATH", os.environ.get("PATH", "/usr/bin:/bin"),
        "--setenv", "SHELL", "/nonexistent" if no_shell else os.environ.get("SHELL", "/bin/bash"),
        "--chdir", str(Path(chdir).resolve()),
        "--die-with-parent",
        "--unshare-pid",
    ]
    return argv


def token_hours_left() -> float | None:
    try:
        exp = json.loads(REAL_CREDENTIALS.read_text())["claudeAiOauth"]["expiresAt"] / 1000
    except (OSError, KeyError, ValueError, TypeError):
        return None
    import time
    return (exp - time.time()) / 3600


def refresh_token_if_needed(min_hours: float = 1.0) -> str:
    """Sandboxed agents can read the OAuth token but never write it, so they cannot
    refresh it; left alone it expires (~8 h lifetime) and every agent fails with 401.
    When it is close to expiry, run one tiny *unsandboxed* claude call -- the CLI
    refreshes and rewrites the credentials file as a normal session would."""
    left = token_hours_left()
    if left is None or left > min_hours:
        return f"token ok ({left:.1f} h left)" if left is not None else "no OAuth token file"
    r = subprocess.run(["claude", "-p", "--model", "haiku", "--tools", "", "--output-format", "json"],
                       input="Reply with: ok", capture_output=True, text=True, timeout=300)
    after = token_hours_left()
    return f"token had {left:.2f} h left; refresh call rc={r.returncode}; now {after if after is None else round(after, 2)} h left"


def new_session_id() -> str:
    return str(uuid.uuid4())


def transcript_path(cfg_dir: Path, session_id: str) -> Path | None:
    hits = list((Path(cfg_dir) / "projects").glob(f"*/{session_id}.jsonl"))
    return hits[0] if hits else None


def run_agent(*, prompt: str, system_prompt: str, tools: list[str], rw_paths, ro_paths,
              cfg_dir: Path, chdir: Path, model: str, effort: str, log_path: Path,
              session_id: str, resume: bool = False, timeout: int = 3600):
    """Spawn one sandboxed agent and block until it finishes.

    An agent whose tools do not include Bash runs with no shell binaries at all.
    Returns (returncode, result_text, parsed_json_or_None). returncode 124 = timeout.
    """
    chdir = Path(chdir)
    chdir.mkdir(parents=True, exist_ok=True)
    sysfile = Path(cfg_dir) / "system_prompt.md"
    sysfile.write_text(system_prompt)
    no_shell = "Bash" not in tools
    denied = ALWAYS_DENIED + (SHELL_TOOLS if no_shell else [])

    argv = bwrap_prefix(rw_paths, ro_paths, cfg_dir, chdir, no_shell) + [
        "claude", "-p",
        "--model", model,
        "--settings", json.dumps({"effortLevel": effort}),
        "--append-system-prompt-file", str(sysfile),
        "--tools", ",".join(tools),
        "--disallowedTools", ",".join(denied),
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]
    argv += ["--resume", session_id] if resume else ["--session-id", session_id]

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(input=prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        log_path.write_text(f"TIMEOUT after {timeout}s\n")
        return 124, f"agent timed out after {timeout}s", None

    log_path.write_text(out + ("\n--- stderr ---\n" + err if err else ""))
    try:
        data = json.loads(out)
        return proc.returncode, data.get("result", ""), data
    except Exception:
        return proc.returncode, out, None
