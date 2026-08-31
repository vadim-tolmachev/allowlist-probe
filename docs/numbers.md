# Provenance of every figure in the README

Each row gives the artifact and the computation. Everything except the handset rows is
recomputable from this repository with the one-liners shown.

| Figure | File | How |
|---|---|---|
| 6,176 endpoints parsed | `data/stage1_parsed.json` | 6,146 published; 30 of the author's own endpoints removed before publication (none survived stage 1) |
| 2,044 TCP open | `data/stage2_tcp_open.json` | record count |
| 314 carry traffic | `data/stage3_traffic.json` | count of `ok == true` |
| 38 stable 3 of 3 | `data/stage4_stable.json` | count of `hits == 3` (`tries == 3`) |
| 28 of 38 alive on wi-fi, 4 of those 28 pass on SIM | manual, 22 Aug 2026 | see below |
| control 200 -> 4 (2.0%) | `data/control.json` | count, then `ok == true` |
| 13,691 permitted /24 | `data/twl_scan_subnets.json` | record count; source `openlibrecommunity/twl`, snapshot 10 Jul 2026 |
| 108,564 responsive addresses | `data/twl_scan_subnets.json` | sum of `responsive_unique`; unique per block, duplicates in the upstream `ips` array collapsed |
| median density 0.39% | same | median of `responsive_unique / 256` |
| 91.3% at or below 5% | same | share of blocks with density <= 5% |
| 167 blocks at or above 50% | same | `>= 50%` gives 167; strictly `> 50%` gives 164 |
| maximum 98.4% | same | max density |
| 1,772 community /24 | `data/allowlist_comparison.json` | 2,114 CIDR lines expanded to unique /24 |
| 912 confirmed | same | intersection with the scan |
| 12,779 absent from the list | same | scan minus community list |
| 270 broken by `allowInsecure` removal | upstream run log | count of configurations that failed after Xray 26.3.27 |
| 169 of 314 still TCP-open after 9 days | `data/decay_reprobe.json` | re-probe 31 Aug 2026 of the endpoints that carried traffic on 22 Aug |
| 326 vs 327 open ports | upstream run log | same candidate set probed via a Russian relay and a Dutch host |

## The handset rows have no machine-readable artifact

The 22 August test was run manually in a client application on a physical handset: one
profile of 38 candidates, loaded twice, first over wi-fi and then over a SIM in an
allowlist region. The record is the profile, the observed pass/fail per entry, and the
latencies in the README table. There is no log file, because the client does not produce
one.

Two specific gaps follow from that, stated so nobody has to discover them. The wi-fi leg
is recorded as a count (28 of 38 answered) and not as a per-entry list, so the ten
failures cannot be named. And `data/stage5_reality_rerun.json` is **not** this test: it is
an automated datacentre re-run used to narrow the profile, it also contains four
successes, and they are different endpoints with an order of magnitude more latency. The
file was previously named `stage5_sim_candidates.json`, which invited exactly the wrong
reading.

This is stated plainly rather than dressed up. Automating the handset stage, so that it
produces artifacts on the same footing as the remote stages, is the single largest
methodological gap in this work.

## Figures that were corrected

Earlier drafts of this material, circulated privately, contained the following errors.
They are listed because the corrected versions are weaker, and it should be visible that
they were corrected rather than quietly dropped.

| Claim as written | Status |
|---|---|
| "TCP and gRPC over Reality with a permitted SNI passed 4 of 4" | **Wrong.** 4 passed of 28 live candidates. All four were of that type; not all of that type passed. |
| "141,664 /24 blocks from two community repositories, 16.8% confirmed" | **Not reproducible.** That list was a production artifact assembled from two sources, not present here. The reproducible comparison uses one source: 1,772 blocks, 912 confirmed. |
| Density presented as independent support for sub-/24 granularity | **Withdrawn.** Responsiveness cannot separate "not permitted" from "nothing listening". |
| The prefix scan described as the author's own measurement | **Corrected.** It is `openlibrecommunity/twl`, re-analysed here. |
| "The upstream scan died when its author ran out of SIM cards" | **Corrected.** Data stopped on 10 Jul 2026; the project moved to `openlibrecommunity/rewl`, which has been dormant since 6 Aug 2026. |
| `stage5_sim_candidates.json` named as though it were the handset test | **Renamed** to `stage5_reality_rerun.json`. It is a datacentre re-run; its four successes are not the handset's four. |
| The funnel presented as if its last row were a measurement | **Corrected.** Rows 1–4 are candidate selection from a corpus that is mostly dead on arrival. The measurement is the paired wi-fi / SIM run, where the wi-fi leg is the control. |
