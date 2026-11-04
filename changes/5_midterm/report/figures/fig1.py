"""Figure 1: PeakBaleen design (same drawing style as the proposal's fig1)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

BLUE, RED, DARK, GREY = "#2f5d8a", "#b4462f", "#333333", "#8a8a8a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})

fig, ax = plt.subplots(figsize=(6.5, 2.95), dpi=300)
ax.set_xlim(0, 102); ax.set_ylim(0, 46); ax.axis("off")


def box(x, y, w, h, text, kind="kept", tag=None):
    fc, ec, lw, tc, weight = {"kept": ("white", DARK, 1.0, DARK, "normal"),
                              "new": ("#eef3f9", BLUE, 1.6, BLUE, "bold"),
                              "core": ("#fdeeea", RED, 1.6, RED, "bold")}[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.1", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=6.7, weight=weight, color=tc, linespacing=1.45)
    if tag:
        ax.add_patch(Circle((x + w - 0.3, y + h + 0.1), 1.45, fc=ec, ec="white", lw=0.8, zorder=5))
        ax.text(x + w - 0.3, y + h + 0.05, tag, ha="center", va="center", fontsize=6.4, weight="bold", color="white", zorder=6)


def arrow(x1, y1, x2, y2, color=DARK, lw=1.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8, lw=lw, color=color,
                                 shrinkA=2, shrinkB=2))


W, GAP, H = 16.6, 4.0, 10.5
xs = [i * (W + GAP) + 0.4 for i in range(5)]
Y1, Y2 = 28.0, 8.5

ax.text(xs[0], Y1 + H + 3.0, "OFFLINE  (on the training day)", fontsize=7.4, weight="bold", color=DARK)
top = [("Day-1 trace", "kept", None), ("Episodes\nBaleen's model", "kept", None),
       ("Min–max energy\nover all windows", "core", "1"), ("Ising solver\nparallel tempering", "core", "1"),
       ("Train GBM\non labels + load", "new", "2")]
for i, (t, k, tag) in enumerate(top):
    box(xs[i], Y1, W, H, t, k, tag)
    if i:
        arrow(xs[i - 1] + W, Y1 + H / 2, xs[i], Y1 + H / 2)

ax.text(xs[0], Y2 + H + 3.0, "ONLINE  (every request)", fontsize=7.4, weight="bold", color=DARK)
bottom = [("Request\nat time t", "kept", None), ("Load meter\npast 10 min only", "new", "2"),
          ("Adaptive bar\nlower when busy", "new", "3"), ("Admit?\nscore > θ → flash", "kept", None),
          ("GBM score", "kept", None)]
for i, (t, k, tag) in enumerate(bottom):
    box(xs[i], Y2, W, H, t, k, tag)
for i in range(3):
    arrow(xs[i] + W, Y2 + H / 2, xs[i + 1], Y2 + H / 2)
arrow(xs[4], Y2 + H / 2, xs[3] + W, Y2 + H / 2)
arrow(xs[4] + W / 2, Y1 - 0.2, xs[4] + W / 2, Y2 + H + 0.2, color=BLUE, lw=1.3)
ax.text(xs[4] + W / 2 - 1.2, (Y1 + Y2 + H) / 2 + 0.9, "trained model", fontsize=6.8, color=BLUE, style="italic", ha="right", va="center")

ax.text(0.4, 2.0, "1  new labels      2  load feature      3  adaptive bar      white boxes: unchanged from Baleen",
        fontsize=6.9, color=DARK)
fig.tight_layout(pad=0.2)
fig.savefig("fig1_design.png", dpi=300, bbox_inches="tight", facecolor="white")
print("ok")
