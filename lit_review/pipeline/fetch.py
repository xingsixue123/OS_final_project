"""Deterministic half of steps 1-2: download the PDF, clone the repo, derive facts.

The driver tries these first; a fetch agent is spawned only for what they cannot get.
Validity checks here are also what the driver uses to verify a fetch agent's claims.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) lit-review-fetch"


# ---------------------------------------------------------------- validity

def valid_pdf(path: Path) -> tuple[bool, str]:
    path = Path(path)
    if not path.is_file() or path.stat().st_size < 10_000:
        return False, "missing or smaller than 10 KB"
    with open(path, "rb") as f:
        if b"%PDF" not in f.read(1024):
            return False, "no %PDF header (probably an HTML or login page)"
    try:
        import pymupdf
        with pymupdf.open(path) as doc:
            n = doc.page_count
    except Exception as e:  # noqa: BLE001
        return False, f"pymupdf cannot open it: {e}"
    if n < 4:
        return False, f"only {n} pages"
    return True, f"{n} pages"


def valid_repo(path: Path) -> tuple[bool, str]:
    path = Path(path)
    if not path.is_dir():
        return False, "no repo/ directory"
    entries = [p for p in path.iterdir() if p.name != ".git"]
    if not entries:
        return False, "repo/ is empty"
    return True, f"{len(entries)} top-level entries"


# ---------------------------------------------------------------- download

def _is_link(url) -> bool:
    return isinstance(url, str) and url.startswith("http")


def _pdf_candidates(entry: dict) -> list[str]:
    urls = []
    for key in ("pdf_url", "paper_url"):
        u = entry.get(key)
        if not _is_link(u):
            continue
        m = re.match(r"https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:\.pdf)?$", u)
        if m:
            urls.append(f"https://arxiv.org/pdf/{m.group(1)}")
        elif key == "pdf_url" or u.lower().endswith(".pdf"):
            urls.append(u)
    return list(dict.fromkeys(urls))


def try_pdf(entry: dict, dest: Path) -> tuple[bool, list[str]]:
    """Try the list's links. Returns (ok, log of attempts)."""
    tried = []
    for url in _pdf_candidates(entry):
        tmp = dest.with_suffix(".part")
        r = subprocess.run(["curl", "-sSL", "--fail", "-A", UA, "--max-time", "180",
                            "-o", str(tmp), url], capture_output=True, text=True)
        ok, why = valid_pdf(tmp) if r.returncode == 0 else (False, r.stderr.strip()[:200])
        tried.append(f"PDF {url}: {'ok' if ok else 'failed'} ({why})")
        if ok:
            tmp.replace(dest)
            return True, tried
        tmp.unlink(missing_ok=True)
    if not tried:
        tried.append("PDF: the list has no direct PDF or arXiv link")
    return False, tried


def normalize_repo_url(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?(github\.com|gitlab\.com|bitbucket\.org)/([^/\s]+)/([^/\s#?]+)", url)
    if not m:
        return url
    return f"https://{m.group(1)}/{m.group(2)}/{re.sub(r'\.git$', '', m.group(3))}.git"


def try_clone(url, dest: Path) -> tuple[bool, list[str]]:
    if not _is_link(url):
        return False, [f"repo: the list has no repo link ({url!r})"]
    git_url = normalize_repo_url(url)
    tmp = dest.with_name(dest.name + ".part")
    subprocess.run(["rm", "-rf", str(tmp)])
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1")
    try:
        r = subprocess.run(["git", "clone", "--depth", "1", "--no-tags", git_url, str(tmp)],
                           capture_output=True, text=True, env=env, timeout=900)
        err = r.stderr.strip()[-300:]
    except subprocess.TimeoutExpired:
        r, err = None, "timed out after 900 s"
    ok, why = valid_repo(tmp) if r is not None and r.returncode == 0 else (False, err)
    if ok:
        tmp.replace(dest)
    else:
        subprocess.run(["rm", "-rf", str(tmp)])
    return ok, [f"repo {git_url}: {'ok' if ok else 'failed'} ({why})"]


# ---------------------------------------------------------------- derived facts

def extract_text(pdf: Path, out: Path) -> int:
    import pymupdf
    parts = []
    with pymupdf.open(pdf) as doc:
        for i, page in enumerate(doc, 1):
            parts.append(f"\n\n===== page {i} =====\n{page.get_text()}")
        n = doc.page_count
    out.write_text("".join(parts))
    return n


def render_pages(pdf: Path, out_dir: Path, dpi: int = 150) -> int:
    """Every page as a PNG. The auditor has no shell, and Claude Code's page-wise PDF
    reading was measured to fail without one, so figures are read from these."""
    import pymupdf
    tmp = out_dir.with_name(out_dir.name + ".part")
    tmp.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(pdf) as doc:
        for i, page in enumerate(doc, 1):
            page.get_pixmap(dpi=dpi).save(tmp / f"page-{i:02d}.png")
        n = doc.page_count
    tmp.replace(out_dir)
    return n


CODE_EXT = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".py", ".rs", ".go", ".java",
            ".scala", ".cuda", ".cu", ".cuh", ".js", ".ts", ".sh", ".bash", ".pl", ".rb",
            ".ml", ".hs", ".zig", ".jl", ".m", ".swift", ".kt", ".tla", ".v", ".sv", ".proto"}
TEXT_EXT = CODE_EXT | {".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".json", ".cfg",
                       ".ini", ".cmake", ".mk", ".dockerfile", ""}
BUILD_FILES = ["CMakeLists.txt", "Makefile", "meson.build", "configure", "configure.ac",
               "setup.py", "pyproject.toml", "setup.cfg", "environment.yml", "environment.yaml",
               "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "BUILD", "WORKSPACE",
               "Dockerfile", "docker-compose.yml", "Vagrantfile"]

# Grep hints for env.md constraints. Hits are evidence to inspect, not verdicts.
RED_FLAGS = {
    "sudo": r"\bsudo\b",
    "kernel_module": r"\b(insmod|modprobe|rmmod|dkms)\b",
    "custom_kernel": r"make\s+(menuconfig|oldconfig|modules_install)|update-grub|grub-reboot|\breboot\b",
    "ebpf": r"\b(bpftrace|libbpf|bpf_prog|BPF_PROG|sched_ext|scx_)\b",
    "perf_counters": r"\bperf\s+(stat|record)\b|perf_event_open|\bPAPI\b|\blikwid\b",
    "docker": r"\b(docker|podman)\b",
    "kvm_vm": r"/dev/kvm|qemu-system|\bvirsh\b|\bfirecracker\b|cloud-hypervisor",
    "rdma_dpdk_spdk": r"\b(rdma|ibverbs|mlx5|infiniband|dpdk|spdk)\b",
    "cxl_pmem": r"\b(cxl|pmem|ndctl|daxctl|optane|numactl --membind)\b",
    "sysctl_hugepages": r"hugepages|/proc/sys/|sysctl\s+-w|drop_caches|\bcpupower\b|\bwrmsr\b",
    "big_gpu": r"\b(A100|H100|H200|B200|GH200|A6000|L40S?|V100)\b",
    "multi_gpu": r"tensor[-_ ]parallel|pipeline[-_ ]parallel|nproc_per_node|\bworld_size\b|\bNCCL\b",
    "multi_node": r"\b(hostfile|mpirun|slurm|sbatch|srun|ansible|cloudlab)\b|\bec2\b|ssh\s+\S+@",
}


def _repo_files(repo: Path) -> list[Path]:
    r = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True)
    if r.returncode == 0 and r.stdout:
        return [repo / p for p in r.stdout.decode(errors="replace").split("\0") if p]
    return [p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts]


def _github_meta(url) -> dict:
    m = re.match(r"https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", url or "")
    if not m:
        return {}
    api = f"https://api.github.com/repos/{m.group(1)}/{re.sub(r'.git$', '', m.group(2))}"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            d = json.load(resp)
        return {k: d.get(k) for k in ("stargazers_count", "forks_count", "archived",
                                      "pushed_at", "created_at", "open_issues_count")} | {
            "license": (d.get("license") or {}).get("spdx_id")}
    except Exception as e:  # noqa: BLE001 -- unauthenticated API is rate-limited; best effort
        return {"error": str(e)[:200]}


def repo_facts(repo: Path, url) -> dict:
    facts: dict = {"url": url}
    r = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%H%x09%cI"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        facts["head_commit"], facts["head_commit_date"] = r.stdout.strip().split("\t")
    files = _repo_files(repo)
    facts["file_count"] = len(files)
    facts["size_mb"] = round(sum(p.stat().st_size for p in files if p.is_file()) / 2**20, 1)
    facts["top_level"] = sorted(p.name + ("/" if p.is_dir() else "") for p in repo.iterdir()
                                if p.name != ".git")
    facts["build_files"] = sorted({str(p.relative_to(repo)) for p in files
                                   if p.name in BUILD_FILES and len(p.relative_to(repo).parts) <= 3})
    if (repo / ".gitmodules").is_file():
        facts["gitmodules"] = (repo / ".gitmodules").read_text(errors="replace")[:2000]

    loc: dict[str, int] = {}
    flags = {k: {"count": 0, "examples": []} for k in RED_FLAGS}
    pats = {k: re.compile(v, re.I if k not in ("ebpf", "big_gpu") else 0) for k, v in RED_FLAGS.items()}
    any_flag = re.compile("|".join(f"(?:{v})" for v in RED_FLAGS.values()), re.I)  # cheap pre-filter
    for p in files:
        ext = p.suffix.lower() if p.name != "Dockerfile" else ".dockerfile"
        if ext not in TEXT_EXT or not p.is_file() or p.stat().st_size > 1_000_000:
            continue
        # artifacts ship thousands of .txt/.json result and trace files; they are data, not setup
        if ext == ".txt" and not re.match(r"(?i)(requirements|readme|install|constraints|cmakelists)", p.name):
            continue
        if ext in (".json", "") and p.stat().st_size > 64_000:
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        if ext in CODE_EXT:
            loc[ext] = loc.get(ext, 0) + len(lines)
        if not any_flag.search(text):
            continue
        rel = str(p.relative_to(repo))
        for i, line in enumerate(lines, 1):
            if not any_flag.search(line):
                continue
            for k, pat in pats.items():
                if pat.search(line):
                    flags[k]["count"] += 1
                    if len(flags[k]["examples"]) < 5:
                        flags[k]["examples"].append(f"{rel}:{i}: {line.strip()[:160]}")
    facts["lines_by_extension"] = dict(sorted(loc.items(), key=lambda kv: -kv[1])[:12])
    facts["red_flags"] = {k: v for k, v in flags.items() if v["count"]}
    facts["github"] = _github_meta(url)
    return facts
