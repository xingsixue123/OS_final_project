"""Deterministic, fail-closed validator for the PeakBaleen auto-research loop (contract: documents/GOOD_RESULT.md).

  python3 code/validate.py            # integrity + claim; exit 0 only if integrity OK AND a claim passes
  python3 code/validate.py --integrity-only

Writes result/deterministic_validation.json and prints a human-readable report.
"""
import csv
import glob
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # changes/3_autoresearch
REPO = os.path.dirname(os.path.dirname(ROOT))                                # OS_final_project
CH = os.path.join(REPO, "changes")
POOLS = {"T1": [f"Region2_s0.{k}" for k in range(1, 7)],
         "T2": [f"Region4_s0.{k}" for k in range(2, 7)],
         "T3": [f"Region3_s0.{k}" for k in range(1, 4)]}
RESERVE_RE = re.compile(r"Region\d_s0\.[789]\b|full_0\.[789]_0\.1")
TEXT_EXT = (".csv", ".json", ".md", ".txt", ".log", ".out", ".py", ".sh", ".jsonl")
SKIP_DIRS = ("documents", "autoscript", "code", "output")

problems, notes = [], []


def sh(cmd, cwd=REPO):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)


def check_contract():
    want = open(os.path.join(ROOT, "autoscript", "GOOD_RESULT.sha256")).read().split()[0]
    got = hashlib.sha256(open(os.path.join(ROOT, "documents", "GOOD_RESULT.md"), "rb").read()).hexdigest()
    if want != got:
        problems.append("documents/GOOD_RESULT.md was modified (sha256 mismatch)")


def check_frozen():
    r = sh("bash changes/0_reproduce/check_frozen.sh")
    if "frozen OK" not in r.stdout:
        problems.append("check_frozen.sh failed: " + (r.stdout + r.stderr)[-300:])


def check_untouched():
    marker = os.path.join(ROOT, "autoscript", ".leak_marker")
    bad = []
    for top in ("0_reproduce", "1_literature_review", "2_deployable_peak"):
        r = sh(f"find changes/{top} -newer {marker} -type f "
               r"-not -regex '.*cpython-31[23]\.pyc' -not -name .train.lock -not -path '*/.sim_slots*' "
               "-not -name TIMING_IDLE")
        bad += [x for x in r.stdout.split("\n") if x]
    for f in ("RESEARCH.md", "changes/SCOPE.md", "changes/SCOPE_v2.md"):
        if os.path.getmtime(os.path.join(REPO, f)) > os.path.getmtime(marker):
            bad.append(f)
    if bad:
        problems.append(f"{len(bad)} file(s) outside changes/3_autoresearch modified, e.g. {bad[:5]}")


def check_reserve():
    hits = []
    for dp, dns, fns in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT)
        if rel.split(os.sep)[0] in SKIP_DIRS:
            dns[:] = []
            continue
        for fn in fns:
            if RESERVE_RE.search(fn):
                hits.append(os.path.join(rel, fn))
                continue
            p = os.path.join(dp, fn)
            if fn.endswith(TEXT_EXT) and os.path.getsize(p) < 50_000_000:
                try:
                    if RESERVE_RE.search(open(p, errors="ignore").read()):
                        hits.append(os.path.join(rel, fn))
                except OSError:
                    pass
    if hits:
        problems.append(f"reserve samples 0.7-0.9 referenced in {len(hits)} file(s), e.g. {hits[:5]}")


def check_privacy():
    r = sh("python3 tools/privacy_scrub.py --check")
    if r.returncode != 0 or r.stdout.strip():
        problems.append("privacy_scrub --check not clean: " + r.stdout.strip()[:300])


def test_dirs():
    out = []
    for go in sorted(glob.glob(os.path.join(ROOT, "work", "*", "TEST_GO"))):
        d = os.path.dirname(go)
        txt = open(go).read()
        m_h = re.search(r"\b([0-9a-f]{7,40})\b", txt)
        m_p = re.search(r"POOL=(T[123])", txt)
        info = dict(dir=os.path.relpath(d, REPO), go_mtime=os.path.getmtime(go),
                    commit=m_h.group(1) if m_h else None, pool=m_p.group(1) if m_p else None)
        proto = os.path.join(d, "PROTOCOL.md")
        relp = os.path.relpath(proto, REPO)
        if not os.path.exists(proto):
            problems.append(f"{info['dir']}: TEST_GO without PROTOCOL.md")
        elif not info["commit"] or not info["pool"]:
            problems.append(f"{info['dir']}: TEST_GO must contain the protocol commit hash and POOL=T1|T2|T3")
        else:
            r = sh(f"git cat-file -e {info['commit']}:{relp}")
            if r.returncode != 0:
                problems.append(f"{info['dir']}: PROTOCOL.md not in commit {info['commit']}")
            else:
                ct = int(sh(f"git show -s --format=%ct {info['commit']}").stdout.strip() or 0)
                info["commit_time"] = ct
                if ct >= info["go_mtime"]:
                    problems.append(f"{info['dir']}: TEST_GO older than the protocol commit")
                if sh(f"git diff --quiet {info['commit']} -- {relp}").returncode != 0:
                    problems.append(f"{info['dir']}: PROTOCOL.md edited after its commit")
        out.append(info)
    pools = [t["pool"] for t in out]
    if len(out) > 2:
        problems.append(f"{len(out)} test spends (max 2)")
    if len(set(pools)) != len(pools):
        problems.append("a test pool was spent twice")
    if out and sorted(out, key=lambda t: t["go_mtime"])[0]["pool"] == "T3":
        problems.append("T3 may only be the second spend")
    return out


def mean(x):
    return sum(x) / len(x)


def var(x):
    return sum((v - mean(x)) ** 2 for v in x) / (len(x) - 1) if len(x) > 1 else 0.0


def check_claim(tests):
    path = os.path.join(ROOT, "result", "GOOD_RESULT_CLAIM.json")
    if not os.path.exists(path):
        notes.append("no claim file yet")
        return None
    c = json.load(open(path))
    res = dict(claim=c, ok=False, comparisons=[])
    td = os.path.normpath(os.path.join(REPO, c["test_dir"]))
    t = [x for x in tests if os.path.normpath(os.path.join(REPO, x["dir"])) == td]
    if not t:
        problems.append("claim test_dir is not a registered test (no TEST_GO)")
        return res
    t = t[0]
    if t.get("commit") and not c.get("protocol_commit", "").startswith(t["commit"][:7]):
        problems.append("claim protocol_commit differs from TEST_GO")
    proto = open(os.path.join(td, "PROTOCOL.md")).read()
    for k in ("ising_component", "classical_control_arm"):
        if not c.get(k):
            problems.append(f"claim lacks {k}")
    if c["arm_names"]["Y"] not in proto:
        problems.append("claimed config Y is not named in the committed PROTOCOL.md")
    insts = POOLS[t["pool"]]
    rows = list(csv.DictReader(open(os.path.join(REPO, c["trials_csv"]))))
    P = defaultdict(list)
    for r in rows:
        if str(r["matched"]).strip().lower() in ("true", "1") and r["inst"] in insts:
            P[(r["arm"], r["inst"])].append(float(r["p100"]))
        elif r["inst"] not in insts:
            problems.append(f"trials row outside the pool: {r['inst']}")
            break
    an = c["arm_names"]
    for key in ("Y", "A", "B", "A+alpha", "B+alpha", "control"):
        for i in insts:
            if len(P[(an[key], i)]) < 3:
                problems.append(f"arm {key} ({an[key]}) has < 3 matched retrains on {i}")
                return res
    m = {k: mean([mean(P[(an[k], i)]) for i in insts]) for k in an}
    best_alpha = "A+alpha" if m["A+alpha"] <= m["B+alpha"] else "B+alpha"
    n = len(insts)
    need = math.ceil(2 * n / 3)
    ok = True
    for ref in ("A", "B", best_alpha):
        d = [mean(P[(an[ref], i)]) - mean(P[(an["Y"], i)]) for i in insts]
        se = math.sqrt(sum(var(P[(an["Y"], i)]) / len(P[(an["Y"], i)]) +
                           var(P[(an[ref], i)]) / len(P[(an[ref], i)]) for i in insts)) / n
        wins = sum(x > 0 for x in d)
        cond = dict(ref=ref, wins=wins, need=need, mean=mean(d), se=se, worst=min(d),
                    win_ok=wins >= need, margin_ok=mean(d) > 2.5 * se, tail_ok=min(d) >= -2.0)
        cond["ok"] = cond["win_ok"] and cond["margin_ok"] and cond["tail_ok"]
        ok &= cond["ok"]
        res["comparisons"].append(cond)
    st = list(csv.DictReader(open(os.path.join(REPO, c["static_baselines_csv"]))))
    for meth in ("RejectX", "CoinFlip"):
        v = [float(r["p100"]) for r in st if r["method"] == meth and r["instance"] in insts]
        if len(v) < n:
            problems.append(f"static baseline {meth} missing instances")
            ok = False
            continue
        res[f"{meth}_mean"] = mean(v)
        ok &= m["Y"] < mean(v)
    res.update(means=m, best_alpha=best_alpha, ok=ok)
    return res


def main():
    integrity_only = "--integrity-only" in sys.argv
    check_contract()
    check_frozen()
    check_untouched()
    check_reserve()
    check_privacy()
    tests = test_dirs()
    claim = None if integrity_only else check_claim(tests)
    out = dict(problems=problems, notes=notes, tests=tests, claim=claim,
               integrity_ok=not problems, good_result=bool(claim and claim.get("ok")) and not problems)
    json.dump(out, open(os.path.join(ROOT, "result", "deterministic_validation.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))
    if integrity_only:
        sys.exit(0 if not problems else 1)
    sys.exit(0 if out["good_result"] else 1)


if __name__ == "__main__":
    main()
