"""PeakBaleen final presentation deck, built on the ND/EMNLP slide kit (python-pptx; kept outside this repo).

Outline approved 2026-11-24 (13 slides, the reserve-test slide dropped) plus 3 backup slides.
Chart values come from result/numbers.json (code/recompute_final.py); every stated number is mapped in SOURCES.md.

    SLIDE_KIT=<kit dir with ndslides.py> PYTHONDONTWRITEBYTECODE=1 <python with python-pptx 1.0.2> build_deck.py PeakBaleen_Final_v1.pptx
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
OUT = sys.argv[1] if len(sys.argv) > 1 else "PeakBaleen_Final_v1.pptx"
N = json.load(open(os.path.join(HERE, "result", "numbers.json")))
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
    "same flash-write budget. Today: the task, our design, and the full results, including what did not work.")
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
s = d.content("MOTIVATION", "Disks are bought for the busiest 10 minutes, but Baleen optimizes the average",
              "Bulk storage still sits on hard disks, and a flash cache in front of them absorbs reads. Flash wears out, so "
              "flash writes are capped, and the admission policy decides which blocks deserve a write. How many disks you "
              "must buy is set by the peak: the busiest ten-minute window, shown in orange on the right. Baleen, the state of "
              "the art, ranks data by disk time saved per byte written and admits in that order until the budget runs out. "
              "That maximizes the total saving, the blue average line, but nothing in it says when the saving lands. The "
              "authors say so themselves and leave optimizing for the peak to future work. That is our question.")
text(s, 0.89, 2.05, 6.0, 3.8, [
    head("FLASH CACHES DECIDE HOW MANY DISKS YOU BUY"),
    bl("Bulk storage sits on hard disks; a <B>flash cache</B> in front absorbs reads"),
    bl("Flash wears out, so <B>flash writes are capped</B>: the admission policy picks which blocks earn a write"),
    bl("The number of disks follows the <B>peak</B>: the busiest 10-minute window (Baleen §3.1)", after=14),
    head("BALEEN (FAST ’24) IS PEAK-BLIND", col=ORANGE),
    bl("Ranks data by <B>disk time saved per byte written</B>, admits in that order until the budget runs out"),
    bl("That maximizes the <B>total</B> saving; nothing says <I>when</I> the saving lands"),
    bl("The authors, on the peak: <I>“…we leave that for future work”</I> (§3.1)"),
], size=14)
box(s, 7.25, 2.05, 5.2, 3.75, fill=WHITE, line=LINE, radius=0.02)
text(s, 7.4, 2.15, 4.9, 0.3, "DISK LOAD PER 10-MINUTE WINDOW (SCHEMATIC)", size=9.5, color=MUTED, bold=True)
py = bars(s, 7.55, 2.75, 3.25, 2.6, PROFILE, 340)
hline(s, 7.45, 10.9, py, ORANGE)
avg = 2.75 + 2.6 - 2.6 * (sum(PROFILE) / len(PROFILE)) / 340
hline(s, 7.45, 10.9, avg, BLUE, w=1.75)
text(s, 10.98, py - 0.25, 1.4, 0.6, "<B>peak</B>: sets the number of disks", size=10.5, color=ORANGE, anchor="m")
text(s, 10.98, avg - 0.25, 1.4, 0.6, "<B>average</B>: what Baleen lowers", size=10.5, color=BLUE, anchor="m")
bar(s, 0.89, 6.05, 11.56, 0.55, "Our question: with the same flash-write budget, can we lower the peak instead of the average?")

# =====================================================================
# 3 · Task
# =====================================================================
s = d.content("THE TASK", "Choose what enters flash, under a write budget, so the peak disk load is lowest",
              "The task. Read requests hit a flash cache in front of hard disks. A hit costs the disks nothing; a miss costs "
              "disk-head time. On each miss, the admission policy decides whether to write the block into flash, and every "
              "admission spends flash writes, which are capped at 35.6 megabytes per second. We minimize P100, the busiest "
              "ten-minute window of disk utilization. The data are Baleen's public traces from Meta's Tectonic storage: Region1 "
              "to Region7 are seven storage clusters, anonymous names from the paper, not geography. Each sample is a different "
              "0.1 percent slice of a cluster's blocks. Day one trains, later days test. We tune on development samples and test "
              "on others, and for pre-registered tests we commit the hypothesis and pass rule to git before running. Samples 0.7 "
              "to 0.9 were held back from every deployed run.")
xs = [0.89, 3.19, 5.49]
for xx, (h_, b_) in zip(xs, [("Request", "a block read (GET) from the trace"), ("Flash cache", "366 GB; a hit costs the disks nothing"),
                             ("HDD on a miss", "costs disk-head time")]):
    card(s, xx, 2.05, 1.95, 1.05, [(h_, {"size": 14, "bold": True, "color": NAVY, "after": 2}), b_], size=11.5)
arrow(s, 2.86, 2.57, 3.17, 2.57, color=GREY, w=2)
arrow(s, 5.16, 2.57, 5.47, 2.57, color=GREY, w=2)
arrow(s, 4.16, 3.72, 4.16, 3.14, color=BLUE, w=2.25)
c = box(s, 0.89, 3.75, 6.55, 1.0, fill=PALE, line=BLUE, lw=1.5, radius=0.06)
text(s, 1.07, 3.85, 6.2, 0.85, [("Admission policy: what we design", {"size": 14, "bold": True, "color": BLUE, "after": 2}),
                                "On a miss: write the block into flash or not? Every admission spends flash writes."], size=12)
card(s, 0.89, 4.95, 6.55, 1.55, [
    head("HOW WE TEST"),
    bl("Tune on dev samples s0–s0.3 of Region6 and Region7; test on other samples", after=2),
    bl("<B>Pre-registered</B> tests: hypothesis and pass rule committed to git before running", after=2),
    bl("Every Baleen-based policy retrained ≥ 3 times; write rate matched within ±1%", after=2),
    bl("Samples s0.7–s0.9 held back: no deployed run has used them", after=0),
], size=11.5)
card(s, 7.75, 2.05, 4.7, 4.45, [
    head("PROBLEM"),
    ("<B>Constraint</B>: flash write rate 35.6 MB/s (±1%), 366 GB cache", {"after": 8}),
    ("<B>Minimize</B>: P100, the busiest 10-minute window of HDD utilization (%)", {"after": 8}),
    ("<B>Data</B>: Baleen’s public Meta Tectonic traces. <B>Region1–7</B> = seven storage clusters (anonymous names from "
     "the paper), recorded in 2019, 2021 and 2023", {"after": 8}),
    ("<B>Samples</B> s0 … s0.9: ten different 0.1% slices of a cluster’s blocks. Day 1 trains, later days test", {"after": 8}),
    ("<B>Simulator</B>: BCacheSim, Baleen’s own, kept frozen", {}),
], size=13)

# =====================================================================
# 4 · Baselines
# =====================================================================
s = d.content("BASELINES WE RAN", "Baleen beats the simple policies, but sits 14–25% above its own offline oracle",
              "These are the baselines we ran ourselves, all at the same write rate. The first row is the paper's Figure 9 "
              "average, for reference. CoinFlip admits at random, RejectX rejects first-time items, and Baleen is the machine-"
              "learned policy. Baleen is the strongest deployed baseline everywhere except Region6 s0. The last column is "
              "Baleen's OPT, the offline oracle its model is trained to imitate. On the held-out sets, Baleen online sits 14 to "
              "25 percent above that oracle, which is the headroom we target. And that oracle itself optimizes the average, not "
              "the peak.")
rows = [["Trace", "Year", "Samples", "CoinFlip", "RejectX", "Baleen", "Baleen’s OPT"],
        ["Paper, Fig. 9", "2019–23", "avg of 7", "34.63", "31.95", "28.11", "—"],
        ["Region7", "2023", "s0", "48.96", "42.46", "40.10", "34.52"],
        ["Region6", "2023", "s0", "43.45", "42.32", "43.25", "35.56"],
        ["Region6 + 7", "2023", "s0.4–0.6", "48.64", "40.73", "39.27", "33.62"],
        ["Region5", "2023", "s0.1–0.6", "44.47", "39.35*", "36.17", "30.10"],
        ["Region4", "2021", "s0.2–0.6", "68.84", "65.84", "50.72", "38.13"],
        ["Region1", "2019", "s0.1–0.6", "50.39", "28.20", "24.14", "not run"]]
grid(s, 0.89, 2.05, [1.45, 1.0, 1.0, 0.95, 0.95, 0.9, 1.3], rows, rh=0.44, size=13,
     aligns=["l", "l", "l", "r", "r", "r", "r"], shade={1: PALE}, bold_first=True)
text(s, 0.89, 5.6, 7.6, 0.9, "P100 (%), lower is better, all at 35.6 MB/s. s0 rows are our reproduction; later samples are "
     "held-out tests. Baleen = mean of 3–9 retrains. *RejectX cannot reach the write rate on 5 of the 6 Region5 samples.",
     size=10, color=MUTED)
box(s, 8.85, 2.05, 3.6, 2.35, fill=WHITE, line=LINE, radius=0.04)
text(s, 9.05, 2.15, 3.2, 0.8, "14–25%", size=40, color=ORANGE, bold=True)
text(s, 9.05, 2.95, 3.25, 1.4, "Baleen online above its own offline oracle on the held-out sets: Region6 + 7 <B>14.4%</B>, "
     "Region5 <B>16.8%</B>, Region4 <B>24.8%</B>. That gap is our headroom.", size=12)
card(s, 8.85, 4.55, 3.6, 1.95, [
    ("<B>CoinFlip</B>: admit at random", {"after": 3}),
    ("<B>RejectX</B>: reject first-time items", {"after": 3}),
    ("<B>Baleen</B>: a gradient-boosted model (GBM) imitating its oracle", {"after": 6}),
    ("<or>And the oracle optimizes the <B>average</B>, not the peak</or>", {}),
], size=12)

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
s = d.content("OUR METHOD · DESIGN", "PeakBaleen changes three things in Baleen’s pipeline",
              "PeakBaleen keeps Baleen's pipeline and changes three things, numbered on the diagram. Component one, offline on "
              "the training day: the min-max problem, solved by the Ising solver, replaces Baleen's ranking and becomes the "
              "training labels for Baleen's model. Component two: the model also gets a load feature, how much disk time all "
              "read requests used in the last 10, 30 and 60 minutes, computed only from the past. Component three, online: "
              "the model scores each request and admits it if the score beats a bar. Baleen's bar is fixed; ours drops when "
              "the disks are busy and rises when they are quiet, and its base value is still tuned to the same write budget. "
              "White boxes are unchanged from Baleen, and no solver runs at request time.")
BW, GAPX = 1.95, 0.45
X5 = [0.89 + i * (BW + GAPX) for i in range(5)]
KEPT, CORE, NEW = (WHITE, GREY), (PALEOR, ORANGE), (PALE, BLUE)


def dbox(x, y, title, sub, kind, num=None):
    fill, ln = kind
    box(s, x, y, BW, 0.92, fill=fill, line=ln, lw=1.5 if kind != KEPT else 1.0, radius=0.08)
    tc = ORANGE if kind == CORE else (BLUE if kind == NEW else NAVY)
    text(s, x + 0.06, y + 0.08, BW - 0.12, 0.8, [(title, {"size": 13, "bold": True, "color": tc, "after": 1}),
                                                 (sub, {"size": 10.5, "color": INK})], align="c", anchor="m")
    if num:
        circle_num(s, x + BW - 0.2, y - 0.15, num, d=0.32, fill=ORANGE if kind == CORE else BLUE, size=11)


text(s, 0.89, 2.0, 6, 0.3, "OFFLINE · ON THE TRAINING DAY", size=11, color=MUTED, bold=True)
for i, (t_, sb, k, n_) in enumerate([("Day-1 trace", "the training day’s requests", KEPT, None),
                                     ("Episodes", "Baleen’s residency model", KEPT, None),
                                     ("Min–max energy", "over all windows", CORE, 1),
                                     ("Ising solver", "parallel tempering", CORE, 1),
                                     ("Train GBM", "on labels + load", NEW, 2)]):
    dbox(X5[i], 2.38, t_, sb, k, n_)
    if i:
        arrow(s, X5[i - 1] + BW + 0.04, 2.84, X5[i] - 0.04, 2.84, color=GREY, w=2)
text(s, 0.89, 3.62, 6, 0.3, "ONLINE · EVERY REQUEST", size=11, color=MUTED, bold=True)
for i, (t_, sb, k, n_) in enumerate([("Request", "a GET at time t", KEPT, None),
                                     ("Load meter", "past 10 min only", NEW, 2),
                                     ("Adaptive bar", "lower when busy", NEW, 3),
                                     ("Admit?", "score > bar → flash", KEPT, None),
                                     ("GBM score", "s = f(request, load)", KEPT, None)]):
    dbox(X5[i], 4.0, t_, sb, k, n_)
for i in range(3):
    arrow(s, X5[i] + BW + 0.04, 4.46, X5[i + 1] - 0.04, 4.46, color=GREY, w=2)
arrow(s, X5[4] - 0.04, 4.46, X5[3] + BW + 0.04, 4.46, color=GREY, w=2)
arrow(s, X5[4] + BW / 2, 3.33, X5[4] + BW / 2, 3.98, color=BLUE, w=2.25)
text(s, X5[3] + 0.4, 3.5, 1.9, 0.3, "trained model", size=10.5, color=BLUE, align="r")
CW = (11.56 - 0.5) / 3
for i, (n_, col, fill, ttl, body) in enumerate([
        (1, ORANGE, PALEOR, "New labels", "The min–max selection, solved by an Ising solver, becomes the GBM’s training labels"),
        (2, BLUE, PALE, "Load feature", "The GBM also sees the disk time of all reads in the last 10, 30 and 60 min (past only)"),
        (3, BLUE, PALE, "Adaptive bar", "θ_{t} = θ · clip((load_{t} / 20)^{−1}, 0.25, 4); base θ re-tuned to the same write rate")]):
    x0 = 0.89 + i * (CW + 0.25)
    box(s, x0, 5.3, CW, 1.2, fill=fill, radius=0.06)
    circle_num(s, x0 + 0.15, 5.42, n_, d=0.32, fill=col, size=11)
    text(s, x0 + 0.58, 5.4, CW - 0.7, 1.05, [(ttl, {"size": 13, "bold": True, "color": col, "after": 2}), body], size=11.5)

# =====================================================================
# 7 · Algorithm
# =====================================================================
s = d.content("OUR METHOD · ALGORITHM", "PeakBaleen vs Baleen, line by line",
              "Left is Baleen: sort episodes by disk time saved per byte, label the prefix that fits the write budget, train "
              "the model, and online admit when the score beats theta. Right is PeakBaleen. Orange is the Ising core: the load "
              "left in each window, a smooth max over windows plus a quadratic budget penalty, solved by parallel tempering "
              "from an LP warm start. Its solution becomes the labels. Blue is the rest of what is new: the load feature and "
              "the adaptive bar in lines 8 to 10. Gray is unchanged, including tuning theta to the same write rate. Lines 1 to "
              "6 run offline once per training day.")
text(s, 0.89, 2.0, 5.1, 0.35, "Algorithm 1 · Baleen", size=16, color=NAVY, bold=True)
picture(s, os.path.join(HERE, "assets", "alg1.png"), 0.89, 2.45, w=5.1, h=5.1 * 611 / 1816)
for i, (fill, ln, lab) in enumerate([(RGBColor(0xE6, 0xE9, 0xEE), SOFT, "<B>Same</B> as Baleen"),
                                     (RGBColor(0xD6, 0xE4, 0xF7), LBLUE, "<B>New</B>: labels, load feature, adaptive bar"),
                                     (RGBColor(0xFC, 0xE1, 0xCC), RGBColor(0xE7, 0xB4, 0x8F), "<B>New core</B>: min–max energy, Ising solver")]):
    box(s, 0.95, 4.55 + i * 0.45, 0.42, 0.3, fill=fill, line=ln, radius=0.1)
    text(s, 1.5, 4.52 + i * 0.45, 4.6, 0.35, lab, size=13, anchor="m")
text(s, 6.2, 2.0, 6.25, 0.35, "<blue>Algorithm 2 · PeakBaleen (ours)</blue>", size=16, color=NAVY, bold=True)
picture(s, os.path.join(HERE, "assets", "alg2.png"), 6.2, 2.45, w=6.25, h=6.25 * 905 / 1816)
text(s, 0.89, 6.0, 5.1, 0.6, "Lines 1–6 run offline, once per training day; no solver runs at request time.", size=12, color=MUTED)

# =====================================================================
# 8 · Result 1 · Offline
# =====================================================================
off = N["offline"]
s = d.content("RESULT 1 · OFFLINE", "Offline, our peak-aware oracle cuts the peak by 13.7% and wins 37 of 39 samples",
              "First result, offline. Here we compare the two oracles directly, before any model is trained: Baleen's OPT, "
              "which is average-optimal, against our min-max oracle solved by the Ising solver, both replayed in the simulator "
              "at the same write rate. Across 39 samples of Regions 4 to 7, ours lowers the peak by 13.7 percent per sample on "
              "average and wins 37 of them. On Regions 5 to 7 it wins all 30, by about 16 percent. Region4 is the exception: its "
              "peaks are short bursts that Baleen's oracle already absorbs as far as the budget allows. And note that the "
              "busiest window still moves in simulation on 33 of 39 samples, yet the maximum still drops.")
cd = CategoryChartData()
cd.categories = [f"{r['region']}\n−{r['reduction']}% · {r['wins']}/{r['n']}" for r in off["regions"]]
cd.add_series("Baleen’s OPT (average-optimal)", [r["opt"] for r in off["regions"]])
cd.add_series("Our oracle (min–max, Ising)", [r["ours"] for r in off["regions"]])
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, 0.89, 2.0, 7.5, 4.0, cd, [GREY, ORANGE], maxv=40, major=10, cat_size=11)
text(s, 0.89, 6.05, 7.5, 0.45, "Mean P100 (%) of each offline selection, replayed in the simulator at 35.6 MB/s; lower is "
     "better. Under each region: mean per-sample reduction · samples won.", size=10, color=MUTED)
pt = off["solvers"]["pt"]
for i, (big, small) in enumerate([(f"−{pt['reduction']:.1f}%", "mean per-sample reduction against Baleen’s OPT, 39 samples"),
                                  (f"{pt['wins']} / {pt['n']}", "samples won; Regions 5–7: <B>30 / 30</B>, −16.2%")]):
    box(s, 8.75, 2.05 + i * 1.5, 3.7, 1.35, fill=WHITE, line=LINE, radius=0.04)
    text(s, 8.95, 2.12 + i * 1.5, 3.4, 0.6, big, size=30, color=ORANGE, bold=True)
    text(s, 8.95, 2.72 + i * 1.5, 3.4, 0.62, small, size=11.5)
card(s, 8.75, 5.05, 3.7, 1.45, [("<B>Region4: 7 / 9, −5.4%.</B> Its peaks are short bursts that Baleen’s oracle already "
                                 "absorbs as far as the budget allows.", {"after": 4}),
                                ("<muted>The busiest window still moves on 33 / 39 samples, yet the max drops.</muted>",
                                 {"size": 10.5})], size=11.5, fill=CREAM, line=None)

# =====================================================================
# 9 · Result 2 · Solvers
# =====================================================================
s = d.content("RESULT 2 · SOLVERS", "The gain comes from the min–max objective; Ising ties the classical solvers",
              "Second: is the offline win thanks to the Ising solver, or to the objective? We gave the same problem to two "
              "standard solvers: linear programming with rounding, and Google's CP-SAT. They reach 13.0 and 13.2 percent, "
              "against 13.7 for the Ising solver. Sample by sample, Ising is lower than CP-SAT on 18 of 39 and lower than LP on "
              "22 of 39, so it is a tie. We also pre-registered a test at tight solve budgets of 1, 3 and 10 seconds; Ising "
              "matched the best classical method on 1, 6 and 4 of 6 samples, short of the rule. Where the Ising formulations do "
              "well is scale: in sparse form they stay within a few hundred megabytes at 126 thousand variables, where a dense "
              "package runs out of memory. So the contribution is the min-max formulation; Ising is a competitive way to solve it.")
sv = off["solvers"]
cd = CategoryChartData()
cd.categories = ["LP + round + repair", "CP-SAT (300 s)", "Ising: parallel tempering (300 s)"]
cd.add_series("Mean offline peak reduction (%)", [sv["lp"]["reduction"], sv["cpsat"]["reduction"], sv["pt"]["reduction"]])
ch = chart(s, XL_CHART_TYPE.BAR_CLUSTERED, 0.89, 2.05, 5.7, 2.6, cd, [GREY], maxv=16, major=4, legend=False, cat_size=11.5,
           label_fmt='0.0"%"')
ch.category_axis.reverse_order = True
ch.has_title = False
ch.plots[0].gap_width = 45
p_ = ch.plots[0].series[0].points[2]
p_.format.fill.solid()
p_.format.fill.fore_color.rgb = ORANGE
text(s, 0.89, 4.7, 5.7, 0.5, "Mean per-sample peak reduction against Baleen’s OPT; same 39 samples, same objective.",
     size=10, color=MUTED)
card(s, 0.89, 5.25, 5.7, 0.95, [("Sample by sample, Ising is lower than CP-SAT on <B>18 / 39</B> and lower than LP on "
                               "<B>22 / 39</B>: a tie.", {})], size=13, fill=CREAM, line=None)
card(s, 6.85, 2.05, 5.6, 1.75, [
    head("PRE-REGISTERED: ISING AT TIGHT SOLVE BUDGETS"),
    ("Ising ≤ best classical method, by sample:", {"after": 4}),
    ("1 s: <B>1 / 6</B>   ·   3 s: <B>6 / 6</B>   ·   10 s: <B>4 / 6</B>", {"size": 15, "color": NAVY, "after": 4}),
    ("The rule needed ≥ 5 / 6 at two budgets: <or><B>not supported</B></or>", {}),
], size=12.5)
card(s, 6.85, 3.95, 5.6, 2.25, [
    head("WHERE ISING FORMULATIONS DO WELL: SCALE"),
    bl("Matrix-free simulated bifurcation: ≤ <B>214 MB</B> at <B>126k</B> variables", after=3),
    bl("Parallel tempering (sparse): ≤ <B>165 MB</B>", after=3),
    bl("A dense simulated-bifurcation package runs out of memory beyond ≈ 70k variables (123 GB machine)", after=0),
], size=12.5)

# =====================================================================
# 10 · Result 3 · Deployed
# =====================================================================
ab = N["ablation"]
s = d.content("RESULT 3 · DEPLOYED", "Deployed, the full design collapses on two samples; the adaptive bar alone stays steady",
              "Third, deployed. Deployed means we replay the test days in Baleen's simulator and the trained model decides "
              "request by request, without seeing the future. Each pair of bars is one pre-registered test sample, showing the "
              "change in peak against Baleen; below zero is better. Orange is the full PeakBaleen, all three components. It "
              "beats Baleen on most samples, but collapses on Region7 s0.5, plus 13 points, and on Region5 s0.5, plus 9. Those "
              "collapses flip the average: plus 3.2 percent on Regions 6 and 7, so the pre-registered test fails, and plus 5.3 "
              "on Region5. Blue is Baleen with only the adaptive bar. It is steady: minus 2.5 percent on Regions 6 and 7, and "
              "minus 3.2 percent on Region5, a cluster we had never run, where its pre-registered test passes.")
cd = CategoryChartData()
for reg, pre in (("Region6", "Region6_"), ("Region7", "Region7_"), ("Region5", "Region5_")):
    cat = cd.add_category(reg)
    for smp in N["samples"]:
        if smp["inst"].startswith(pre):
            cat.add_sub_category(smp["inst"].split("_")[1])
order = [x for pre in ("Region6_", "Region7_", "Region5_") for x in N["samples"] if x["inst"].startswith(pre)]
cd.add_series("Full PeakBaleen (1 + 2 + 3)", [x["d_full"] for x in order])
cd.add_series("Baleen + adaptive bar (3)", [x["d_bar"] for x in order])
ch = chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, 0.89, 2.0, 8.2, 4.05, cd, [ORANGE, BLUE], maxv=15, minv=-6, major=3,
           fmt='+0;−0;0', labels=False, cat_size=10.5)
for i, x in enumerate(order):
    if x["d_full"] >= 4:
        point_label(ch.plots[0].series[0], i, f"+{x['d_full']:.1f}", ORANGE)
    if x["d_bar"] <= -4:
        point_label(ch.plots[0].series[1], i, f"−{abs(x['d_bar']):.1f}", BLUE)
text(s, 0.89, 6.08, 8.2, 0.45, "Change in P100 against Baleen (points) on each pre-registered test sample; lower is better.",
     size=10, color=MUTED)
f67, f5 = ab["Region6+7"]["full"], ab["Region5"]["full"]
b67, b5 = ab["Region6+7"]["bar"], ab["Region5"]["bar"]
card(s, 9.35, 2.05, 3.1, 2.15, [
    head("FULL PEAKBALEEN", col=ORANGE),
    (f"Region6 + 7: {sign(f67['pct'])} (wins {f67['wins']}/6): pre-registered test <B>fails</B>", {"after": 5}),
    (f"Region5: {sign(f5['pct'])} (wins {f5['wins']}/6)", {"after": 5}),
    ("Two collapses carry it", {"size": 11, "color": MUTED}),
], size=12, fill=PALEOR, line=None)
card(s, 9.35, 4.35, 3.1, 2.15, [
    head("BALEEN + ADAPTIVE BAR"),
    (f"Region5: {sign(b5['pct'])} (wins {b5['wins']}/6): pre-registered test <B>passes</B>", {"after": 5}),
    (f"Region6 + 7: {sign(b67['pct'])} (wins {b67['wins']}/6), as a control arm", {"after": 5}),
    ("No collapse", {"size": 11, "color": MUTED}),
], size=12, fill=PALE, line=None)

# =====================================================================
# 11 · Result 4 · Ablation
# =====================================================================
s = d.content("RESULT 4 · WHAT EACH COMPONENT ADDS", "Taking the design apart: the adaptive bar carries the deployed gain",
              "Fourth, we take the design apart, on all four test pools. Each cell is the deployed peak and its change against "
              "Baleen. The load feature alone does not help, and on Region4 it hurts. The adaptive bar alone helps on Regions "
              "4 to 7: minus 2.5, minus 3.2 and minus 15.5 percent. Adding the load feature on top is similar. Adding the new "
              "labels on top of both makes things worse. Region1 is the quietest cluster, Baleen's peak is only 24 percent, and "
              "there nothing helps. Only two cells are pre-registered tests: the full design on Regions 6 and 7, which failed, "
              "and the adaptive bar on Region5, which passed. The rest were observed alongside.")


def cell(key, pool):
    c = ab[pool].get(key)
    return "not run" if c is None else f"{c['p100']:.2f}  {sign(c['pct'])}"


POOL = ["Region6+7", "Region5", "Region4", "Region1"]
rows = [["Configuration", "Region6 + 7", "Region5", "Region4", "Region1"],
        ["Baleen (reference)"] + [f"{ab[p]['baleen']:.2f}" for p in POOL],
        ["+ load feature  (2)"] + [cell("load", p) for p in POOL],
        ["+ adaptive bar  (3)"] + [cell("bar", p) for p in POOL],
        ["+ load feature + adaptive bar  (2, 3)"] + [cell("load_bar", p) for p in POOL],
        ["Full PeakBaleen  (1, 2, 3)"] + [cell("full", p) for p in POOL]]
grid(s, 0.89, 2.05, [3.56, 2.0, 2.0, 2.0, 2.0], rows, rh=0.5, size=13, aligns=["l", "r", "r", "r", "r"],
     shade={3: PALE}, bold_first=True)
text(s, 0.89, 5.1, 11.56, 0.6, "Deployed P100 (%) and change against Baleen; lower is better. Pre-registered cells: the full "
     "design on Region6 + 7 (fails) and the adaptive bar on Region5 (passes); the rest were observed alongside.",
     size=10.5, color=MUTED)
bar(s, 0.89, 5.8, 11.56, 0.65, "What helps is spending writes when the disks are busy; the load feature alone does not, "
    "and the new labels hurt", size=14)

# =====================================================================
# 12 · Result 5 · Why
# =====================================================================
cl = N["collapse"]
s = d.content("RESULT 5 · WHY THE LABELS FAIL", "The collapses are scans at the peak that the training day never had",
              "Why did the full design collapse? Both collapsed samples have a scan at the peak: many requests reading large "
              "blocks in order, far into each block. In Region7 s0.5's peak window, 48 percent of the accesses are such reads; "
              "in Region5 s0.5, 52 percent. Region7's training-day peaks had no scans, so our oracle never picked scan data, "
              "and the model learned not to cache it. The chart shows how much of that peak window each policy admitted: "
              "Baleen 57 percent, Baleen with the adaptive bar 67, our full design only 9. The scan goes to the disks, and the "
              "peak rises from 39 to 52. On the right, the counter-example: Region6's training-day peaks are scans, and there "
              "the same labels help. So labels from one day transfer only if that day's peaks look like the test day's.")
text(s, 0.89, 2.05, 4.15, 4.3, [
    head("WHAT HAPPENED"),
    bl("A <B>scan</B>: many reads of large blocks in order, deep into each block (ending past 8 MB)"),
    bl(f"Peak window of Region7 s0.5: <B>{round(100 * cl['Region7_s0.5']['baleen']['big'])}%</B> of accesses are such reads; "
       f"Region5 s0.5: <B>{round(100 * cl['Region5_s0.5']['baleen']['big'])}%</B>"),
    bl("Region7’s training-day peaks had <B>no scans</B>: the oracle never picked scan data, so the model learned "
       "<B>not to cache it</B>"),
    bl("The scan goes to the disks: Region7 s0.5 peak <B>39.1 → 52.3</B>"),
], size=13)
cd = CategoryChartData()
cd.categories = ["Region7 s0.5", "Region5 s0.5"]
for key, name in (("baleen", "Baleen"), ("bar", "+ adaptive bar"), ("full", "Full PeakBaleen")):
    cd.add_series(name, [100 * cl["Region7_s0.5"][key]["adm"], 100 * cl["Region5_s0.5"][key]["adm"]])
chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, 5.2, 2.0, 4.4, 3.75, cd, [GREY, BLUE, ORANGE], maxv=80, major=20,
      fmt='0"%"', label_fmt='0"%"', cat_size=11)
text(s, 5.2, 5.8, 4.4, 0.6, "Share of the peak window’s accesses admitted to flash (mean of 3 retrains)", size=10, color=MUTED)
card(s, 9.85, 2.05, 2.6, 4.1, [
    head("WHEN THE TRAINING DAY HAS SCANS"),
    ("Region6 (dev): its peaks <B>are</B> scans.", {"after": 6}),
    ("The full design admits <B>41%</B> of the peak window vs Baleen’s <B>22%</B>,", {"after": 6}),
    ("and moves the peak off the scan in <B>10 / 12</B> retrains.", {}),
], size=12.5, fill=PALE, line=None)
bar(s, 0.89, 6.38, 11.56, 0.48, "Labels learned on one day transfer only if that day’s peaks look like the test day’s",
    size=13.5)

# =====================================================================
# 13 · Conclusion
# =====================================================================
s = d.content("CONCLUSION", "What we learned",
              "Three takeaways. One: the min-max objective works offline, 13.7 percent lower peak than Baleen's own oracle on "
              "37 of 39 samples, and the solver does not matter, Ising ties LP and CP-SAT, though Ising formulations scale "
              "well. Two: offline is not online. Labels learned on one training day break when the type of peak changes, so "
              "the full design failed its pre-registered test. Three: load-aware admission keeps part of the gain. Baleen with "
              "the adaptive bar passed a pre-registered test on Region5 and helped on Regions 4, 6 and 7, but not on the quiet "
              "Region1. Next, we would train labels over several days so they cover more kinds of peak, run the one-shot final "
              "test on the held-back samples, and cover Regions 2 and 3. Thank you; we are happy to take questions.")
CW = (11.56 - 0.5) / 3
for i, (col, fill, ttl, body) in enumerate([
        (ORANGE, PALEOR, "The min–max objective works offline",
         "<B>−13.7%</B> peak against Baleen’s oracle, <B>37 / 39</B> samples. Ising ties LP and CP-SAT: the objective, "
         "not the solver, is the gain; Ising formulations scale in sparse form."),
        (NAVY, CREAM, "Offline is not online",
         "Labels from one training day break when the type of peak changes. The full design fails its pre-registered "
         "test (<or>+3.2%</or>)."),
        (BLUE, PALE, "Load-aware admission keeps part of the gain",
         "Baleen + adaptive bar: <blue><B>−3.2%</B></blue> pre-registered on Region5; −2.5% to −15.5% observed on Regions "
         "4, 6, 7; no gain on the quiet Region1.")]):
    x0 = 0.89 + i * (CW + 0.25)
    box(s, x0, 2.05, CW, 2.75, fill=fill, radius=0.05)
    circle_num(s, x0 + 0.2, 2.22, i + 1, d=0.4, fill=col, size=13)
    text(s, x0 + 0.2, 2.75, CW - 0.4, 2.0, [(ttl, {"size": 15, "bold": True, "color": col, "after": 6}), body], size=13)
card(s, 0.89, 5.0, 11.56, 0.95, [head("NEXT"),
                                 ("Train labels over several days to cover more kinds of peak  ·  one-shot final test on the "
                                  "held-back samples s0.7–s0.9  ·  Regions 2 and 3  ·  when load-awareness helps", {})],
     size=13)
bar(s, 0.89, 6.1, 11.56, 0.5, "Thank you · Questions?", size=15)

# =====================================================================
# Backup
# =====================================================================
s = d.dark("Backup slides for questions.")
text(s, 0.89, 3.2, 11.56, 1.0, "Backup", size=40, color=CREAM, bold=True, align="c")

r5 = N["region5"]
s = d.content("BACKUP · REGION5 TEST", "The Region5 pass holds, but 69% of its gain comes from one sample",
              "If asked about the strength of the Region5 result. The pass rule used the retrain-level standard error, 0.09, "
              "and the adaptive bar beat Baleen by 1.16 points with 5 of 6 wins. At the sample level the standard error is 0.75, "
              "so the gain is about 1.5 standard errors, and 69 percent of it comes from s0.5. Baleen with both the load feature "
              "and the adaptive bar won all 6 samples, minus 4.7 percent.")
rows = [["Sample", "Baleen", "+ adaptive bar", "+ load + bar", "Gain of the bar"]]
for r in r5["rows"]:
    rows.append([r["inst"].replace("_", " "), f"{r['A']:.2f}", f"{r['Aa']:.2f}", f"{r['Ba']:.2f}", f"{r['gain_Aa']:+.2f}"])
rows.append(["Mean", f"{ab['Region5']['baleen']:.2f}", f"{ab['Region5']['bar']['p100']:.2f}",
             f"{ab['Region5']['load_bar']['p100']:.2f}", "+1.16"])
grid(s, 0.89, 2.05, [2.0, 1.45, 1.6, 1.6, 1.75], rows, rh=0.45, size=13, aligns=["l", "r", "r", "r", "r"],
     shade={5: PALE, 7: CREAM}, bold_first=True)
card(s, 9.6, 2.05, 2.85, 3.6, [
    head("STATISTICS"),
    ("Pass rule (retrain level): +1.16, SE <B>0.09</B>, wins 5 / 6", {"after": 8}),
    ("Sample level: +1.16 ± <B>0.75</B> (≈ 1.5 SE)", {"after": 8}),
    ("<B>69%</B> of the gain from s0.5", {"after": 8}),
    ("+ load + bar: 6 / 6, <blue>−4.7%</blue>", {}),
], size=12.5)

s = d.content("BACKUP · REPRODUCTION", "Baleen reproduces, with one metric nuance in the paper’s Figure 9",
              "If asked about the reproduction. RejectX and CoinFlip replays match the authors' runs exactly. Baleen matches the "
              "authors' runs within 0.6 points when both use the released metric. The paper's Figure 9 Baleen bars for Regions 6 "
              "and 7 come from an older, unreleased version of the disk-time metric, so they cannot be reproduced exactly. "
              "Running the authors' own notebook on their results file gives the paper's averages exactly.")
CW = (11.56 - 0.25) / 2
for i, (ttl, body) in enumerate([
        ("Bit-exact baselines", "RejectX and CoinFlip replays match the authors’ runs exactly (Region7: 42.455 and 48.961)."),
        ("Baleen within 0.6 points", "Against the authors’ runs measured with the released metric, after re-tuning the "
                                     "threshold to the same write rate (paper §4.1)."),
        ("One metric nuance", "The paper’s Fig. 9 Baleen bars for Region7 / Region6 (37.59 / 41.31) use an older, unreleased "
                              "metric. Ours, over 9 retrains: 40.10 ± 0.18 / 43.25 ± 0.04."),
        ("Paper averages exact", "The authors’ notebook on their results file gives 28.11 / 31.95 / 34.63 (Baleen / RejectX / "
                                 "CoinFlip), as in the paper.")]):
    x0, y0 = 0.89 + (i % 2) * (CW + 0.25), 2.05 + (i // 2) * 1.95
    card(s, x0, y0, CW, 1.75, [(ttl, {"size": 15, "bold": True, "color": NAVY, "after": 6}), body], size=13)

s = d.content("BACKUP · RELATED ATTEMPTS", "Load-based admission was tried before, without lowering the peak there",
              "If asked whether the adaptive bar is new. The Baleen authors tried admitting only during high load; it saved "
              "flash writes but did not reduce the peak. Wong's thesis tried load-dependent thresholds on the oracle and got "
              "8 percent fewer writes but only 1.4 percent lower peak, on Region3, a trace we did not run. It also tried "
              "optimizing one fixed peak period, which worked analytically but not in simulation, because the peak moved. Our "
              "bar scales the trained model's threshold continuously and re-tunes it to the same write rate, and is judged at a "
              "matched write rate. We have not measured which of these differences explains the different outcome.")
rows = [["Attempt", "What it did", "Outcome"],
        ["Baleen §5.6", "admit only during high load", "saved flash writes; did not reduce the peak"],
        ["Wong thesis §7.4.1", "load-dependent thresholds on the oracle", "−8.0% flash writes; −1.4% peak (Region3)"],
        ["Wong thesis §7.4.2", "optimize one fixed peak period (PeakOPT)", "−29% analytically; lost in simulation (peak moves)"],
        ["Ours (adaptive bar)", "scale the trained model’s bar with the last 10 min of load; base re-tuned to the same "
                                "write rate", "<blue><B>−3.2%</B></blue> peak at matched write rate (Region5, pre-registered)"]]
grid(s, 0.89, 2.05, [2.6, 4.9, 4.06], rows, rh=0.72, size=12.5, shade={4: PALE}, bold_first=True)
text(s, 0.89, 5.75, 11.56, 0.6, "Which of these differences explains the different outcome has not been measured; Region3, the "
     "thesis’s trace, was not run here.", size=11, color=MUTED)

d.save(os.path.join(HERE, OUT))

# the speaker notes as one file, for rehearsal
lines = ["# PeakBaleen final presentation: speaker notes", "",
         f"Generated by build_deck.py from {OUT}. Slides 15-17 are backup.", ""]
for i, sl in enumerate(d.prs.slides, 1):
    title = sl.shapes.title.text_frame.text if sl.shapes.title is not None else ("Title" if i == 1 else "Backup")
    lines += [f"## {i} · {title}", "", sl.notes_slide.notes_text_frame.text, ""]
open(os.path.join(HERE, "SPEAKER_NOTES.md"), "w", encoding="utf-8").write("\n".join(lines))
