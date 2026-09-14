STATUS: not_yet_published
TOTAL_PAPERS: 0
INCLUDED: 0

## Sources

The 27th ACM/IFIP International Middleware Conference (Middleware 2026) has **not yet
taken place** and its main-track accepted-paper list is **not public** as of 2026-09-14.

What I checked:

1. **Official conference site** — https://middleware-conf.github.io/2026/ (also served at
   https://middleware-conf.org/2026/ and https://www.middleware-conf.org/).
   The landing page announces the conference for **14–18 December 2026**, Universitat
   Rovira i Virgili, Tarragona, Spain. General chair Pedro García López; PC co-chairs
   Sara Bouchenak and Abhishek Chandra.
   The site has no accepted-papers or program listing. I probed
   `/accepted-papers`, `/accepted_papers`, `/accepted`, `/papers`, `/program`,
   `/technical-program`, `/program.html`, `/accepted-papers.html`, `/sitemap.xml` —
   all returned HTTP 404.

2. **Site navigation, authoritative check** — the navbar template
   (https://raw.githubusercontent.com/middleware-conf/2026/main/fixed-templates/navbar.html)
   contains a top-level `PROGRAM` entry whose href is `/2026/TBD.html`, and that page
   renders exactly "PROGRAM — To Be Announced". The organizers have therefore explicitly
   deferred publication of the program.

3. **Full file listing of the official site repository** —
   https://github.com/middleware-conf/2026 (branch `main`, last commit 2026-09-10,
   "updated Industry Track PC"). The complete git tree contains only: `index.html`,
   `TBD.html`, the seven `calls/*` pages, `important-dates`, `organizing-committee`,
   `program-committee`, `workshops`, `venue-information`, `accommodation-information`,
   `visa-information`, `conference-registration`, `camera-ready-instructions`,
   `sponsorship`, plus assets. There is no accepted-papers or program file, published or
   draft.

4. **Call for Research Papers timeline** —
   https://middleware-conf.github.io/2026/calls/call-for-research-papers/
   confirms the two-cycle model: Cycle 1 notification 2026-03-06, camera-ready
   2026-04-24; Cycle 2 notification 2026-08-28, **camera-ready due 2026-10-16**.
   Both notification dates have passed, but camera-ready for the summer cycle is still a
   month away, which is consistent with no public list yet.

5. **Cross-check 1 — DBLP.** https://dblp.org/db/conf/middleware/index.html (fetched
   through a text-rendering proxy; dblp serves an Anubis bot-challenge to plain `curl`
   and to browser user-agents alike). The most recent indexed volume is *Proceedings of
   the 26th International Middleware Conference, MIDDLEWARE 2025, Vanderbilt University,
   Nashville, TN, USA, December 15–19, 2025* (ISBN 979-8-4007-1554-9). There is **no
   27th / 2026 volume**.

6. **Cross-check 2 — ACM Digital Library.** https://dl.acm.org/conference/middleware/proceedings
   is behind a Cloudflare challenge (HTTP 403 to both `curl` and WebFetch), so I verified
   indirectly by search: the newest indexed volumes are the 26th International Middleware
   Conference main track (10.1145/3721462 / 3721464) and Industry Track (10.1145/3721463),
   both from December 2025. No "Proceedings of the 27th International Middleware
   Conference" exists.

Conclusion: the main-track paper list for Middleware 2026 cannot be enumerated today.
Both accept notifications (2026-03-06 and 2026-08-28) have gone out, so the list exists
privately; it should become public once camera-ready copy closes on 2026-10-16 and the
program page replaces `/2026/TBD.html`. Re-run this scout after mid-October 2026, or
after the ACM DL proceedings appear around the conference dates (14–18 December 2026).

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
