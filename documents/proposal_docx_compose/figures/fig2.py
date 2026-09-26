import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
BLUE, RED, DARK = "#2f5d8a", "#b4462f", "#333333"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})

n = 14
greedy = np.array([33, 38, 44, 53, 42, 69, 48, 40, 51, 60, 35, 45, 41, 32], float)
m = greedy.mean()
ours = m + (greedy - m) * 0.42          # same budget, flatter profile
ours[5] -= 1.5

fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.45), dpi=300, sharey=True)
for ax, vals, title, col in ((axes[0], greedy, "Baleen: greedy ratio sort\n(average-DT optimal)", BLUE),
                             (axes[1], ours, "PeakBaleen: min–max selection\n(peak-DT optimal)", RED)):
    ax.bar(np.arange(n), vals, color=col, alpha=.85, width=.72)
    pi = int(vals.argmax()); pk = vals[pi]
    ax.bar(pi, pk, color=col, width=.72, edgecolor=DARK, lw=1.3)
    ax.axhline(pk, ls="--", lw=1.1, color=DARK)
    ax.text(0.0, pk + 1.8, "Peak DT", ha="left", fontsize=7.5, color=DARK, weight="bold")
    ax.set_title(title, fontsize=8, color=col, weight="bold", pad=6)
    ax.set_xlabel("10-minute window", fontsize=7.5)
    ax.set_xticks([]); ax.tick_params(labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, 80)
axes[1].axhline(greedy.max(), ls=":", lw=1.0, color=BLUE)
axes[1].text(n - .3, greedy.max() + 1.8, "Baleen's peak", fontsize=7.2, color=BLUE, ha="right")
axes[1].annotate("", xy=(12.4, ours.max()), xytext=(12.4, greedy.max()),
                 arrowprops=dict(arrowstyle="<->", color=DARK, lw=1.1))
axes[1].text(11.9, (ours.max() + greedy.max()) / 2, "peak\nreduction", fontsize=7.2,
             color=DARK, ha="right", va="center", weight="bold")
axes[0].set_ylabel("Backend load\n(disk-head time, %)", fontsize=7.5)
fig.suptitle("Schematic (illustrative values): spending the same flash writes for a lower maximum",
             fontsize=8.2, y=1.04)
fig.tight_layout(pad=0.3)
fig.savefig("figures/fig2_minmax.png", dpi=300, bbox_inches="tight", facecolor="white")
print("ok")
