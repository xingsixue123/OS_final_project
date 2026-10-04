"""Hold one sim slot per orphaned simulation (driver restart) until that process exits, so the 6-sim cap holds."""
import os, sys, time, fcntl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C
pids = [int(x) for x in sys.argv[1:]]
d = os.path.join(C.W, ".sim_slots.d")
held = []
for i in range(C.IDLE_SIMS):
    if len(held) >= len(pids):
        break
    f = open(os.path.join(d, f"slot_{i}"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held.append(f)
    except OSError:
        f.close()
print("holding", len(held), "slots for", pids, flush=True)
alive = list(pids)
while alive:
    time.sleep(10)
    still = [p for p in alive if os.path.exists(f"/proc/{p}")]
    for _ in range(len(alive) - len(still)):
        if held:
            f = held.pop(); fcntl.flock(f, fcntl.LOCK_UN); f.close()
    alive = still
print("all orphan sims finished", flush=True)
