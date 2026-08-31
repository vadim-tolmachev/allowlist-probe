#!/usr/bin/env python3
"""Строит xray-конфиг (socks inbound -> один outbound) из распарсенного URI."""
import json, base64
from urllib.parse import urlparse, parse_qs, unquote

def _stream(d, q):
    net = (d.get("net") or "tcp").lower()
    if net in ("raw", ""): net = "tcp"
    if net == "h2": net = "http"
    sec = (d.get("sec") or "none").lower()
    if sec in ("", "none"): sec = "none"
    st = {"network": net, "security": sec}

    sni = d.get("sni") or d.get("hostheader") or d.get("host")
    fp = (q.get("fp", [""])[0] or "chrome")
    alpn = q.get("alpn", [""])[0]

    if sec == "reality":
        st["realitySettings"] = {
            "serverName": sni, "fingerprint": fp,
            "publicKey": d.get("pbk", ""), "shortId": q.get("sid", [""])[0],
            "spiderX": q.get("spx", ["/"])[0] or "/",
        }
    elif sec == "tls":
        t = {"serverName": sni, "fingerprint": fp}
        if alpn: t["alpn"] = alpn.split(",")
        st["tlsSettings"] = t

    if net == "ws":
        ws = {"path": d.get("path") or "/"}
        hh = d.get("hostheader") or sni
        if hh: ws["headers"] = {"Host": hh}
        st["wsSettings"] = ws
    elif net == "grpc":
        st["grpcSettings"] = {"serviceName": q.get("serviceName", [""])[0] or d.get("path", "").strip("/"),
                              "multiMode": q.get("mode", [""])[0] == "multi"}
    elif net == "xhttp":
        xh = {"path": d.get("path") or "/", "mode": q.get("mode", ["auto"])[0] or "auto"}
        hh = d.get("hostheader")
        if hh: xh["host"] = hh
        st["xhttpSettings"] = xh
    elif net == "http":
        h = {"path": d.get("path") or "/"}
        hh = d.get("hostheader") or sni
        if hh: h["host"] = [hh]
        st["httpSettings"] = h
    elif net == "tcp":
        ht = q.get("headerType", [""])[0]
        if ht == "http":
            hh = d.get("hostheader") or sni
            st["tcpSettings"] = {"header": {"type": "http",
                                            "request": {"headers": {"Host": [hh] if hh else ["www.bing.com"]}}}}
    return st

def outbound(d):
    u = d["uri"]
    proto = d["proto"]
    q = parse_qs(urlparse(u).query) if proto != "vmess" else {}

    if proto == "vless":
        uid = urlparse(u).username or ""
        vnext = {"address": d["host"], "port": int(d["port"]),
                 "users": [{"id": unquote(uid), "encryption": q.get("encryption", ["none"])[0] or "none"}]}
        flow = d.get("flow") or ""
        if flow: vnext["users"][0]["flow"] = flow
        return {"protocol": "vless", "settings": {"vnext": [vnext]},
                "streamSettings": _stream(d, q)}

    if proto == "vmess":
        raw = u.split("://", 1)[1].split("#")[0]
        j = json.loads(base64.b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8", "replace"))
        d2 = dict(d); d2["sec"] = "tls" if str(j.get("tls", "")) in ("tls", "reality") else "none"
        return {"protocol": "vmess",
                "settings": {"vnext": [{"address": d["host"], "port": int(d["port"]),
                                        "users": [{"id": j.get("id"), "alterId": int(j.get("aid", 0) or 0),
                                                   "security": j.get("scy", "auto")}]}]},
                "streamSettings": _stream(d2, {})}

    if proto == "trojan":
        pw = unquote(urlparse(u).username or "")
        return {"protocol": "trojan",
                "settings": {"servers": [{"address": d["host"], "port": int(d["port"]), "password": pw}]},
                "streamSettings": _stream(d, q)}

    if proto in ("ss", "shadowsocks"):
        p = urlparse(u)
        userinfo = p.username or ""
        if p.password:
            method, pw = unquote(userinfo), unquote(p.password)
        else:
            try:
                dec = base64.b64decode(userinfo + "=" * (-len(userinfo) % 4)).decode("utf-8", "replace")
                method, pw = dec.split(":", 1)
            except Exception:
                return None
        return {"protocol": "shadowsocks",
                "settings": {"servers": [{"address": d["host"], "port": int(d["port"]),
                                          "method": method, "password": pw}]},
                "streamSettings": _stream(d, q)}
    return None

def config(d, socks_port):
    ob = outbound(d)
    if not ob: return None
    return {"log": {"loglevel": "error"},
            "inbounds": [{"listen": "127.0.0.1", "port": socks_port, "protocol": "socks",
                          "settings": {"udp": False}}],
            "outbounds": [ob]}
