import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
BLUE, RED, DARK, GREY = "#2f5d8a", "#b4462f", "#333333", "#8a8a8a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})

fig, ax = plt.subplots(figsize=(6.5, 2.9), dpi=300)
ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis("off")

def box(x, y, w, h, text, fc="white", ec=DARK, lw=1.0, fs=7.4, weight="normal", tc=DARK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.1",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
            weight=weight, color=tc, linespacing=1.55)

def arrow(x1, y1, x2, y2, color=DARK, lw=1.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8,
                                 lw=lw, color=color, shrinkA=2, shrinkB=2))

W, GAP, Y, H = 14.0, 3.2, 31.0, 11.0
labels = ["Training\ntrace", "Episode\nmodel", "Episode\nselection\n(write budget)",
          "GBM admission\n& prefetch", "Cache\nsimulator", "Peak DT\n(P100, 10-min\nwindows)"]
xs = [i * (W + GAP) for i in range(6)]
for i, (x, t) in enumerate(zip(xs, labels)):
    if i == 2:
        box(x, Y, W, H, t, fc="#eef3f9", ec=BLUE, lw=1.6, weight="bold", tc=BLUE)
    elif i == 5:
        box(x, Y, W, H, t, fc="#eef3f9", ec=BLUE, lw=1.1, fs=7.0)
    else:
        box(x, Y, W, H, t)
    if i:
        arrow(xs[i-1] + W, Y + H/2, x, Y + H/2)

ax.text(xs[0], Y + H + 3.2, "OFFLINE  (label generation & training)", fontsize=7.4,
        weight="bold", color=DARK)
ax.text(xs[4] - 1, Y + H + 3.2, "ONLINE  (datapath unchanged)", fontsize=7.4,
        weight="bold", color=DARK)
ax.plot([xs[4] - 2.0, xs[4] - 2.0], [Y - 12, Y + H + 2.2], color="#cccccc", lw=0.9, ls=(0, (4, 4)))

box(1, 4.0, 45, 12.0,
    "Baleen (FAST'24)\ngreedy ratio sort:  score = DT saved / size\n→ optimises AVERAGE DT",
    ec=GREY, lw=1.1, fs=7.3)
box(53, 4.0, 46, 12.0,
    "PeakBaleen  (this project)\njoint min–max selection across windows,\nsolved as QUBO on an Ising machine\n→ optimises PEAK DT",
    fc="#fdeeea", ec=RED, lw=1.6, fs=7.3, weight="bold", tc=RED)
arrow(23.5, 16.0, 37.5, 30.8, color=GREY, lw=1.1)
arrow(76.0, 16.0, 45.5, 30.8, color=RED, lw=1.7)
ax.text(49.5, 24.0, "replaced by", fontsize=7.2, color=RED, style="italic", ha="center")
fig.tight_layout(pad=0.2)
fig.savefig("figures/fig1_pipeline.png", dpi=300, bbox_inches="tight", facecolor="white")
print("ok")
