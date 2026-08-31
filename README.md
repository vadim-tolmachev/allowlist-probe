# allowlist-probe

Measurements of allowlist-mode filtering in Russian mobile networks: a staged pipeline
that takes candidate circumvention endpoints from published sources down to what actually
carries traffic on a handset inside the regime, plus the raw per-stage artifacts.

Allowlist mode (`default-deny`) is a filtering posture in which a mobile operator permits
a narrow set of destination prefixes and drops everything else, rather than blocking a
blacklist. It is applied per region and per operator, and it is not the same thing as a
shutdown: the region is not disconnected, it has a narrow permitted corridor.

This repository exists because almost every published claim about which endpoints survive
that corridor is either untested or wrong, including several of my own earlier ones. The
funnel below is the short version of why.

**Start with [GROUND-TRUTH.md](GROUND-TRUTH.md) if you only read one thing.** It takes the
opposite approach to the funnel below: rather than testing candidates from public lists,
it decodes paid subscriptions from commercial services that already work under the regime
and reads off which networks their entry points sit in. It contains the strongest result
here, which is that permission is granted per prefix and not per network, observed as one
ASN passing on one block and failing on another in the same measurement. It also contains
the most counterintuitive one: under this regime a commercial service removed Reality and
SNI spoofing in favour of an honest certificate on its own domain, weakening its
resistance to active probing, and started passing on an operator that had been rejecting
it from the same prefix.

## The funnel: how 6,176 candidates became 38 worth testing

**This table is candidate selection, not a result.** The corpus was scraped from free
public subscriptions, and such corpora are mostly dead on arrival: entries are withdrawn,
overloaded, attacked or simply abandoned. Separating "this endpoint is broken" from "the
regime blocked this endpoint" is the entire methodological problem, and it is solved in
the next section, not in this one.

| Stage | Survived | What it means |
|---|---|---|
| Unique endpoints parsed from 19 public subscriptions | 6,176 | candidate corpus |
| TCP port open | 2,044 | reachable from a server |
| Carries traffic (HTTP 200 through the tunnel) | 314 | a working proxy, measured from a datacentre |
| Stable 3 of 3 on re-measurement | 38 | not a one-off success |

A TCP handshake overstates working endpoints by a factor of about six (2,044 → 314). Any
tool, list or guide validated by port checks is describing something other than what a
subscriber experiences. The 38 survivors are the input to the handset test below.

**The corpus is a snapshot, and it rots fast.** Every figure above is from the run of
**22 August 2026**. The candidate corpus was scraped from public subscription lists, and
those lists are mostly stale on the day they are published. Re-probing on **31 August
2026**, nine days later: of the 314 endpoints that carried traffic, **169 still accept a
TCP connection, 46% are gone**. TCP acceptance is itself a sixfold overestimate of working
(2,044 → 314 above), so the number still carrying traffic today is far smaller.

This is not a caveat, it is the result that matters most for anyone building on data like
this. A published list of endpoints has a half-life measured in days, and a measurement
run once is describing a network that no longer exists. The same applies to the prefix
allowlist: see endpoint 29 below.

**Control group.** 200 configurations drawn without allowlist pre-selection were run
through the same pipeline: 4 carried traffic (2.0%), against 314 of 6,176 (5.1%) for the
pre-selected corpus. Pre-selection roughly doubles the yield at that stage. The control
group was never carried to a handset, so there is no baseline for the last row. That is a
gap, not an omission: see [Limitations](#limitations).

## The handset test (22 August 2026)

This is the part that cannot be done remotely, it is the smallest sample here, and it is
the only measurement in this repository that describes the regime rather than the corpus.

**The design is paired, and the pairing is the whole argument.** The same 38
configurations, in the same client profile, on the same handset, in one sitting, were run
twice: once over unrestricted wi-fi, then over a SIM in a region with allowlist mode
active. **28 of 38 answered over wi-fi. 4 of those 28 passed over the SIM.**

The wi-fi leg is the control, and it is what makes the number mean anything. An endpoint
that is dead, overloaded, withdrawn by its operator or under attack fails over wi-fi too,
and is therefore already excluded before the SIM leg runs. What reaches the SIM leg is 28
endpoints demonstrably carrying traffic minutes earlier, over the same device and the same
client. Of those, the regime admitted four. The ten that failed on wi-fi are counted as
broken, not as blocked.

This is also the answer to the obvious objection that free public endpoints die for a
hundred reasons that have nothing to do with censorship. They do, and the control removes
them from the denominator.

| # | Transport | Permitted SNI / Host | Latency on SIM |
|---|---|---|---|
| 03 | VLESS gRPC over Reality | `vk.com` | 59 ms |
| 29 | VLESS raw over Reality | `max.ru` | 66 ms |
| 06 | VLESS TCP over Reality | `max.ru` | 109 ms |
| 07 | VLESS raw over Reality | `hd.kinopoisk.ru` | 128 ms |

What failed, with live servers on confirmed-permitted /24 blocks:

- **plain WebSocket with a permitted `Host:` header: 0 of 8.** This was the largest
  cluster in the corpus (245 configurations on ports 2200 and 4100, `Host: rzd.ru` or
  `Host: live.ok.ru`, no TLS at all). It is also the technique most often recommended in
  community repositories.
- **bare VLESS without TLS, and Shadowsocks: 0 of 3**, including the fastest endpoint in
  the whole corpus at 62 Mbit/s.
- **XHTTP over Reality: 0 of 2**, despite permitted `dest` values.

**Working hypothesis.** On port 443 the middlebox admits only a valid TLS ClientHello
carrying a permitted SNI, and drops non-TLS traffic on 443 as well as everything on
non-standard ports, regardless of destination prefix. A permitted IP address is necessary
but not sufficient.

**What this evidence does not support.** All four successes were Reality with a permitted
SNI, but the converse does not hold: other Reality configurations with permitted SNI in
the same run also failed, and the reasons were not isolated. The claim here is
"everything that passed was of this type", not "everything of this type passes". Earlier
drafts of this work stated the latter. It was wrong.

**A permitted address is not stable either.** Endpoint 29 passed although its /24 is
absent from the scan used for pre-selection. That scan was taken on 10 July; the test was
run on 22 August. Six weeks were enough for the permitted set to grow past the snapshot,
which is the strongest argument in this repository for continuous rather than one-off
measurement.

## The allowlist itself

The prefix-level allowlist data here is **not mine**. It comes from
[`openlibrecommunity/twl`](https://github.com/openlibrecommunity/twl), a public masscan
sweep of Russian address space performed through a mobile base station in allowlist mode:
if TCP/443 answers through the cell, the packet crossed L3, so its /24 is permitted. The
snapshot re-analysed here is from **10 July 2026**, one operator (MegaFon), one region.
The upstream project stopped publishing data after that date and its README now points to
a successor repository, `openlibrecommunity/rewl`, which has been dormant since 6 August.

My contribution is the re-analysis and everything downstream of it, not the sweep.

**Scale.** 13,691 permitted /24 blocks containing 108,564 unique responsive addresses.

**Published lists miss most of it.** Cross-checking one widely used community CIDR
allowlist (2,114 entries, 1,772 unique /24 blocks) against the scan: 912 confirmed
permitted, while the scan contains 12,779 permitted blocks that the list does not. A
developer building on the published list is working from a small and unrepresentative
slice.

**Responsive-host density, and why it proves less than it looks like.** Median density of
responsive hosts inside a permitted /24 is 0.39%; 91.3% of blocks are at or below 5%; 167
blocks are at or above 50%, with a maximum of 98.4%.

It is tempting to read low density as evidence that permission is granted more finely than
a whole /24. **It is not evidence of that.** An address that does not answer on port 443
usually has nothing listening on port 443; responsiveness measures what is hosted, not
what is permitted. The statistic is reported here because it describes the dataset, and
because anyone re-using this scan should know that it cannot separate those two
explanations. Testing sub-/24 granularity requires knocking on a silent neighbour of a
responsive address from inside the regime, which is future work.

## Negative results and measurement traps

Recorded because they cost time and are not written down anywhere else.

- **DNS tunnelling through the mandatory state resolver does not give usable throughput.**
  The resolver at `195.208.4.1` stays reachable under the regime on both operators tested,
  because closing it would break resolution for the permitted sites themselves. A tunnel
  establishes, but effective MTU is around 134 bytes, payload was empty on every run, and
  the transport dropped in half of them. This demonstrates that a corridor exists at that
  layer. It is not a circumvention channel.
- **Renting a permitted address does not work.** More than 700 floating-IP allocations
  across five regions of one cloud provider and three availability zones of another
  produced zero addresses inside a permitted /24, although the pools repeatedly returned
  neighbouring subnets.
- **`allowInsecure` was removed in Xray 26.3.27**, which silently broke 270 of 2,044
  otherwise-live configurations. No error is raised; the connection simply fails.
- **Chaining through `proxySettings` breaks Reality and XTLS Vision.**
- **HTML-escaped subscription payloads** silently turn a Reality configuration into plain
  VLESS, with no indication that anything changed.
- **Subscriptions advertised as "whitelist-ready" are mostly dead.** The largest in the
  sample listed 1,046 servers, of which 25 were alive.
- **Observation point does not bias the remote stage.** The same candidate set probed
  through a Russian relay and a Dutch host returned 326 versus 327 open ports.
- **A service's own location labels are not evidence of location.** In one commercial
  subscription every endpoint flagged as European was the same Russian address as its
  domestic neighbour on a different port; in another, endpoints advertised as Mexican,
  French, Canadian and Polish resolved into a single Russian hosting provider. Anyone
  deriving a geographic distribution from scraped subscriptions is measuring marketing.

## Limitations

Stated in full, because every one of them is load-bearing.

1. **The handset oracle is single.** One phone, one operator, one region, one day. The
   central hypothesis rests on 4 successes. This is a pilot, not a measurement.
2. **The prefix scan is third-party, single-operator, single-date**, and no longer
   updated. Every figure derived from it inherits those limits, including the 912 and
   12,779 above.
3. **Allowlists are regional and per-operator.** A MegaFon sweep is not ground truth for
   Tele2. Results here should not be generalised to the country.
4. **An earlier run on a different operator pointed the other way**, suggesting L3
   filtering dominated and SNI was effectively unchecked. Either operators differ or the
   regime tightened between June and August. Both are results; neither is established.
5. **No control group reached a handset**, so the last row of the funnel has no baseline.
6. **Throughput figures are from the datacentre side**, not from the handset.

**Falsification rule, fixed in advance.** The hypothesis is refuted if non-TLS transport
on a permitted prefix passes in two or more independent runs, where independent means a
different operator or a different region. Confirmation requires the opposite across at
least four operators and three regions, three repetitions each. The verdict will be
published either way, with the raw artifacts, and this rule will not be changed after the
fact.

## Ethics and what is not published

- **No user traffic, and no user data of any kind, is present in this repository or in any
  measurement behind it.** Every probe ran on hardware and SIM cards under my own control.
  No third party's connection was used as an experimental subject.
- **Credentials are stripped.** The corpus was assembled from publicly posted
  subscriptions, but republishing 6,176 working configurations in aggregated, indexed form
  is a different act from the original posting. The `uri` field, containing user UUIDs, and
  the Reality public key and short ID have been removed from every record. What remains
  reproduces every number in this README and does not hand anyone a working tunnel.
- **My own infrastructure is excluded.** 30 endpoints belonging to infrastructure I control were
  removed from stage 1 before publication, which is why the published artifact holds 6,146
  records rather than 6,176. None of them survived past stage 1, so no downstream figure
  changes.
- Operator and vendor names are given where they are already public and load-bearing, and
  omitted where naming them would identify a commercial counterparty without adding to the
  result.

## Repository layout

```
GROUND-TRUTH.md   what nine commercial operators converged on, and why lists are wrong
harness/    the five pipeline stages, as run
data/       per-stage artifacts, redacted as described above
docs/       provenance of every number in this README
```

See [`docs/numbers.md`](docs/numbers.md) for the file and computation behind each figure,
and [`data/README.md`](data/README.md) for record schemas.

## Reproducing

The remote stages need only a host with outbound access. The handset stage needs a SIM in
a region with the regime active, and cannot be reproduced from outside Russia.

```
python3 harness/parse.py      # subscriptions  -> parsed endpoints
python3 harness/resolve.py    # hostnames      -> addresses
python3 harness/probe.py      # addresses      -> TCP reachability, then live traffic
python3 harness/speed.py      # survivors      -> throughput and stability
python3 harness/xraygen.py    # survivors      -> client profile for handset testing
```

## Author

Vadim Tolmachev, independent researcher in Russia. This work comes out of operational
experience with circumvention transports under the regime it describes, which is why the
handset stage exists at all. Corrections are welcome, particularly to the handset results:
they are the weakest part of this work and the part most worth attacking.

## License

MIT. See [LICENSE](LICENSE).
