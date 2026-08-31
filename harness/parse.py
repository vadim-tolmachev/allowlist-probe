#!/usr/bin/env python3
"""Парсит подписки, извлекает параметры серверов, сверяет с белыми /24."""
import base64, html, json, os, re, sys, ipaddress, socket
from urllib.parse import urlparse, parse_qs, unquote
from collections import defaultdict

SUBS = "subs"

def maybe_b64(text):
    t = text.strip()
    if "://" in t[:2000]:
        return text
    try:
        pad = t + "=" * (-len(t) % 4)
        dec = base64.b64decode(pad).decode("utf-8", "replace")
        if "://" in dec[:2000]:
            return dec
    except Exception:
        pass
    return text

def parse_uri(u):
    """-> dict или None"""
    try:
        scheme = u.split("://", 1)[0].lower()
        if scheme == "vmess":
            raw = u.split("://", 1)[1].split("#")[0]
            pad = raw + "=" * (-len(raw) % 4)
            j = json.loads(base64.b64decode(pad).decode("utf-8", "replace"))
            return dict(proto="vmess", host=str(j.get("add", "")), port=int(j.get("port", 0) or 0),
                        net=j.get("net", ""), sec=j.get("tls", ""), sni=j.get("sni") or j.get("host", ""),
                        hostheader=j.get("host", ""), path=j.get("path", ""), flow="", pbk="",
                        tag=str(j.get("ps", "")), uri=u)
        p = urlparse(u)
        host = p.hostname or ""
        port = p.port or 0
        q = parse_qs(p.query)
        g = lambda k: (q.get(k, [""])[0] or "")
        return dict(proto=scheme, host=host, port=port, net=g("type") or g("obfs") or "",
                    sec=g("security"), sni=g("sni") or g("peer") or g("host"),
                    hostheader=g("host"), path=unquote(g("path") or g("spx") or ""),
                    flow=g("flow"), pbk=g("pbk"),
                    tag=unquote(p.fragment or ""), uri=u)
    except Exception:
        return None

# --- белые подсети из twl-скана ---
white24 = set()
if os.path.exists("subnets.json"):
    for e in json.load(open("subnets.json")):
        white24.add(e["cidr"].split("/")[0].rsplit(".", 1)[0])
print(f"twl белых /24: {len(white24)}", file=sys.stderr)

# --- cidr-список jsxta (published) ---
jsxta = []
if os.path.exists("jsxta_cidrwhitelist.txt"):
    for ln in open("jsxta_cidrwhitelist.txt"):
        ln = ln.strip()
        if "/" in ln:
            try: jsxta.append(ipaddress.ip_network(ln, strict=False))
            except Exception: pass
print(f"jsxta published CIDR: {len(jsxta)}", file=sys.stderr)

URI_RE = re.compile(r'(?:vless|vmess|trojan|ss|ssr|hysteria2?|hy2|tuic|wireguard|socks|http)://[^\s\'"<>]+')

rows = []
seen = set()
for fn in sorted(os.listdir(SUBS)):
    txt = html.unescape(maybe_b64(open(os.path.join(SUBS, fn), encoding="utf-8", errors="replace").read()))
    for m in URI_RE.finditer(txt):
        d = parse_uri(m.group(0))
        if not d or not d["host"] or not d["port"]:
            continue
        key = (d["proto"], d["host"], d["port"])
        if key in seen:
            rows.append(None)  # счётчик дублей
            continue
        seen.add(key)
        d["src"] = fn.replace(".txt", "")
        rows.append(d)

dups = sum(1 for r in rows if r is None)
rows = [r for r in rows if r]
print(f"уникальных серверов: {len(rows)} (дублей отброшено {dups})", file=sys.stderr)

json.dump(rows, open("parsed.json", "w"), ensure_ascii=False)

# статистика
by_proto = defaultdict(int); by_net = defaultdict(int); by_port = defaultdict(int)
for r in rows:
    by_proto[r["proto"]] += 1
    by_net[f'{r["proto"]}/{r["net"] or "-"}/{r["sec"] or "-"}'] += 1
    by_port[r["port"]] += 1
print("\n== протоколы ==")
for k, v in sorted(by_proto.items(), key=lambda x: -x[1]): print(f"{v:6d}  {k}")
print("\n== топ транспортов ==")
for k, v in sorted(by_net.items(), key=lambda x: -x[1])[:20]: print(f"{v:6d}  {k}")
print("\n== топ портов ==")
for k, v in sorted(by_port.items(), key=lambda x: -x[1])[:15]: print(f"{v:6d}  :{k}")
