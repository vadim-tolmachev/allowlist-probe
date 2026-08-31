# Data

Per-stage artifacts. Every file is a JSON array of records.

## Redaction

Removed from every record before publication:

- `uri` — the full subscription URI, which carries the user UUID and therefore the
  credential itself;
- `pbk` — Reality public key;
- `exit_ip` — the egress address observed by the probe target;
- any UUID appearing inside a `path`, replaced by `<redacted-uuid>`: for some WebSocket
  endpoints the path itself is the credential.

The corpus came from publicly posted subscriptions, but republishing thousands of working
configurations in aggregated, indexed form is a different act from the original posting.
What remains reproduces every published figure and does not constitute a usable
configuration.

30 endpoints belonging to a service operated by the author were removed from stage 1.
None of them survived to stage 2, so no downstream count changes.

## Record schema

| Field | Meaning |
|---|---|
| `proto` | `vless`, `vmess`, `trojan`, `ss`, ... |
| `host` | hostname or address as published |
| `ip` | resolved address |
| `port` | destination port |
| `net` | transport: `tcp`, `raw`, `ws`, `grpc`, `xhttp` |
| `sec` | security layer: `reality`, `tls`, `none` |
| `sni` | SNI, or `Host` header for plain WebSocket |
| `hostheader`, `path`, `flow` | transport parameters |
| `tag` | label as given by the subscription author |
| `src` | subscription the record came from |
| `twl_white` | address falls inside a /24 confirmed permitted by the scan |
| `pub_white` | address falls inside the community CIDR allowlist |
| `ok` | traffic passed (HTTP 200 through the tunnel) |
| `err` | failure reason where recorded |
| `ms` | latency |
| `hits` / `tries` | stability re-measurement (stage 4 only) |
| `mbps` | throughput, measured from the datacentre side (stage 4 only) |

## Files

| File | Records | Stage |
|---|---|---|
| `stage1_parsed.json` | 6,146 | parsed and de-duplicated endpoints |
| `stage2_tcp_open.json` | 2,044 | TCP port open |
| `stage3_traffic.json` | 2,044 | probed with a real proxy client; 314 have `ok == true` |
| `stage4_stable.json` | 56 | re-measured; 38 have `hits == 3` |
| `stage5_sim_candidates.json` | 60 | automated Reality run; 4 have `ok == true` |
| `control.json` | 200 | control group without allowlist pre-selection; 4 have `ok == true` |
| `twl_scan_subnets.json` | 13,691 | permitted /24 blocks with unique responsive-host counts |
| `allowlist_comparison.json` | — | community list versus scan |

`twl_scan_subnets.json` is derived from `openlibrecommunity/twl`, snapshot of
10 July 2026, and is included so the comparison is reproducible without re-downloading a
repository that is no longer maintained. Credit for the sweep belongs there.
