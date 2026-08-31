#!/usr/bin/env python3
"""Тест качества: 3 повтора связи + скачивание 2 МБ через каждый сервер."""
import json, os, subprocess, sys, tempfile, time, socket, threading
from concurrent.futures import ThreadPoolExecutor

XRAY = os.path.expanduser("~/bin/xray")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xraygen import config

IN, OUT = sys.argv[1], sys.argv[2]
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
rows = json.load(open(IN))

port_lock = threading.Lock(); next_port = [26000]
def grab_port():
    with port_lock:
        for _ in range(3000):
            p = next_port[0]; next_port[0] += 1
            if next_port[0] > 38000: next_port[0] = 26000
            s = socket.socket()
            try: s.bind(("127.0.0.1", p)); s.close(); return p
            except OSError: s.close()
    raise RuntimeError("нет портов")

def test(r):
    res = dict(r); res.update(hits=0, tries=3, mbps=0.0, ttfb=0, exit_ip="", note="")
    try: cfg = config(r, 0)
    except Exception: return res
    if not cfg: return res
    port = grab_port(); cfg["inbounds"][0]["port"] = port
    fd, path = tempfile.mkstemp(suffix=".json"); os.close(fd); json.dump(cfg, open(path, "w"))
    proc = subprocess.Popen([XRAY, "run", "-c", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            time.sleep(0.1)
            s = socket.socket(); s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0: s.close(); break
            s.close()
        else:
            res["note"] = "не стартовал"; return res
        P = ["--socks5-hostname", f"127.0.0.1:{port}"]
        # 3 повтора на стабильность
        for i in range(3):
            t0 = time.time()
            p = subprocess.run(["curl", "-s", *P, "-m", "12", "https://api.ipify.org"],
                               capture_output=True, text=True)
            ip = (p.stdout or "").strip()
            if p.returncode == 0 and ip.count(".") == 3:
                res["hits"] += 1; res["exit_ip"] = ip
                if i == 0: res["ttfb"] = int((time.time() - t0) * 1000)
            time.sleep(0.3)
        if res["hits"]:
            # скорость: 2 МБ с быстрого источника
            p = subprocess.run(["curl", "-s", "-o", "/dev/null", *P, "-m", "30", "-w", "%{speed_download}",
                                "https://speed.cloudflare.com/__down?bytes=2000000"],
                               capture_output=True, text=True)
            try: res["mbps"] = round(float(p.stdout.strip()) * 8 / 1e6, 2)
            except Exception: pass
            # доступен ли реально заблокированный в РФ ресурс
            p = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", *P, "-m", "12",
                                "https://www.youtube.com/"], capture_output=True, text=True)
            res["note"] = f"yt={p.stdout.strip()}"
    finally:
        proc.terminate()
        try: proc.wait(timeout=3)
        except Exception: proc.kill()
        try: os.unlink(path)
        except Exception: pass
    return res

out = []
done = [0]
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for r in ex.map(test, rows):
        out.append(r); done[0] += 1
        if done[0] % 25 == 0: print(f"{done[0]}/{len(rows)}", file=sys.stderr, flush=True)
json.dump(out, open(OUT, "w"), ensure_ascii=False)
good = [r for r in out if r["hits"] == 3]
print(f"\nстабильных (3/3): {len(good)} из {len(out)}")
for r in sorted(good, key=lambda x: -x["mbps"]):
    print(f"{r['mbps']:7.2f} Mbps  {r['ttfb']:5d}ms  {r['ip']}:{r['port']:<6} "
          f"{r['proto']}/{r['net'] or '-'}/{r['sec'] or 'none':<7} host={(r['hostheader'] or r['sni'] or '-')[:24]:<24} "
          f"exit={r['exit_ip']:<15} {r['note']}")
