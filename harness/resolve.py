#!/usr/bin/env python3
"""Резолв хостов -> IP, пересечение с белыми /24 из twl-скана."""
import json, socket, ipaddress, sys
from concurrent.futures import ThreadPoolExecutor

rows = json.load(open("parsed.json"))
white24 = set()
for e in json.load(open("subnets.json")):
    white24.add(e["cidr"].split("/")[0].rsplit(".", 1)[0])

jsxta = []
for ln in open("jsxta_cidrwhitelist.txt"):
    ln = ln.strip()
    if "/" in ln:
        try: jsxta.append(ipaddress.ip_network(ln, strict=False))
        except Exception: pass

def is_ip(h):
    try: ipaddress.ip_address(h); return True
    except Exception: return False

hosts = sorted({r["host"] for r in rows if not is_ip(r["host"])})
print(f"доменов к резолву: {len(hosts)}", file=sys.stderr)

def res(h):
    try:
        socket.setdefaulttimeout(4)
        return h, socket.gethostbyname(h)
    except Exception:
        return h, None

cache = {}
with ThreadPoolExecutor(max_workers=60) as ex:
    for h, ip in ex.map(res, hosts):
        cache[h] = ip
ok = sum(1 for v in cache.values() if v)
print(f"отрезолвилось: {ok}/{len(hosts)}", file=sys.stderr)

def in_jsxta(ip):
    a = ipaddress.ip_address(ip)
    return any(a in n for n in jsxta)

for r in rows:
    ip = r["host"] if is_ip(r["host"]) else cache.get(r["host"])
    r["ip"] = ip
    if ip and ":" not in ip:
        r["twl_white"] = ip.rsplit(".", 1)[0] in white24
        r["pub_white"] = in_jsxta(ip)
    else:
        r["twl_white"] = False
        r["pub_white"] = False

json.dump(rows, open("resolved.json", "w"), ensure_ascii=False)

live = [r for r in rows if r["ip"]]
twl = [r for r in live if r["twl_white"]]
pub = [r for r in live if r["pub_white"]]
both = [r for r in live if r["twl_white"] and r["pub_white"]]
print(f"\nс IP: {len(live)}")
print(f"в белом /24 по эмпирическому скану twl: {len(twl)}")
print(f"в published-списке (jsxta): {len(pub)}")
print(f"в обоих: {len(both)}")

# whitelist-совместимые: белый IP + TCP-протокол + порт 443/80
def wl_ready(r):
    return (r["twl_white"] and r["port"] in (443, 80)
            and r["proto"] in ("vless", "trojan", "ss", "vmess"))
ready = [r for r in live if wl_ready(r)]
print(f"\nWL-годных (белый /24 + TCP + :443/:80): {len(ready)}")
json.dump(ready, open("candidates.json", "w"), ensure_ascii=False)

from collections import Counter
print("\n== источники WL-годных ==")
for k, v in Counter(r["src"] for r in ready).most_common(): print(f"{v:5d}  {k}")
print("\n== транспорты WL-годных ==")
for k, v in Counter(f'{r["proto"]}/{r["net"] or "-"}/{r["sec"] or "-"}' for r in ready).most_common(): print(f"{v:5d}  {k}")
print("\n== топ /16 WL-годных ==")
for k, v in Counter(".".join(r["ip"].split(".")[:2]) for r in ready).most_common(15): print(f"{v:5d}  {k}.x.x")
