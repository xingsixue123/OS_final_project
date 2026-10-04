"""Redact private, non-project details from committed text files (leak-check listings, CPU audits, notes).

Paths outside the project (other projects, home caches/config, /tmp, system dirs) and the names of foreign
processes are replaced by category labels; consecutive identical redacted lines collapse into one "xN" line.
Research content (results, numbers, project paths) is untouched.

  python3 tools/privacy_scrub.py --check            # list offending files (exit 1 if any)
  python3 tools/privacy_scrub.py --apply            # rewrite them in place
"""
import argparse
import re
import subprocess
import sys

PROJECT = "/home/sxing/project/OS_final_project"
PATH_RE = re.compile(r"(?<![\w.])((?:/home|/tmp|/var|/dev/shm|/run|/etc)/[^\s\"'`,)\]|>]*)")
TILDE_RE = re.compile(r"(?<![\w.])(~/[^\s\"'`,)\]|>]*)")
# Free-text mentions that identify unrelated private work or machine state.
NAME_SUBS = [
    (re.compile(r"(?:~/)?(?:project/)?server_fix(?:/[\w./-]*)?"), "<another project>"),
    (re.compile(r"\bmatch_background(?:\.py)?\b"), "<foreign process>"),
    (re.compile(r"\b(?:faculty\.csv|scholar_A_profile\.json|fetch_scholar\.py)\b"), "<another project file>"),
    (re.compile(r"krb5cc_[\w]+"), "<kerberos cache>"),
    (re.compile(r"models--[\w.-]+--[\w.-]+"), "<model cache>"),
]
SENSITIVE = re.compile(r"~/\.|~/snap|server_fix|match_background|krb5cc_|models--|/\.cache/huggingface|/\.config/(?:dconf|pulse)|/snap/|"
                       r"/\.copilot|/\.cache/copilot|faculty\.csv|scholar_A|fetch_scholar|/\.wget-hsts|aau_token_host")
SKIP_PREFIXES = ("lit_review/", "documents/", "tools/privacy_scrub.py")


TECHNICAL = ("/tmp/cache-sim-accesses",)  # artifact behaviour documented in the reports, not private


def category(p):
    if p == "/home/sxing" or p.startswith(PROJECT) or p.startswith(TECHNICAL) or p in ("/tmp/", "/dev/shm"):
        return None  # project path: keep
    if p.startswith("/home/sxing/project/"):
        return "<another project>"
    if p.startswith("/home/sxing/.cache/"):
        return "<home cache>"
    if p.startswith("/home/sxing/.config/") or p.startswith("/home/sxing/snap/") or p.startswith("/home/sxing/.local/"):
        return "<home desktop/config>"
    if p.startswith("/home/sxing/.claude") or p.startswith("/home/sxing/.vscode") or p.startswith("/home/sxing/.copilot") \
            or p.startswith("/home/sxing/.codex"):
        return "<editor/agent state>"
    if p.startswith("/home/sxing/miniconda3"):
        return "<other conda env>"
    if p.startswith("/home/sxing/"):
        return "<home file>"
    if p.startswith("/tmp/") or p.startswith("/var/tmp") or p.startswith("/dev/shm"):
        return "<tmp file>"
    return "<system file>"


LABELS = {"<another project>", "<home cache>", "<home desktop/config>", "<editor/agent state>", "<other conda env>",
          "<home file>", "<tmp file>", "<system file>", "<another project file>", "<foreign process>"}


def scrub_text(text):
    out, prev, count = [], None, 0

    def flush():
        if prev is not None:
            out.append(prev if count == 1 else f"{prev}  x{count}")

    for line in text.split("\n"):
        new = PATH_RE.sub(lambda m: category(m.group(1)) or m.group(1), line)
        new = TILDE_RE.sub(lambda m: category("/home/sxing/" + m.group(1)[2:]) or m.group(1), new)
        for rx, rep in NAME_SUBS:
            new = rx.sub(rep, new)
        stripped = new.strip()
        is_label_only = stripped in LABELS
        if is_label_only and new != line:
            if stripped == prev:
                count += 1
                continue
            flush()
            prev, count = stripped, 1
            continue
        flush()
        prev, count = None, 0
        out.append(new)
    flush()
    return "\n".join(out)


def tracked_files():
    files = subprocess.check_output(["git", "ls-files"], text=True, cwd=PROJECT).splitlines()
    # Only records and docs: never rewrite code (paths like /tmp are functional there) or package lock files.
    return [f for f in files if not f.startswith(SKIP_PREFIXES)
            and f.endswith((".md", ".txt", ".log")) and not f.endswith("env.lock.txt")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    hits = []
    for f in tracked_files():
        try:
            txt = open(f"{PROJECT}/{f}", encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        # A file needs scrubbing iff the scrub would change it (project paths, functional /tmp in docs and
        # system daemons such as /snap/snapd are left alone).
        if scrub_text(txt) != txt:
            hits.append(f)
            if a.apply:
                open(f"{PROJECT}/{f}", "w", encoding="utf-8").write(scrub_text(txt))
    for f in hits:
        print(f)
    if a.check and hits:
        sys.exit(1)


if __name__ == "__main__":
    main()
