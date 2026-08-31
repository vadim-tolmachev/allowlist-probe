# What actually passes: nine commercial operators as ground truth

The funnel in the [README](README.md) starts from public subscription lists and ends at
four working endpoints. This document is the other half of the work, and the stronger
half: instead of scraping public lists, it takes **paid trial subscriptions from
commercial circumvention services that already work under the regime**, decodes them, and
reads off which networks their working entry points sit in.

The oracle is a live handset. A subscriber inside an allowlist region marks which
locations in each competitor's app actually connect; the address behind each working
location is then resolved to a prefix and an ASN from public BGP and whois data.

This inverts the usual measurement problem. Instead of guessing which prefixes are
permitted and testing them, it observes what people who must be right for commercial
reasons have already converged on.

**Services are not named here.** They are commercial operators in a jurisdiction where
providing circumvention carries administrative liability, and identifying them adds
nothing to the result. Hosting providers and ASNs *are* named: they are visible in public
routing data, and they are the finding.

## Results, one operator (Beeline), 3 June 2026

Six subscriptions, each marked on a live SIM in allowlist mode.

| Network | ASN | Example blocks observed | Used by | Passes |
|---|---|---|---|---|
| Selectel | AS49505 (SPb), AS50340 (Msk) | `87.228.101.x`, `46.182.24.x`, `185.91.53.x`, `5.188.115.x` | 3 services | yes |
| Timeweb | AS9123 | `81.200.148.0/22` | 1 | yes |
| Kontel | AS204490 | `46.8.209.x`, `46.8.210.x` | 2 | yes |
| CDNetworks / Global Cloud | AS204720 | `151.236.114.x`, `46.243.232.x`, `37.18.15.x`, `185.141.227.x` | 2 | yes |
| UFO Hosting | AS33993 | `94.131.121.x` | 1 | yes |
| Okay-Telecom | AS199669 | `91.109.201.x` | 1 | yes |
| HLL | AS51115 | `178.248.238.0/24` | 1 | **yes** |
| HLL | AS51115 | `81.161.98.0/24` | 1 | **no** |
| Yandex Cloud | AS200350 | `51.250.x`, `178.154.x`, `158.160.x` | 2 | no, 4 independent confirmations |

## Finding 1: permission is per-prefix, not per-network

This is the part that bears on the open question of how finely the allowlist is drawn,
and unlike a density statistic it does not confound permission with hosting occupancy.

Two networks were observed passing on one prefix and failing on another **within the same
ASN, on the same operator, in the same measurement**:

- HLL AS51115: `178.248.238.0/24` passes, `81.161.98.0/24` does not.
- Timeweb AS9123: `81.200.148.0/22` passes, `185.211.168.0/22` does not.

An ASN is therefore not a unit of permission, and neither is a provider. The practical
consequence for anyone operating under this regime is sharp: changing your address inside
the same provider can silently move you out of the permitted set, so a re-roll has to be
checked against a specific confirmed block rather than against the provider's reputation.

A later run against a different operator's infrastructure reproduced the same shape: a
published-permitted block at HZ Hosting AS59711 (`185.253.116.0/24`), used as a working
location by another service, **failed on a live SIM** while that service's other entry
point passed.

## Finding 2: published allowlists are wrong in both directions, by name

The community CIDR lists that circumvention guides are built on were checked against the
same live oracle.

**False positives** — listed as permitted, do not pass:

- Yandex Cloud blocks (four independent confirmations);
- HLL `81.161.98.0/22`;
- Timeweb `185.211.168.0/22`, which we tested directly and which failed.

**False negatives** — not in any published list, pass anyway:

- CDNetworks / Global Cloud, Selectel and Kontel blocks, all three carrying live
  commercial traffic at the time of measurement.

The error is not noise around a correct list. Whole networks that work are missing, and
whole networks that are listed do not work. A published list is usable as a coarse
pre-filter and as nothing else; the source of truth is a SIM in an affected region.

## Finding 3: at this layer the address decides, not the transport

Across all six subscriptions, what separated a working location from a non-working one was
the prefix, not the protocol or the disguise. Services using identical transports
(VLESS with Reality on port 443) succeeded or failed according to where their entry point
sat.

**This is in tension with a later result of ours** on a different operator in August,
where non-TLS transports on confirmed-permitted prefixes failed while Reality with a
permitted SNI passed. Both observations are recorded, neither is discarded, and the
disagreement is the reason the [README](README.md) states a falsification rule instead of
a conclusion. The two candidate explanations — operators differ, or the regime tightened
between June and August — are themselves the result worth funding, because either one
means no single published recommendation is correct everywhere.

## Finding 4: what mature operators actually buy

Two of the larger services run **their own autonomous systems** with leased address space:
AS216253 announcing 34 /24 blocks, and AS198077. It is tempting to read this as the
solution to the allowlist problem. It is not.

Their own prefixes are foreign — Frankfurt, Amsterdam, New York, Prague, Milan, Bucharest,
Helsinki, Zurich, Warsaw, Riga, London, Istanbul, Tokyo, Fujairah — and serve as **exits**.
The entry point that has to survive the allowlist still sits on a Russian network they do
not own. Owning address space solves address reputation and instant re-rolls; it does not
buy a place in the permitted set, because the permitted set is built from Russian prefixes
that are not for sale (see the README on 700+ floating-IP allocations returning zero hits).

One of these operators states publicly that it will not offer allowlist bypass at all,
because the result is not dependable enough to attach its name to. That is a market signal
worth recording: the segment that can most afford the infrastructure has decided the
problem is not reliably solvable with it.

## Method

Subscriptions are distributed as encrypted links and gated against scraping. Decoding them
required handling two generations of the format (RSA-PKCS1, and RSA plus
ChaCha20-Poly1305) and passing device-identity headers, whose presence rather than
validity is what the gate checks. The specifics are deliberately not reproduced here: they
are someone else's anti-scraping measure, and publishing a working bypass for it serves no
research purpose.

What is reproducible from this document is the part that matters: the mapping from
observed working location to prefix to ASN, using public BGP and whois data, against a
handset oracle in an affected region.

## Limitations

1. **One operator, one date** for the six-subscription run. Beeline, 3 June 2026.
2. **The oracle is a subscriber, not an instrument.** "This location connects" is a
   coarser signal than a controlled probe, and it cannot distinguish a filtered path from
   a dead server.
3. **Selection bias by construction.** These are the networks commercial services had
   already found. Networks that pass but that nobody uses are invisible to this method.
4. **The June result and the August result disagree** on whether transport matters. See
   Finding 3.
5. **Sample sizes are small** and the underlying set moves: see the decay measurement in
   the README.
