#!/usr/bin/env python3
"""Живой прогон: поднимает xray на каждый конфиг, тянет трафик через socks."""
import json, os, subprocess, sys, tempfile, time, socket, threading
from concurrent.futures import ThreadPoolExecutor

XRAY = os.path.expanduser("~/bin/xray")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xraygen import config

IN = sys.argv[1] if len(sys.argv) > 1 else "candidates.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "probed.json"
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 24
UPSTREAM = os.environ.get("UPSTREAM", "")   # "127.0.0.1:1081" -> цепочка через RU-туннель

rows = json.load(open(IN))
port_lock = threading.Lock()
next_port = [21000]

def grab_port():
    with port_lock:
        for _ in range(2000):
            p = next_port[0]; next_port[0] += 1
            if next_port[0] > 32000: next_port[0] = 21000
            s = socket.socket()
            try:
                s.bind(("127.0.0.1", p)); s.close(); return p
            except OSError:
                s.close()
    raise RuntimeError("нет портов")

def probe(r):
    res = dict(r); res["ok"] = False; res["err"] = ""; res["exit_ip"] = ""; res["ms"] = 0
    cfg = None
    try:
        cfg = config(r, 0)
    except Exception as e:
        res["err"] = f"cfg:{e}"; return res
    if not cfg:
        res["err"] = "cfg:unsupported"; return res

    if UPSTREAM:
        ha, hp = UPSTREAM.split(":")
        cfg["outbounds"][0]["proxySettings"] = {"tag": "up"}
        cfg["outbounds"].append({"tag": "up", "protocol": "socks",
                                 "settings": {"servers": [{"address": ha, "port": int(hp)}]}})
    port = grab_port()
    cfg["inbounds"][0]["port"] = port
    fd, path = tempfile.mkstemp(suffix=".json"); os.close(fd)
    json.dump(cfg, open(path, "w"))
    proc = subprocess.Popen([XRAY, "run", "-c", path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        # ждём, пока порт откроется
        for _ in range(60):
            time.sleep(0.1)
            s = socket.socket(); s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                s.close(); break
            s.close()
        else:
            res["err"] = "xray:no-listen"; return res

        t0 = time.time()
        p = subprocess.run(["curl", "-s", "--socks5-hostname", f"127.0.0.1:{port}",
                            "-m", "14", "https://api.ipify.org"],
                           capture_output=True, text=True)
        ip = (p.stdout or "").strip()
        if p.returncode == 0 and ip and len(ip) < 46 and ip.count(".") == 3:
            res["ok"] = True; res["exit_ip"] = ip; res["ms"] = int((time.time() - t0) * 1000)
        else:
            res["err"] = f"curl:{p.returncode}"
    except Exception as e:
        res["err"] = f"run:{e}"
    finally:
        proc.terminate()
        try: proc.wait(timeout=3)
        except Exception: proc.kill()
        try: os.unlink(path)
        except Exception: pass
    return res

done = [0]
lock = threading.Lock()
out = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for r in ex.map(probe, rows):
        out.append(r)
        with lock:
            done[0] += 1
            if done[0] % 50 == 0:
                alive = sum(1 for x in out if x["ok"])
                print(f"{done[0]}/{len(rows)}  живых {alive}", file=sys.stderr, flush=True)

json.dump(out, open(OUT, "w"), ensure_ascii=False)
alive = [r for r in out if r["ok"]]
print(f"\nЖИВЫХ: {len(alive)}/{len(out)}")
from collections import Counter
print("\n== причины отказа ==")
for k, v in Counter(r["err"].split(":")[0] + ":" + r["err"].split(":")[-1][:20] for r in out if not r["ok"]).most_common(10):
    print(f"{v:5d}  {k}")
