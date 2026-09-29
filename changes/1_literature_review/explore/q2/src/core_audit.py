"""Timing-cleanliness audit: every 10 s, per-thread CPU-time deltas from /proc/*/task/*/stat; log threads that are
not part of a q2run.py timing process and used > 5% of a core in the interval while last scheduled on cores 0-7."""
import os
import sys
import time

LOG = sys.argv[1]
HZ = os.sysconf("SC_CLK_TCK")


def snap():
    d = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            for tid in os.listdir(f"/proc/{pid}/task"):
                with open(f"/proc/{pid}/task/{tid}/stat") as f:
                    s = f.read()
                fl = s[s.rfind(")") + 2:].split()
                d[(pid, tid)] = (int(fl[11]) + int(fl[12]), int(fl[36]))
        except Exception:
            pass
    return d


def cmd(pid):
    try:
        return open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
    except Exception:
        return "?"


prev = snap()
while True:
    time.sleep(10)
    cur = snap()
    ts = time.strftime("%H:%M:%S")
    out = []
    for k, (t, cpu) in cur.items():
        if k in prev and cpu <= 7:
            dt = (t - prev[k][0]) / HZ
            if dt > 0.5:
                c = cmd(k[0])
                if "q2run.py" not in c:
                    out.append(f"{ts} pid={k[0]} tid={k[1]} cpu={cpu} used={dt:.1f}s/10s {c[:200]}")
    if out:
        with open(LOG, "a") as f:
            f.write("\n".join(out) + "\n")
    prev = cur
