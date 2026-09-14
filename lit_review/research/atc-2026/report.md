STATUS: not_held
TOTAL_PAPERS: 0
INCLUDED: 0

## Sources

**Conclusion: USENIX ATC 2026 does not exist. USENIX ATC '25 (July 7–9, 2025, Boston) was the
final USENIX Annual Technical Conference; USENIX sunset the conference after 50 years.**

Evidence checked on 2026-09-13:

1. `https://www.usenix.org/conference/atc26` — HTTP 200 but the server serves the **USENIX
   ATC '25** page (page title `USENIX ATC '25 | USENIX`, "2025 USENIX Annual Technical
   Conference, July 7–9, 2025, Boston, MA, USA"). There is no atc26 conference object.
2. `https://www.usenix.org/conference/atc26/technical-sessions` — **HTTP 404**.
3. `https://www.usenix.org/conference/atc26/accepted-papers` — **HTTP 404**.
4. The ATC '25 page links to `https://www.usenix.org/blog/usenix-atc-announcement`
   ("Please read this announcement about USENIX ATC"). Direct `curl` and WebFetch of that
   URL are blocked by Cloudflare (HTTP 403 / JS challenge), so it was cross-checked via
   secondary sources below.
5. Cross-check via secondary coverage of the announcement: Admin Magazine
   ("USENIX Annual Technical Conference To Be Discontinued"), LWN.net
   ("The end of the USENIX Annual Technical Conference", https://lwn.net/Articles/1020306/),
   Bryan Cantrill's "RIP USENIX ATC" (2025-05-11), USENIX's own follow-up blog post
   "Preserving the Legacy of USENIX ATC", and the Wikipedia article
   "USENIX Annual Technical Conference". All agree ATC '25 was the last USENIX-run edition;
   USENIX cited declining attendance / loss of critical mass.
6. `https://dblp.org/db/conf/usenix/usenix2026.html` — returns only an Anubis
   proof-of-work bot-protection page, no paper data (no usable DBLP entry to enumerate).

### About the successor venue (also not usable this cycle)

ACM SIGOPS took over the conference after a community petition. The successor is the
**ACM SIGOPS Annual Technical Conference (ATC)** — same acronym, new sponsor, so it is a
different venue name from "USENIX ATC".

- `https://atc.sigops.org/2026/` — "ATC 2026: The 2026 ACM SIGOPS Annual Technical
  Conference, **November 15–18, 2026**, Hyatt Hotel, Shatin, Hong Kong."
- `https://sigops.org/s/conferences/atc/2026/cfp.html` — timeline: submission deadline
  June 10, 2026; early rejects August 1, 2026; **author notification September 18, 2026**;
  camera-ready October 16, 2026; conference November 16–18, 2026.
- `https://atc.sigops.org/2026/accepted-papers.html` — **HTTP 404**. The site has an
  "Accepted Papers" nav entry but no page behind it yet.

So even under the successor reading, as of today (2026-09-13) author notification has not
happened (it is 5 days away) and no accepted-paper list is public. That reading would give
`STATUS: not_yet_published`; the ACM DL proceedings would appear around/after November 2026.

**Recommendation for the course project:** treat USENIX ATC as covered by the 2023–2025
editions only, and re-scout "ACM SIGOPS ATC 2026" as a separate venue-year after
mid-October 2026 (camera-ready) or after the November 2026 conference.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
