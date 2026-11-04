"""Figure 2: change in peak load vs Baleen on each pre-registered deployed test sample. Data: fig2_data.csv."""
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FULL, BAR = "#b4501a", "#1f5faf"       # validated with the dataviz palette checker (light mode)
INK, MUTED, GRID = "#333333", "#6b7588", "#e3e6ea"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})

rows = list(csv.DictReader(open("fig2_data.csv")))
gap_after = {2, 5}
xs, x = [], 0.0
for i in range(len(rows)):
    xs.append(x)
    x += 1.0 + (0.7 if i in gap_after else 0.0)

fig, ax = plt.subplots(figsize=(6.5, 2.75), dpi=300)
w = 0.36
for i, r in enumerate(rows):
    f, b = float(r["d_full"]), float(r["d_bar"])
    ax.bar(xs[i] - w / 2 - 0.015, f, w, color=FULL, label="Full PeakBaleen" if i == 0 else None, zorder=3)
    ax.bar(xs[i] + w / 2 + 0.015, b, w, color=BAR, label="Baleen + adaptive bar" if i == 0 else None, zorder=3)
    if f >= 4:
        ax.text(xs[i] - w / 2 - 0.015, f + 0.3, f"{f:+.1f}", ha="center", va="bottom", fontsize=7, color=INK)
    if b <= -4:
        ax.text(xs[i] + w / 2 + 0.015, b - 0.3, f"{b:+.1f}".replace("-", "−"), ha="center", va="top", fontsize=7, color=INK)

ax.axhline(0, color=INK, lw=0.8, zorder=4)
ax.set_xticks(xs)
ax.set_xticklabels([r["inst"].split("_")[1] for r in rows], fontsize=7, color=MUTED)
for name, a, b in (("Region6", 0, 2), ("Region7", 3, 5), ("Region5", 6, 11)):
    ax.text((xs[a] + xs[b]) / 2, -0.115, name, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7.6, color=INK, weight="bold")
ax.set_ylabel("Change in P100 vs Baleen\n(points; lower is better)", fontsize=7.4, color=INK)
ax.set_ylim(-6.5, 15)
ax.set_yticks([-5, 0, 5, 10, 15])
ax.set_yticklabels(["−5", "0", "+5", "+10", "+15"])
ax.yaxis.grid(True, color=GRID, lw=0.7, zorder=0)
ax.set_axisbelow(True)
ax.tick_params(axis="y", labelsize=7, colors=MUTED, length=0)
ax.tick_params(axis="x", length=0)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.legend(loc="upper right", frameon=False, fontsize=7.4, ncol=2, handlelength=1.0, columnspacing=1.2, labelcolor=INK)
fig.tight_layout(pad=0.3)
fig.savefig("fig2_samples.png", dpi=300, bbox_inches="tight", facecolor="white")
print("ok")
