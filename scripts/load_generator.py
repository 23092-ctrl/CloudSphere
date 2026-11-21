import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

TARGET_URL = "http://localhost:8088/api/info"

def make_request(idx):
    start = time.time()
    try:
        req = urllib.request.Request(TARGET_URL, headers={"User-Agent": "LoadGen/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read()
            duration = round((time.time() - start) * 1000, 2)
            return (True, resp.status, duration)
    except Exception as e:
        return (False, str(e), 0)

def main():
    total_reqs = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"🚀 Lancement de {total_reqs} requêtes avec {workers} threads...")
    start_time = time.time()
    success = 0
    failed = 0
    latencies = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(make_request, i) for i in range(total_reqs)]
        for f in futures:
            ok, status, lat = f.result()
            if ok and status == 200:
                success += 1
                latencies.append(lat)
            else:
                failed += 1

    total_time = round(time.time() - start_time, 2)
    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0
    rps = round(success / total_time, 1) if total_time > 0 else 0

    print(f"✔ Terminé en {total_time}s | Succès: {success} | Échecs: {failed} | Débit: {rps} req/s | Latence moyenne: {avg_lat}ms")

if __name__ == "__main__":
    main()
