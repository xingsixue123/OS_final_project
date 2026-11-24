"""PeakBaleen final presentation deck, version 3 (v2 + a rewritten motivation slide), built on the ND/EMNLP slide kit (python-pptx; kept outside this repo).

Outline re-planned 2026-11-24: 13 slides plus 2 backup slides. Chart values come from result/numbers.json
(code/recompute_final.py) and result/numbers_v2.json (code/recompute_final_v2.py); every number is mapped in SOURCES_v2.md.

    SLIDE_KIT=<kit dir with ndslides.py> PYTHONDONTWRITEBYTECODE=1 <python with python-pptx 1.0.2> build_deck_v3.py PeakBaleen_Final_v3.pptx
"""
import json
import os
import sys

if not os.environ.get("SLIDE_KIT"):
    sys.exit("set SLIDE_KIT to the slide kit directory (the one with ndslides.py)")
sys.path.insert(0, os.environ["SLIDE_KIT"])
from ndslides import *  # noqa: E402,F401,F403
from pptx.chart.data import CategoryChartData  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "PeakBaleen_Final_v3.pptx"
N = json.load(open(os.path.join(HERE, "result", "numbers.json")))
V = json.load(open(os.path.join(HERE, "result", "numbers_v2.json")))
d = Deck(footer="PeakBaleen · Final presentation · Chiu, Fu, Xing · Graduate Operating Systems, Fall 2026")


# ---------------- helpers ----------------
def grid(s, x, y, widths, rows, rh=0.4, size=12, aligns=None, shade=None, head_size=10, bold_first=False):
    """Table drawn with text boxes: muted header, alternating cream rows, `shade` = {row index: fill}."""
    aligns = aligns or ["l"] * len(widths)
    W = sum(widths)
    for i, row in enumerate(rows):
        yy = y + i * rh
        if i == 0:
            box(s, x, yy + rh - 0.02, W, 0.015, fill=LINE, shape=MSO_SHAPE.RECTANGLE)
        elif shade and i in shade:
            box(s, x, yy, W, rh, fill=shade[i], radius=0.03)
        elif i % 2 == 0:
            box(s, x, yy, W, rh, fill=CREAM, radius=0.03)
        xx = x
        for j, c in enumerate(row):
            if i == 0:
                text(s, xx + 0.08, yy, widths[j] - 0.16, rh, c, size=head_size, color=MUTED, bold=True, align=aligns[j], anchor="m")
            else:
                text(s, xx + 0.08, yy, widths[j] - 0.16, rh, c, size=size, color=NAVY if (bold_first and j == 0) else INK,
                     bold=bold_first and j == 0, align=aligns[j], anchor="m")
            xx += widths[j]


def chart(s, kind, x, y, w, h, cd, colors, maxv=None, minv=0, major=None, fmt='0', legend=True, cat_size=11, labels=True,
          label_fmt="0.0"):
    gf = s.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    ch.font.name = PLEX
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(11)
        ch.legend.font.color.rgb = INK
    va = ch.value_axis
    if maxv is not None:
        va.maximum_scale = maxv
    va.minimum_scale = minv
    if major:
        va.major_unit = major
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = LINE
    va.tick_labels.font.size = Pt(10)
    va.tick_labels.font.color.rgb = MUTED
    va.tick_labels.number_format = fmt
    va.tick_labels.number_format_is_linked = False
    va.format.line.fill.background()
    ca = ch.category_axis
    ca.tick_labels.font.size = Pt(cat_size)
    ca.tick_labels.font.color.rgb = NAVY
    ca.format.line.color.rgb = GREY
    ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    pl = ch.plots[0]
    pl.gap_width = 60
    pl.overlap = -8
    for ser, col in zip(pl.series, colors):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = col
        ser.invert_if_negative = False
    if labels:
        pl.has_data_labels = True
        dl = pl.data_labels
        dl.font.size = Pt(10)
        dl.font.color.rgb = INK
        dl.number_format = label_fmt
        dl.number_format_is_linked = False
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
    return ch


def point_label(ser, i, label, color=INK, size=10):
    dl = ser.points[i].data_label
    dl.has_text_frame = True
    dl.text_frame.text = label
    r = dl.text_frame.paragraphs[0].runs[0]
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = True
    dl.position = XL_LABEL_POSITION.OUTSIDE_END


def bars(s, x, y, w, h, vals, top, peak_color=ORANGE, color=LBLUE, gap=0.25):
    """Simple bar profile inside (x, y, w, h); bar heights relative to `top`. Returns the y of the tallest bar."""
    n = len(vals)
    bw = w / (n + (n - 1) * gap)
    pk = max(vals)
    for i, v in enumerate(vals):
        bh = h * v / top
        box(s, x + i * bw * (1 + gap), y + h - bh, bw, bh, fill=peak_color if v == pk else color,
            shape=MSO_SHAPE.RECTANGLE)
    box(s, x - 0.05, y + h, w + 0.1, 0.015, fill=MUTED, shape=MSO_SHAPE.RECTANGLE)
    return y + h - h * pk / top


def hline(s, x1, x2, yy, color, dash=True, w=1.5):
    arrow(s, x1, yy, x2, yy, color=color, w=w, dash=dash, head=False)


def sign(v, unit="%"):
    t = f"{v:+.1f}{unit}".replace("-", "−")
    return f"<blue>{t}</blue>" if v < 0 else f"<or>{t}</or>"


PROFILE = [100, 130, 150, 180, 160, 200, 230, 250, 280, 320, 270, 230, 190, 210, 170, 140, 160, 120, 110, 90, 80]

# =====================================================================
# 1 · Title
# =====================================================================
s = d.title_slide(
    "Hi, we are PeakBaleen. Our project improves Baleen, the FAST 2024 paper on deciding what goes into a flash cache. "
    "Disks are bought for the busiest ten minutes of the day, but Baleen optimizes the average. We asked whether a "
    "peak-aware selection, formulated as a min-max problem and solved with an Ising solver, can lower that peak at the "
    "same flash-write budget. Today: the task, our design, and our results offline and online.")
text(s, 0.72, 1.42, 7.5, 0.3, "GRADUATE OPERATING SYSTEMS · FALL 2026 · FINAL PRESENTATION", size=12, color=BLUE, bold=True)
text(s, 0.72, 1.8, 7.45, 0.9, "PeakBaleen", size=40, color=NAVY, bold=True, spacing=1.0)
text(s, 0.72, 2.62, 7.45, 0.9, "Peak-aware flash-cache admission with min–max Ising/QUBO selection", size=19, color=INK,
     spacing=1.05)
text(s, 0.72, 3.65, 7.5, 0.3, "Ching-Hao Chiu · Jie Fu · Sixue Xing", size=14, color=NAVY, bold=True)
text(s, 0.72, 3.98, 7.5, 0.3, "University of Notre Dame · Fall 2026", size=12, color=MUTED)
text(s, 0.72, 4.5, 7.4, 0.5, "An improvement on Baleen: ML admission & prefetching for flash caches (USENIX FAST ’24)",
     size=12, color=MUTED)
box(s, 8.31, 1.4, 3.89, 3.89, fill=WHITE, line=LINE, radius=0.02)
text(s, 8.45, 1.52, 3.6, 0.3, "DISK LOAD PER 10-MINUTE WINDOW", size=9.5, color=MUTED, bold=True, align="c")
py = bars(s, 8.6, 2.15, 3.3, 2.35, PROFILE, 340)
hline(s, 8.5, 12.0, py, ORANGE)
text(s, 8.42, 4.62, 3.7, 0.5, "Disks are sized for the <or>busiest</or> 10 minutes", size=10.5, color=INK, align="c")

# =====================================================================
# 2 · Motivation
# =====================================================================
s = d.content("MOTIVATION", "Disks are sized for the peak, but Baleen optimizes the average",
              "A flash cache sits in front of the hard disks and absorbs reads. Flash wears out, so the number of flash writes "
              "is limited. How many disks you must buy is set by the busiest ten minutes of the day. Baleen, the state of the "
              "art, decides what to cache by how much disk time a block saves per byte written, no matter when that saving "
              "happens. In this sketch, the light part of each bar is what Baleen's cache takes off the disks. It is spread over "
              "the whole day, and the disks still have to carry the orange peak. A saving at a quiet hour buys no fewer disks. "
              "So our question: with the same flash writes, can we cut the peak instead?")
text(s, 0.89, 2.15, 4.35, 3.7, [
    bl("A flash cache in front of the disks absorbs reads. Flash wears out, so <B>flash writes are limited</B>.", after=16),
    bl("The number of disks is set by the <or><B>busiest 10 minutes</B></or> of the day.", after=16),
    bl("Baleen caches by <B>disk time saved per byte</B>, no matter <I>when</I> the saving happens.", after=0),
], size=17, spacing=1.15)
box(s, 5.55, 2.05, 6.9, 3.8, fill=WHITE, line=LINE, radius=0.02)
text(s, 5.75, 2.15, 6.5, 0.3, "DISK LOAD OVER ONE DAY (SCHEMATIC)", size=9.5, color=MUTED, bold=True)
NC = [40, 46, 55, 66, 80, 94, 100, 92, 74, 62, 52, 46, 42, 40, 38, 36]
SV = [16, 17, 18, 17, 18, 17, 16, 17, 18, 17, 18, 17, 16, 16, 15, 15]
LEFT = [a - b for a, b in zip(NC, SV)]
X0, Y0, PW, PH, TOP = 5.85, 2.6, 6.3, 2.7, 110
bw = PW / (len(NC) + (len(NC) - 1) * 0.3)
pk = LEFT.index(max(LEFT))
for i, (nc, lf) in enumerate(zip(NC, LEFT)):
    x = X0 + i * bw * 1.3
    box(s, x, Y0 + PH - PH * nc / TOP, bw, PH * (nc - lf) / TOP, fill=PALE, line=LBLUE, lw=0.75, shape=MSO_SHAPE.RECTANGLE)
    box(s, x, Y0 + PH - PH * lf / TOP, bw, PH * lf / TOP, fill=ORANGE if i == pk else BLUE, shape=MSO_SHAPE.RECTANGLE)
box(s, X0 - 0.05, Y0 + PH, PW + 0.1, 0.015, fill=MUTED, shape=MSO_SHAPE.RECTANGLE)
ypk = Y0 + PH - PH * LEFT[pk] / TOP
hline(s, X0 - 0.05, X0 + PW, ypk, ORANGE)
text(s, X0 + 3.3, ypk - 0.33, 3.0, 0.3, "<B>disks needed</B>: set by this peak", size=11, color=ORANGE, align="r")
q = 13
xq = X0 + q * bw * 1.3 + bw / 2
yq = Y0 + PH - PH * NC[q] / TOP
text(s, X0 + 3.55, yq - 1.0, 2.75, 0.55, [("saved at a quiet hour:", {"after": 0}), "no fewer disks"], size=10.5, color=INK,
     align="c", spacing=1.0, space_after=0)
arrow(s, xq, yq - 0.42, xq, yq - 0.02, color=INK, w=1.25)
for j, (fill, ln, lab) in enumerate([(BLUE, None, "load left on the disks"), (PALE, LBLUE, "load Baleen’s cache takes off")]):
    box(s, 5.85 + j * 2.9, 5.47, 0.28, 0.2, fill=fill, line=ln, lw=0.75, shape=MSO_SHAPE.RECTANGLE)
    text(s, 6.2 + j * 2.9, 5.4, 2.6, 0.32, lab, size=10.5, color=INK, anchor="m")
bar(s, 0.89, 6.05, 11.56, 0.55, "Our question: with the same flash writes, can we cut the peak instead of the average?")

# =====================================================================
# 3 · Task
# =====================================================================
s = d.content("THE TASK", "The task: decide what enters flash so the peak disk load is lowest",
              "The task. Requests read blocks through a flash cache in front of hard disks. A hit costs the disks nothing; a "
              "miss costs disk-head time. On every miss, the admission policy, which is what we design, decides whether to "
              "write the block into flash. Every admission spends flash writes, so all policies get the same budget, 35.6 "
              "megabytes per second. The goal is the lowest P100: the busiest ten minutes of disk load. We use Meta's "
              "production storage traces from seven clusters, which the Baleen paper calls Region1 to Region7, and replay them "
              "in Baleen's own simulator: the first day trains, the later days test. Each cluster is cut into small samples, "
              "and each sample is one test case.")
BW3, G3 = 1.95, 0.42
xs = [0.89 + i * (BW3 + G3) for i in range(3)]
for xx, (h_, b_) in zip(xs, [("Request", "a block read (GET) from the trace"), ("Flash cache", "366 GB; a hit costs the disks nothing"),
                             ("HDD on a miss", "costs disk-head time")]):
    card(s, xx, 2.4, BW3, 1.2, [(h_, {"size": 16, "bold": True, "color": NAVY, "after": 3}), b_], size=13)
for i in range(2):
    arrow(s, xs[i] + BW3 + 0.03, 3.0, xs[i + 1] - 0.03, 3.0, color=GREY, w=2)
arrow(s, xs[1] + BW3 / 2, 4.27, xs[1] + BW3 / 2, 3.64, color=BLUE, w=2.25)
box(s, 0.89, 4.3, xs[2] + BW3 - 0.89, 1.2, fill=PALE, line=BLUE, lw=1.5, radius=0.06)
text(s, 1.09, 4.42, xs[2] + BW3 - 1.29, 1.0, [("Admission policy: what we design", {"size": 16, "bold": True, "color": BLUE, "after": 3}),
                                             "On a miss: write the block into flash or not? Every admission spends flash writes."],
     size=13)
for y0, h0, lab, big, small in [
        (2.2, 1.05, "BUDGET", "35.6 MB/s", "of flash writes, the same for every policy"),
        (3.4, 1.05, "GOAL", "Lowest P100", "the busiest 10 minutes of disk load"),
        (4.6, 1.5, "DATA", "7 Meta storage clusters", "named Region1–7 as in the Baleen paper, replayed in Baleen’s simulator; day 1 "
                                                         "trains, later days test; each cluster is cut into small samples, each "
                                                         "one test case")]:
    box(s, 7.95, y0, 4.5, h0, fill=WHITE, line=LINE, radius=0.04)
    text(s, 8.15, y0 + 0.08, 4.1, h0 - 0.12, [(lab, {"size": 11, "bold": True, "color": BLUE, "after": 1}),
                                             (big, {"size": 19, "bold": True, "color": NAVY, "after": 1}),
                                             (small, {"size": 12, "color": INK})], spacing=1.05)

# =====================================================================
# 4 · Baselines
# =====================================================================
s = d.content("BASELINES WE RAN", "Baleen is the baseline to beat, and it still leaves room",
              "These are the baselines we ran ourselves, all at the same write budget; lower is better. The first row is the "
              "paper's own average. CoinFlip admits at random, RejectX rejects first-time items, and Baleen is the machine-"
              "learned policy: it is the baseline to beat. The last column is Baleen's OPT. It looks back at the whole trace, as if "
              "it knew the future, ranks the data by how much disk time each byte of flash writes saves, and caches the best "
              "until the write budget runs out. Baleen's model is trained to imitate OPT. Online, Baleen sits 14 to 25 percent "
              "above OPT on our test sets. That gap is the room we target.")
rows = [["Trace", "Year", "Samples", "CoinFlip", "RejectX", "Baleen", "Baleen’s OPT"],
        ["Paper, Fig. 9", "2019–23", "avg of 7", "34.63", "31.95", "28.11", "—"],
        ["Region7", "2023", "s0", "48.96", "42.46", "40.10", "34.52"],
        ["Region6", "2023", "s0", "43.45", "42.32", "43.25", "35.56"],
        ["Region6 + 7", "2023", "s0.4–0.6", "48.64", "40.73", "39.27", "33.62"],
        ["Region5", "2023", "s0.1–0.6", "44.47", "39.35", "36.17", "30.10"],
        ["Region4", "2021", "s0.2–0.6", "68.84", "65.84", "50.72", "38.13"],
        ["Region1", "2019", "s0.1–0.6", "50.39", "28.20", "24.14", "not run"]]
grid(s, 0.89, 2.1, [1.45, 1.0, 1.0, 0.95, 0.95, 0.9, 1.3], rows, rh=0.5, size=13.5,
     aligns=["l", "l", "l", "r", "r", "r", "r"], shade={1: PALE}, bold_first=True)
text(s, 8.95, 2.3, 3.5, 3.8, [
    bl("<B>Baleen’s OPT</B> (last column): looking back at the whole trace, it caches the data that saves the most disk "
       "time per byte written, until the write budget runs out", after=16),
    bl("Baleen’s model learns to imitate OPT; online it is <or><B>14–25%</B></or> above OPT on our test sets", after=16),
    bl("That gap is the room we target", after=0),
], size=15.5, spacing=1.12)

# =====================================================================
# 5 · Key idea
# =====================================================================
s = d.content("KEY IDEA", "Spend the same flash writes on the busiest window instead of the average",
              "Here is the idea on a toy example. On the left, Baleen ranks by saving per byte, which is optimal for the "
              "average; the tallest window is left where it is. On the right, the same flash writes are spent so that the "
              "maximum over all windows is as low as possible. Formally: each episode, one stay of a block in the cache, is a "
              "binary decision. Each window has a no-cache load C, and admitting an episode removes its saving d from the "
              "windows it touches. We minimize the largest remaining window load under the write budget B. As an Ising "
              "energy, we use a smooth maximum over all windows plus a quadratic penalty on the budget, and solve it with "
              "parallel tempering, 16 replicas, started from an LP solution. Earlier attempts targeted one fixed peak window; "
              "ours covers every window.")
G = [33, 38, 44, 53, 42, 69, 48, 40, 51, 60, 35, 45, 41, 32]
m = sum(G) / len(G)
O = [m + (g - m) * 0.42 for g in G]
O[5] -= 1.5
for x0, vals, ttl, sub, col in ((0.89, G, "Baleen: rank by saving per byte", "average-optimal", BLUE),
                                (4.49, O, "PeakBaleen: min–max over all windows", "peak-optimal", ORANGE)):
    box(s, x0, 2.05, 3.45, 3.6, fill=WHITE, line=LINE, radius=0.03)
    text(s, x0 + 0.15, 2.13, 3.2, 0.55, [(ttl, {"size": 12, "bold": True, "color": col, "after": 0}),
                                         (sub, {"size": 10.5, "color": MUTED})], size=12)
    pk = bars(s, x0 + 0.25, 2.95, 2.95, 2.4, vals, 80, peak_color=col,
              color=LBLUE if col == BLUE else RGBColor(0xE7, 0xB4, 0x8F))
    hline(s, x0 + 0.15, x0 + 3.3, pk, NAVY)
    text(s, x0 + 0.15, pk - 0.3, 1.5, 0.28, "<B>peak</B>", size=10, color=NAVY)
pkG = 2.95 + 2.4 - 2.4 * max(G) / 80
hline(s, 4.64, 7.79, pkG, BLUE, w=1.25)
text(s, 5.9, pkG - 0.3, 1.85, 0.28, "Baleen’s peak", size=10, color=BLUE, align="r")
pkO = 2.95 + 2.4 - 2.4 * max(O) / 80
arrow(s, 7.6, pkG + 0.03, 7.6, pkO - 0.03, color=NAVY, w=1.5, both=True)
text(s, 0.89, 5.75, 7.0, 0.3, "Schematic, illustrative values: the same flash writes, a lower maximum", size=10, color=MUTED)
card(s, 8.2, 2.05, 4.25, 4.45, [
    head("AS AN OPTIMIZATION PROBLEM"),
    ("<I>x</I>_{e} ∈ {0, 1}: admit episode <I>e</I> (one stay of a block in cache)", {"after": 5}),
    ("Load left in window <I>w</I>:  <I>L</I>_{w}(<I>x</I>) = <I>C</I>_{w} − Σ_{e} <I>d</I>_{e,w} <I>x</I>_{e}", {"after": 5}),
    ("<B>minimize</B> max_{w} <I>L</I>_{w}(<I>x</I>)  subject to  Σ_{e} <I>s</I>_{e} <I>x</I>_{e} ≤ <I>B</I>", {"after": 12}),
    head("AS AN ISING / QUBO ENERGY", col=ORANGE),
    ("<I>E</I>(<I>x</I>) = LSE_{γ}(<I>L</I>(<I>x</I>)) + <I>P</I> (Σ_{e} <I>s</I>_{e} <I>x</I>_{e} − <I>B</I>)^{2}", {"after": 5}),
    ("Smooth max over all windows + quadratic write-budget penalty; solved by <B>parallel tempering</B> (16 replicas) "
     "from an LP start", {"after": 8}),
    ("<muted>Earlier attempts targeted one fixed peak window; this covers every window</muted>", {"size": 11}),
], size=12.5)

# =====================================================================
# 6 · Design
# =====================================================================
s = d.content("OUR METHOD · DESIGN", "PeakBaleen adds an Ising-trained peak model next to Baleen’s own model",
              "PeakBaleen keeps Baleen and adds three things, numbered on the diagram. One, offline on the training day: the "
              "min-max problem, solved by the Ising solver, picks the data that keeps the busiest window lowest. Two: those "
              "Ising labels train a second model, the peak model, which also sees how busy the disks were in the last 10, 30 "
              "and 60 minutes. Three, online: a request enters flash if either Baleen's model or the peak model clears its "
              "bar, and the bar drops when the disks are busy. Its base value is tuned so the total flash writes stay at the "
              "same budget. Baleen's model keeps everything Baleen already caches well; the peak model adds what matters at "
              "the peak. No solver runs at request time.")
BW, GAPX = 1.95, 0.45
X5 = [0.89 + i * (BW + GAPX) for i in range(5)]
KEPT, CORE, NEW = (WHITE, GREY), (PALEOR, ORANGE), (PALE, BLUE)


def dbox(x, y, title, sub, kind, num=None, h=0.92, tsize=13):
    fill, ln = kind
    box(s, x, y, BW, h, fill=fill, line=ln, lw=1.5 if kind != KEPT else 1.0, radius=0.08)
    tc = ORANGE if kind == CORE else (BLUE if kind == NEW else NAVY)
    paras = [(title, {"size": tsize, "bold": True, "color": tc, "after": 1})] + ([(sub, {"size": 10.5, "color": INK})] if sub else [])
    text(s, x + 0.06, y + 0.04, BW - 0.12, h - 0.08, paras, align="c", anchor="m")
    if num:
        circle_num(s, x + BW - 0.2, y - 0.15, num, d=0.32, fill=ORANGE if kind == CORE else BLUE, size=11)


text(s, 0.89, 2.0, 6, 0.3, "OFFLINE · ON THE TRAINING DAY", size=11, color=MUTED, bold=True)
for i, (t_, sb, k, n_) in enumerate([("Day-1 trace", "the training day’s requests", KEPT, None),
                                     ("Episodes", "Baleen’s residency model", KEPT, None),
                                     ("Min–max energy", "over all windows", CORE, 1),
                                     ("Ising solver", "parallel tempering", CORE, 1),
                                     ("Peak model", "GBM on Ising labels + load", NEW, 2)]):
    dbox(X5[i], 2.38, t_, sb, k, n_)
    if i:
        arrow(s, X5[i - 1] + BW + 0.04, 2.84, X5[i] - 0.04, 2.84, color=GREY, w=2)
text(s, 0.89, 3.62, 6, 0.3, "ONLINE · EVERY REQUEST", size=11, color=MUTED, bold=True)
for i, (t_, sb, k, n_) in enumerate([("Request", "a GET at time t", KEPT, None),
                                     ("Load meter", "past 10 min only", NEW, None),
                                     ("Adaptive bar", "lower when busy", NEW, 3),
                                     ("Admit?", "either model clears its bar → flash", NEW, 3)]):
    dbox(X5[i], 4.0, t_, sb, k, n_)
for i in range(3):
    arrow(s, X5[i] + BW + 0.04, 4.46, X5[i + 1] - 0.04, 4.46, color=GREY, w=2)
dbox(X5[4], 4.0, "Peak model", None, NEW, h=0.42, tsize=12)
dbox(X5[4], 4.5, "Baleen’s model", None, KEPT, h=0.42, tsize=12)
arrow(s, X5[4] - 0.04, 4.46, X5[3] + BW + 0.04, 4.46, color=GREY, w=2)
arrow(s, X5[4] + BW / 2, 3.33, X5[4] + BW / 2, 3.98, color=BLUE, w=2.25)
text(s, X5[3] + 0.2, 3.45, 2.3, 0.3, "trained peak model", size=10.5, color=BLUE, align="r")
CW = (11.56 - 0.5) / 3
for i, (n_, col, fill, ttl, body) in enumerate([
        (1, ORANGE, PALEOR, "Ising labels", "The min–max selection, solved by an Ising solver, marks what to cache to keep the "
                                            "busiest window low"),
        (2, BLUE, PALE, "Peak model", "A GBM trained on the Ising labels, with the load of the last 10, 30 and 60 min; it runs "
                                      "next to Baleen’s model"),
        (3, BLUE, PALE, "Load-aware admission", "Admit if either model clears its bar; bar θ_{t} = θ · clip((load_{t} / 20)^{−1}, "
                                                "0.25, 4)")]):
    x0 = 0.89 + i * (CW + 0.25)
    box(s, x0, 5.3, CW, 1.2, fill=fill, radius=0.06)
    circle_num(s, x0 + 0.15, 5.42, n_, d=0.32, fill=col, size=11)
    text(s, x0 + 0.58, 5.4, CW - 0.7, 1.05, [(ttl, {"size": 13, "bold": True, "color": col, "after": 2}), body], size=11.5)

# =====================================================================
# 7 · Algorithm
# =====================================================================
s = d.content("OUR METHOD · ALGORITHM", "PeakBaleen vs Baleen, line by line",
              "Left is Baleen: sort episodes by disk time saved per byte, label the prefix that fits the write budget, train "
              "the model, and admit when the score beats theta. Right is PeakBaleen. Orange is the Ising core: the load left in "
              "each window, a smooth max over all windows plus a quadratic budget penalty, solved by parallel tempering from an "
              "LP warm start. Line 5 trains the peak model on the Ising labels. Online, line 10 admits a request if either "
              "Baleen's model or the peak model clears its bar; kappa scales the peak model's bar to its own day-one threshold, "
              "and the bar drops when the disks are busy. Theta is still tuned to the same write rate.")
text(s, 0.89, 2.0, 5.1, 0.35, "Algorithm 1 · Baleen", size=16, color=NAVY, bold=True)
picture(s, os.path.join(HERE, "algorithm_v2", "alg1.png"), 0.89, 2.45, w=5.1, h=5.1 * 611 / 1816)
for i, (fill, ln, lab) in enumerate([(RGBColor(0xE6, 0xE9, 0xEE), SOFT, "<B>Same</B> as Baleen"),
                                     (RGBColor(0xD6, 0xE4, 0xF7), LBLUE, "<B>New</B>: peak model, load, either-model admission"),
                                     (RGBColor(0xFC, 0xE1, 0xCC), RGBColor(0xE7, 0xB4, 0x8F), "<B>New core</B>: min–max energy, Ising solver")]):
    box(s, 0.95, 4.55 + i * 0.45, 0.42, 0.3, fill=fill, line=ln, radius=0.1)
    text(s, 1.5, 4.52 + i * 0.45, 4.6, 0.35, lab, size=13, anchor="m")
text(s, 6.2, 2.0, 6.25, 0.35, "<blue>Algorithm 2 · PeakBaleen (ours)</blue>", size=16, color=NAVY, bold=True)
picture(s, os.path.join(HERE, "algorithm_v2", "alg2.png"), 6.2, 2.45, w=6.25, h=6.25 * 905 / 1816)
text(s, 0.89, 6.0, 5.1, 0.6, "Lines 1–6 run offline, once per training day; no solver runs at request time.", size=12, color=MUTED)

# =====================================================================
# 8 · Result 1 · Offline
# =====================================================================
off = N["offline"]
s = d.content("RESULT 1 · OFFLINE", "Offline, the Ising min–max oracle cuts the peak by 13.7% and wins 37 of 39 samples",
              "First result, offline. We compare the two oracles directly: Baleen's OPT, which is optimal for the average, and "
              "our min-max oracle solved by the Ising solver, both replayed in the simulator at the same write rate. Across 39 "
              "samples of Regions 4 to 7, ours lowers the peak by 13.7 percent per sample on average and wins 37 of them. On "
              "Regions 5 to 7 it wins all 30, by 16 percent.")
cd = CategoryChartData()
cd.categories = [f"{r['region']}\n−{r['reduction']}% · {r['wins']}/{r['n']}" for r in off["regions"]]
cd.add_series("Baleen’s OPT (average-optimal)", [r["opt"] for r in off["regions"]])
cd.add_series("Ising min–max oracle (ours)", [r["ours"] for r in off["regions"]])
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, 0.89, 2.0, 7.5, 4.0, cd, [GREY, ORANGE], maxv=40, major=10, cat_size=11)
text(s, 0.89, 6.05, 7.5, 0.45, "Mean P100 (%) of each offline selection, replayed in the simulator at 35.6 MB/s; lower is "
     "better. Under each region: mean per-sample reduction · samples won.", size=10, color=MUTED)
pt = off["solvers"]["pt"]
for i, (big, small) in enumerate([(f"−{pt['reduction']:.1f}%", "mean per-sample peak reduction against Baleen’s OPT"),
                                  (f"{pt['wins']} / {pt['n']}", "samples won, Regions 4–7"),
                                  ("30 / 30", "samples won on Regions 5–7, <B>−16.2%</B>")]):
    box(s, 8.75, 2.05 + i * 1.5, 3.7, 1.35, fill=WHITE, line=LINE, radius=0.04)
    text(s, 8.95, 2.12 + i * 1.5, 3.4, 0.6, big, size=30, color=ORANGE, bold=True)
    text(s, 8.95, 2.72 + i * 1.5, 3.4, 0.62, small, size=11.5)

# =====================================================================
# 9 · Result 2 · Ising solver
# =====================================================================
s = d.content("RESULT 2 · ISING SOLVER", "The Ising solver finds the lowest peaks and scales to large instances",
              "Second, the solver. On the same 39 samples and the same objective, parallel tempering gives the largest mean "
              "peak reduction, 13.7 percent, against 13.2 for CP-SAT and 13.0 for linear programming. With a short solve budget "
              "of three seconds, it matches or beats the best classical solver on all six test samples. And Ising formulations "
              "scale: matrix-free simulated bifurcation handles 126 thousand variables in 214 megabytes, and parallel tempering "
              "stays within 165 megabytes, while a dense solver runs out of memory beyond about 70 thousand variables.")
sv = off["solvers"]
cd = CategoryChartData()
cd.categories = ["LP + round + repair", "CP-SAT", "Ising: parallel tempering"]
cd.add_series("Mean offline peak reduction (%)", [sv["lp"]["reduction"], sv["cpsat"]["reduction"], sv["pt"]["reduction"]])
ch = chart(s, XL_CHART_TYPE.BAR_CLUSTERED, 0.89, 2.05, 5.9, 3.4, cd, [GREY], maxv=16, major=4, legend=False, cat_size=12,
           label_fmt='0.0"%"')
ch.category_axis.reverse_order = True
ch.has_title = False
ch.plots[0].gap_width = 45
p_ = ch.plots[0].series[0].points[2]
p_.format.fill.solid()
p_.format.fill.fore_color.rgb = ORANGE
text(s, 0.89, 5.5, 5.9, 0.5, "Mean per-sample peak reduction against Baleen’s OPT; 39 samples, same objective, 300 s each.",
     size=10, color=MUTED)
box(s, 7.1, 2.05, 5.35, 1.9, fill=WHITE, line=LINE, radius=0.04)
text(s, 7.3, 2.12, 5.0, 0.3, "SHORT SOLVE BUDGET", size=12, color=BLUE, bold=True)
text(s, 7.3, 2.45, 5.0, 0.7, "6 / 6", size=34, color=ORANGE, bold=True)
text(s, 7.3, 3.2, 5.0, 0.7, "test samples where Ising matches or beats the best classical solver at a 3 s budget",
     size=12.5)
card(s, 7.1, 4.1, 5.35, 1.9, [
    head("SCALES TO LARGE INSTANCES"),
    bl("Matrix-free simulated bifurcation: <B>214 MB</B> at <B>126k</B> variables", after=4),
    bl("Parallel tempering (sparse): ≤ <B>165 MB</B>", after=4),
    bl("A dense solver runs out of memory beyond ≈ 70k variables (123 GB machine)", after=0),
], size=12.5)

# =====================================================================
# 10 · Result 3 · Online with Ising labels (dev)
# =====================================================================
x1 = V["dev_x1"]
s = d.content("RESULT 3 · ONLINE", "Online, a model trained on Ising labels learns to cache the peak",
              "Third, online. Online means we replay the test days in Baleen's simulator and the trained model decides request "
              "by request, without seeing the future. A model trained on the Ising labels, with the load feature and the "
              "load-aware bar, lowers the peak by 3.4 percent against Baleen on our development samples, winning 6 of 8, and "
              "by 6.6 percent on Region6, winning all 4. The reason: Region6's peaks are big sequential scans. The Ising labels "
              "teach the model to admit them at the peak: it caches 41 percent of the peak window instead of 22, and the peak "
              "moves off the scan in 10 of 12 retrains. Load-aware admission helps the Ising labels most: plus 1.17 points on "
              "every sample, versus 0.62 on Baleen's labels.")
dv = x1["dev"]
cd = CategoryChartData()
cd.categories = [f"All dev samples\n{dv['all']['pct']:+.1f}% · {dv['all']['wins']}/{dv['all']['n']}".replace("-", "−"),
                 f"Region6\n{dv['Region6']['pct']:+.1f}% · {dv['Region6']['wins']}/{dv['Region6']['n']}".replace("-", "−")]
cd.add_series("Baleen", [dv["all"]["baleen"], dv["Region6"]["baleen"]])
cd.add_series("Ising labels + load-aware admission", [dv["all"]["ising"], dv["Region6"]["ising"]])
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, 0.89, 2.0, 6.0, 4.0, cd, [GREY, ORANGE], maxv=45, major=10, cat_size=11.5)
text(s, 0.89, 6.05, 6.0, 0.45, "Mean deployed P100 (%), lower is better; development samples of Region6 and Region7 "
     "(s0–s0.3), 3 retrains each.", size=10, color=MUTED)
mb, mi = x1["mech"]["baleen"], x1["mech"]["ising"]
for i, (big, small) in enumerate([
        (f"{round(100 * mb['peak_adm'])}% → {round(100 * mi['peak_adm'])}%", "of Region6’s peak window cached in flash"),
        (f"{mb['scan_peaks']}/{mb['n']} → {mi['scan_peaks']}/{mi['n']}", "retrains whose peak is a scan (Region6)"),
        (f"+{x1['bar_on_ising']:.2f}", f"points from load-aware admission on Ising labels ({x1['bar_on_ising_wins']}/8 "
                                        f"samples), vs +{x1['bar_on_baleen']:.2f} on Baleen’s labels")]):
    box(s, 7.2, 2.05 + i * 1.5, 5.25, 1.35, fill=WHITE, line=LINE, radius=0.04)
    text(s, 7.4, 2.12 + i * 1.5, 4.9, 0.6, big, size=28, color=ORANGE, bold=True)
    text(s, 7.4, 2.72 + i * 1.5, 4.9, 0.62, small, size=12)

# =====================================================================
# 11 · Result 4 · PeakBaleen on dev
# =====================================================================
u = V["dev_union"]
s = d.content("RESULT 4 · PEAKBALEEN", "PeakBaleen beats Baleen on all 10 development samples",
              "Fourth, the full PeakBaleen: Baleen's model plus the Ising peak model, with load-aware admission. On ten "
              "development samples from four clusters, it beats Baleen on all ten, lowering the peak by 3.9 percent. It also "
              "beats Baleen with the load feature on 9 of 10, and Baleen with the load-aware bar alone on 7 of 10, so the Ising "
              "peak model adds on top of load-aware admission. And the Ising labels matter: the same design with labels from "
              "CP-SAT reaches 36.13, while the Ising version reaches 35.36.")
rows = [["Configuration", "Mean P100 (%)", "PeakBaleen better on"],
        ["Baleen", f"{u['baleen']:.2f}", f"<B>{u['baleen_wins']} / 10</B> samples"],
        ["Baleen + load feature", f"{u['load']:.2f}", f"{u['load_wins']} / 10"],
        ["Baleen + load-aware admission", f"{u['bar']:.2f}", f"{u['bar_wins']} / 10"],
        ["PeakBaleen with CP-SAT labels", f"{u['cpsat']:.2f}", f"{u['cpsat_wins']} / 10"],
        ["<or>PeakBaleen (Ising labels)</or>", f"<or><B>{u['peak']:.2f}</B></or>", "—"]]
grid(s, 0.89, 2.05, [3.9, 1.9, 2.2], rows, rh=0.55, size=14, aligns=["l", "r", "r"], shade={5: PALEOR}, bold_first=True)
text(s, 0.89, 5.45, 8.0, 0.6, "Development samples: Region6 and Region7 s0–s0.3, Region5 s0, Region1 s0; 3 retrains each; "
     "lower is better.", size=10.5, color=MUTED)
for i, (big, small) in enumerate([(f"{u['pct_baleen']:+.1f}%".replace("-", "−"), f"peak against Baleen, better on "
                                                                                  f"<B>{u['baleen_wins']} / 10</B> samples"),
                                  ("Ising > CP-SAT", f"labels in the same design: {u['peak']:.2f} vs {u['cpsat']:.2f}")]):
    box(s, 9.2, 2.05 + i * 1.75, 3.25, 1.55, fill=WHITE, line=LINE, radius=0.04)
    text(s, 9.4, 2.12 + i * 1.75, 2.95, 0.6, big, size=26 if i else 30, color=ORANGE, bold=True)
    text(s, 9.4, 2.75 + i * 1.75, 2.95, 0.75, small, size=12)

# =====================================================================
# 12 · Result 5 · Fresh clusters
# =====================================================================
r4, r5 = V["region4"], V["region5"]
s = d.content("RESULT 5 · NEW CLUSTERS", "On a cluster it never saw, PeakBaleen cuts Baleen’s peak by 14.9%",
              "Fifth, clusters the design never saw. On Region4, PeakBaleen lowers the peak from 50.7 to 43.2 percent, 14.9 "
              "percent below Baleen and better on 4 of 5 samples, and 23.9 percent below Baleen with the load feature. The "
              "Ising-label version again beats the CP-SAT-label version, 43.2 against 44.4. On Region5 we ran a pre-registered "
              "test of load-aware admission, PeakBaleen's third component: it passed, minus 3.2 percent on 5 of 6 samples, and "
              "minus 4.7 percent on all 6 with the load feature.")
cd = CategoryChartData()
cd.categories = ["Baleen", "Baleen + load feature", "PeakBaleen, CP-SAT labels", "PeakBaleen (Ising labels)"]
cd.add_series("Region4 mean P100 (%)", [r4["baleen"], r4["load"], r4["cpsat"], r4["peak"]])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, 0.89, 2.0, 7.0, 4.0, cd, [GREY], maxv=60, major=10, legend=False, cat_size=11)
ch.has_title = False
ch.plots[0].gap_width = 70
for i, col in ((2, RGBColor(0xE7, 0xB4, 0x8F)), (3, ORANGE)):
    pp = ch.plots[0].series[0].points[i]
    pp.format.fill.solid()
    pp.format.fill.fore_color.rgb = col
text(s, 0.89, 6.05, 7.0, 0.45, "Region4 (2021 trace, samples s0.2–s0.6, never used for design): mean deployed P100 (%), "
     "lower is better.", size=10, color=MUTED)
box(s, 8.2, 2.05, 4.25, 2.05, fill=WHITE, line=LINE, radius=0.04)
text(s, 8.4, 2.12, 3.9, 0.3, "REGION4", size=12, color=BLUE, bold=True)
text(s, 8.4, 2.42, 3.9, 0.65, f"{r4['pct_baleen']:+.1f}%".replace("-", "−"), size=32, color=ORANGE, bold=True)
text(s, 8.4, 3.1, 3.9, 0.95, f"vs Baleen, better on <B>{r4['wins_baleen']} / {r4['n']}</B> samples; "
     f"{r4['pct_load']:+.1f}% vs Baleen + load feature ({r4['wins_load']} / {r4['n']})".replace("-", "−"), size=12)
card(s, 8.2, 4.25, 4.25, 1.8, [
    head("REGION5 · PRE-REGISTERED TEST"),
    ("Load-aware admission (component 3) on a cluster never run before:", {"after": 5}),
    (f"<blue><B>{r5['bar']['pct']:+.1f}%</B></blue>, better on {r5['bar']['wins']} / 6 samples".replace("-", "−"), {"after": 3}),
    (f"with the load feature: <blue><B>{r5['load_bar']['pct']:+.1f}%</B></blue>, {r5['load_bar']['wins']} / 6".replace("-", "−"), {}),
], size=12.5, fill=PALE, line=None)

# =====================================================================
# 13 · Conclusion
# =====================================================================
s = d.content("CONCLUSION", "What we built and what it achieves",
              "To conclude. One: formulating admission as a min-max problem and solving it with an Ising solver finds much "
              "better peaks offline, 13.7 percent below Baleen's own oracle, with the Ising solver giving the lowest peaks and "
              "scaling to large instances. Two: a model trained on those Ising labels learns to cache the peak online. Three: "
              "PeakBaleen, Baleen's model plus the Ising peak model with load-aware admission, beats Baleen on all ten "
              "development samples and by 14.9 percent on a cluster it never saw. Next, we will train the labels over several "
              "days, run the final test on our held-back samples, and cover all seven clusters. Thank you.")
CW = (11.56 - 0.5) / 3
for i, (col, fill, ttl, body) in enumerate([
        (ORANGE, PALEOR, "Ising finds better peaks offline",
         "<B>−13.7%</B> against Baleen’s oracle, <B>37 / 39</B> samples; the lowest peaks of the solvers we tried, and it "
         "scales to 126k variables."),
        (NAVY, CREAM, "Ising labels teach the model the peak",
         "Online, <B>−3.4%</B> on development samples and <B>−6.6%</B> on Region6: the model caches 41% of the peak window "
         "instead of 22%."),
        (BLUE, PALE, "PeakBaleen beats Baleen online",
         "<B>10 / 10</B> development samples; <B>−14.9%</B> on the unseen Region4; load-aware admission passes a "
         "pre-registered test on Region5.")]):
    x0 = 0.89 + i * (CW + 0.25)
    box(s, x0, 2.05, CW, 2.75, fill=fill, radius=0.05)
    circle_num(s, x0 + 0.2, 2.22, i + 1, d=0.4, fill=col, size=13)
    text(s, x0 + 0.2, 2.75, CW - 0.4, 2.0, [(ttl, {"size": 15, "bold": True, "color": col, "after": 6}), body], size=13)
card(s, 0.89, 5.0, 11.56, 0.95, [head("NEXT"),
                                 ("Train the Ising labels over several days  ·  final test on held-back samples s0.7–s0.9  ·  "
                                  "all seven clusters", {})], size=13)
bar(s, 0.89, 6.1, 11.56, 0.5, "Thank you · Questions?", size=15)

# =====================================================================
# Backup
# =====================================================================
s = d.dark("Backup slides for questions.")
text(s, 0.89, 3.2, 11.56, 1.0, "Backup", size=40, color=CREAM, bold=True, align="c")

ab, r5v = N["ablation"], N["region5"]
s = d.content("BACKUP · REGION5 TEST", "Region5 pre-registered test, sample by sample",
              "Region5, sample by sample. Load-aware admission beats Baleen on 5 of 6 samples, and with the load feature on "
              "all 6.")
rows = [["Sample", "Baleen", "+ load-aware admission", "+ load feature + load-aware admission"]]
for r in r5v["rows"]:
    rows.append([r["inst"].replace("_", " "), f"{r['A']:.2f}", f"{r['Aa']:.2f}", f"{r['Ba']:.2f}"])
rows.append(["Mean", f"{ab['Region5']['baleen']:.2f}", f"<blue><B>{ab['Region5']['bar']['p100']:.2f}</B></blue>",
             f"<blue><B>{ab['Region5']['load_bar']['p100']:.2f}</B></blue>"])
grid(s, 0.89, 2.05, [2.4, 2.0, 3.2, 3.9], rows, rh=0.48, size=13, aligns=["l", "r", "r", "r"], shade={7: PALE}, bold_first=True)
text(s, 0.89, 6.0, 11.5, 0.4, "Deployed P100 (%), mean of 3 retrains; lower is better.", size=10.5, color=MUTED)

s = d.content("BACKUP · REPRODUCTION", "Our Baleen reproduction matches the authors’ runs",
              "If asked about the reproduction. RejectX and CoinFlip replays match the authors' runs exactly, Baleen matches "
              "within 0.6 points with the released metric, and the authors' notebook on their results file gives the paper's "
              "averages exactly. The paper's Figure 9 Baleen bars for Regions 6 and 7 used an older version of the metric.")
CW = (11.56 - 0.25) / 2
for i, (ttl, body) in enumerate([
        ("Bit-exact baselines", "RejectX and CoinFlip replays match the authors’ runs exactly (Region7: 42.455 and 48.961)."),
        ("Baleen within 0.6 points", "Against the authors’ runs measured with the released metric, after re-tuning the "
                                     "threshold to the same write rate (paper §4.1)."),
        ("Figure 9 metric", "The paper’s Fig. 9 Baleen bars for Region7 / Region6 (37.59 / 41.31) use an older metric. "
                            "Ours, over 9 retrains: 40.10 ± 0.18 / 43.25 ± 0.04."),
        ("Paper averages exact", "The authors’ notebook on their results file gives 28.11 / 31.95 / 34.63 (Baleen / RejectX / "
                                 "CoinFlip), as in the paper.")]):
    x0, y0 = 0.89 + (i % 2) * (CW + 0.25), 2.05 + (i // 2) * 1.95
    card(s, x0, y0, CW, 1.75, [(ttl, {"size": 15, "bold": True, "color": NAVY, "after": 6}), body], size=13)

d.save(os.path.join(HERE, OUT))

# the speaker notes as one file, for rehearsal
lines = ["# PeakBaleen final presentation (v3): speaker notes", "",
         f"Generated by build_deck_v3.py from {OUT}. Slides 15-16 are backup.", ""]
for i, sl in enumerate(d.prs.slides, 1):
    title = sl.shapes.title.text_frame.text if sl.shapes.title is not None else ("Title" if i == 1 else "Backup")
    lines += [f"## {i} · {title}", "", sl.notes_slide.notes_text_frame.text, ""]
open(os.path.join(HERE, "SPEAKER_NOTES_v3.md"), "w", encoding="utf-8").write("\n".join(lines))
