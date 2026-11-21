import os
import socket
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from flask import Flask, request, jsonify, render_template_string
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# System identity
HOSTNAME = socket.gethostname()
NODE_NAME = os.getenv("NODE_NAME", HOSTNAME)
NODE_COLOR = os.getenv("NODE_COLOR", "#3b82f6")

# Environment configurations
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "cloud_db")
DB_USER = os.getenv("DB_USER", "cloud_user")
DB_PASS = os.getenv("DB_PASSWORD", "cloud_secret_pass")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Prometheus Metrics
REQUESTS_TOTAL = Counter(
    "cloud_http_requests_total",
    "Total HTTP requests handled by Cloud nodes",
    ["node", "endpoint", "method", "status"]
)
REQUEST_DURATION = Histogram(
    "cloud_http_request_duration_seconds",
    "Latency of HTTP requests in seconds",
    ["node", "endpoint"]
)
ACTIVE_CONNECTIONS = Gauge(
    "cloud_active_connections",
    "Number of active connections currently handled",
    ["node"]
)
CACHE_OPERATIONS = Counter(
    "cloud_cache_operations_total",
    "Total cache lookups",
    ["node", "result"]
)

def get_redis_client():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_timeout=2)
        r.ping()
        return r
    except Exception as e:
        return None

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=3
        )
        return conn
    except Exception as e:
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cloud_records (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        source_node VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("SELECT COUNT(*) FROM cloud_records;")
                count = cur.fetchone()[0]
                if count == 0:
                    cur.execute("""
                        INSERT INTO cloud_records (title, source_node) VALUES 
                        ('Initialisation du cluster Cloud', 'provisioning-agent'),
                        ('Configuration du Load Balancer Nginx', 'nginx-proxy'),
                        ('Mise en service du Cache Redis', 'redis-inmemory');
                    """)
                conn.commit()
        except Exception as e:
            conn.rollback()
        finally:
            conn.close()

# Try initial DB setup on launch
try:
    init_db()
except:
    pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudSphere - Plateforme Haute Disponibilité</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary-node: {{ node_color }};
        }
        body {
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .navbar-custom {
            background: #1e293b;
            border-bottom: 2px solid #334155;
        }
        .card-custom {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s;
        }
        .card-custom:hover {
            transform: translateY(-2px);
        }
        .node-badge {
            background-color: var(--primary-node);
            color: #ffffff;
            font-size: 1.15rem;
            padding: 8px 16px;
            border-radius: 30px;
            font-weight: 700;
            display: inline-block;
            box-shadow: 0 0 15px var(--primary-node);
        }
        .status-pill {
            font-size: 0.85rem;
            padding: 4px 10px;
            border-radius: 20px;
        }
        .status-ok { background-color: #059669; color: #fff; }
        .status-err { background-color: #dc2626; color: #fff; }
        .btn-action {
            background: #2563eb;
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 8px;
            font-weight: 600;
        }
        .btn-action:hover {
            background: #1d4ed8;
            color: white;
        }
        .terminal-box {
            background: #020617;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 12px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            color: #38bdf8;
            max-height: 220px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-custom py-3">
        <div class="container">
            <span class="navbar-brand text-light fw-bold">
                <i class="fa-solid fa-cloud text-primary me-2"></i> CloudSphere
                <small class="text-secondary fw-normal fs-6">| Projet Cloud & Virtualisation</small>
            </span>
            <div class="d-flex align-items-center gap-3">
                <a href="/metrics" target="_blank" class="btn btn-outline-info btn-sm">
                    <i class="fa-solid fa-chart-line me-1"></i> Prometheus Metrics
                </a>
                <a href="http://localhost:3000" target="_blank" class="btn btn-outline-warning btn-sm">
                    <i class="fa-solid fa-gauge me-1"></i> Grafana Dashboard
                </a>
            </div>
        </div>
    </nav>

    <div class="container my-4">
        <!-- Hero Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card-custom p-4 text-center">
                    <h5 class="text-uppercase text-secondary tracking-wider">Requête traitée dynamiquement par le nœud :</h5>
                    <div class="my-2">
                        <span class="node-badge">
                            <i class="fa-solid fa-server me-2"></i> {{ node_name }}
                        </span>
                    </div>
                    <p class="text-muted mb-0">
                        <small>IP Conteneur : <strong>{{ container_ip }}</strong> | Hostname ID : <strong>{{ hostname }}</strong></small>
                    </p>
                    <div class="mt-3">
                        <button onclick="location.reload()" class="btn btn-action">
                            <i class="fa-solid fa-arrows-rotate me-1"></i> Rafraîchir (Tester le Load Balancing)
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Infrastructure Status Grid -->
        <div class="row g-4 mb-4">
            <!-- Nginx Ingress -->
            <div class="col-md-3">
                <div class="card-custom p-3 h-100">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="text-light"><i class="fa-solid fa-route text-info me-2"></i>Load Balancer</h6>
                        <span class="status-pill status-ok">Nginx Active</span>
                    </div>
                    <p class="small text-secondary mb-1">Algorithme : <strong>Round-Robin</strong></p>
                    <p class="small text-secondary mb-0">Port d'entrée : <strong>8088 / 80</strong></p>
                </div>
            </div>

            <!-- Backend Replicas -->
            <div class="col-md-3">
                <div class="card-custom p-3 h-100">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="text-light"><i class="fa-solid fa-cubes text-primary me-2"></i>Pool Applicatif</h6>
                        <span class="status-pill status-ok">3 Réplicas</span>
                    </div>
                    <p class="small text-secondary mb-1">Architecture : <strong>Microservices HA</strong></p>
                    <p class="small text-secondary mb-0">Worker : <strong>Gunicorn / Python</strong></p>
                </div>
            </div>

            <!-- Database Tier -->
            <div class="col-md-3">
                <div class="card-custom p-3 h-100">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="text-light"><i class="fa-solid fa-database text-warning me-2"></i>Base de Données</h6>
                        <span class="status-pill {% if db_status %}status-ok{% else %}status-err{% endif %}">
                            {% if db_status %}PostgreSQL OK{% else %}Erreur DB{% endif %}
                        </span>
                    </div>
                    <p class="small text-secondary mb-1">Stockage : <strong>Volume Persistant</strong></p>
                    <p class="small text-secondary mb-0">Entrées enregistrées : <strong>{{ db_count }}</strong></p>
                </div>
            </div>

            <!-- In-Memory Cache -->
            <div class="col-md-3">
                <div class="card-custom p-3 h-100">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="text-light"><i class="fa-solid fa-bolt text-danger me-2"></i>Cache Distribué</h6>
                        <span class="status-pill {% if redis_status %}status-ok{% else %}status-err{% endif %}">
                            {% if redis_status %}Redis OK{% else %}Erreur Redis{% endif %}
                        </span>
                    </div>
                    <p class="small text-secondary mb-1">Réseau : <strong>SDN cloud_net</strong></p>
                    <p class="small text-secondary mb-0">Compteur de hits : <strong>{{ cache_hits }}</strong></p>
                </div>
            </div>
        </div>

        <!-- Interactive Cloud Operations -->
        <div class="row g-4 mb-4">
            <!-- Persistence Demo -->
            <div class="col-lg-6">
                <div class="card-custom p-4 h-100">
                    <h5 class="text-light mb-3">
                        <i class="fa-solid fa-floppy-disk text-success me-2"></i>Test de Persistance Cloud (PostgreSQL)
                    </h5>
                    <p class="small text-secondary">
                        Ajoutez une donnée depuis ce nœud. Elle sera immédiatement persistée dans le volume Docker et accessible par tous les réplicas.
                    </p>
                    <div class="input-group mb-3">
                        <input type="text" id="recordTitle" class="form-control bg-dark text-light border-secondary" placeholder="Titre de la tâche ou ressource cloud...">
                        <button class="btn btn-success" type="button" onclick="addRecord()">
                            <i class="fa-solid fa-plus me-1"></i> Persister
                        </button>
                    </div>
                    <div class="terminal-box" id="dbRecordsBox">
                        Chargement des données persistées...
                    </div>
                </div>
            </div>

            <!-- Caching & Latency Demo -->
            <div class="col-lg-6">
                <div class="card-custom p-4 h-100">
                    <h5 class="text-light mb-3">
                        <i class="fa-solid fa-stopwatch text-warning me-2"></i>Accélération In-Memory (Redis Cache)
                    </h5>
                    <p class="small text-secondary">
                        Compare le temps de réponse avec et sans mise en cache pour illustrer l'optimisation des performances dans une architecture cloud.
                    </p>
                    <div class="d-flex gap-2 mb-3">
                        <button class="btn btn-warning" onclick="testCache()">
                            <i class="fa-solid fa-gauge-high me-1"></i> Exécuter Test Cache vs DB
                        </button>
                        <button class="btn btn-outline-danger" onclick="flushCache()">
                            <i class="fa-solid fa-trash me-1"></i> Invalider le Cache
                        </button>
                    </div>
                    <div class="terminal-box" id="cacheTestBox">
                        Cliquez sur "Exécuter Test" pour mesurer les performances en millisecondes.
                    </div>
                </div>
            </div>
        </div>

        <!-- Architecture Diagram & Info Footer -->
        <div class="row">
            <div class="col-12">
                <div class="card-custom p-4">
                    <h6 class="text-light mb-2"><i class="fa-solid fa-network-wired me-2 text-info"></i>Topologie Réseau & Isolation Multi-Tiers</h6>
                    <p class="small text-secondary mb-0">
                        Cette architecture démontre les piliers fondamentaux de la virtualisation moderne : 
                        <strong>Isolation par Namespaces/cgroups</strong>, 
                        <strong>Réseau Virtuel Privé (172.25.0.0/16)</strong>, 
                        <strong>Équilibrage de charge L7 Nginx</strong>, 
                        <strong>Haute Disponibilité sans état (Stateless Compute)</strong>, 
                        <strong>Stockage Cloud Découplé (Stateful Volume)</strong> et 
                        <strong>Observabilité Continue (Prometheus / Grafana)</strong>.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function loadRecords() {
            fetch('/api/records')
                .then(r => r.json())
                .then(data => {
                    const box = document.getElementById('dbRecordsBox');
                    if (data.records && data.records.length > 0) {
                        box.innerHTML = data.records.map(rec => 
                            `[#${rec.id}] ${rec.title} <span class="text-secondary">(Créé par ${rec.source_node} à ${rec.created_at})</span>`
                        ).join('<br>');
                    } else {
                        box.innerHTML = "Aucun enregistrement trouvé.";
                    }
                })
                .catch(err => {
                    document.getElementById('dbRecordsBox').innerHTML = "Erreur: " + err;
                });
        }

        function addRecord() {
            const titleInput = document.getElementById('recordTitle');
            const title = titleInput.value.trim();
            if (!title) return;
            fetch('/api/records', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title})
            })
            .then(r => r.json())
            .then(data => {
                titleInput.value = '';
                loadRecords();
            });
        }

        function testCache() {
            const box = document.getElementById('cacheTestBox');
            box.innerHTML = "Mesure en cours...";
            fetch('/api/cache-benchmark')
                .then(r => r.json())
                .then(data => {
                    box.innerHTML = `
                        <strong>Statut :</strong> ${data.cache_hit ? '<span class="text-success">CACHE HIT (Redis)</span>' : '<span class="text-info">CACHE MISS (Base DB interrogée)</span>'}<br>
                        <strong>Temps d'exécution :</strong> ${data.duration_ms} ms<br>
                        <strong>Nœud exécutant :</strong> ${data.node}<br>
                        <strong>Détail :</strong> ${data.message}
                    `;
                });
        }

        function flushCache() {
            fetch('/api/cache-flush', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    document.getElementById('cacheTestBox').innerHTML = `<span class="text-warning">${data.message}</span>`;
                });
        }

        loadRecords();
    </script>
</body>
</html>
"""

@app.before_request
def start_timer():
    request.start_time = time.time()
    ACTIVE_CONNECTIONS.labels(node=NODE_NAME).inc()

@app.after_request
def track_metrics(response):
    ACTIVE_CONNECTIONS.labels(node=NODE_NAME).dec()
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        endpoint = request.endpoint or 'unknown'
        REQUEST_DURATION.labels(node=NODE_NAME, endpoint=endpoint).observe(duration)
        REQUESTS_TOTAL.labels(node=NODE_NAME, endpoint=endpoint, method=request.method, status=response.status_code).inc()
    return response

@app.route('/')
def home():
    container_ip = socket.gethostbyname(HOSTNAME)
    
    # DB status & count
    db_status = False
    db_count = 0
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM cloud_records;")
                db_count = cur.fetchone()[0]
                db_status = True
        except:
            pass
        finally:
            conn.close()

    # Redis status & hits
    r = get_redis_client()
    redis_status = False
    cache_hits = 0
    if r:
        try:
            redis_status = True
            cache_hits = r.incr("cloud_total_hits")
        except:
            pass

    return render_template_string(
        HTML_TEMPLATE,
        node_name=NODE_NAME,
        node_color=NODE_COLOR,
        hostname=HOSTNAME,
        container_ip=container_ip,
        db_status=db_status,
        db_count=db_count,
        redis_status=redis_status,
        cache_hits=cache_hits
    )

@app.route('/api/info')
def api_info():
    return jsonify({
        "status": "online",
        "node_name": NODE_NAME,
        "hostname": HOSTNAME,
        "container_ip": socket.gethostbyname(HOSTNAME),
        "timestamp": time.time(),
        "architecture": "High Availability Cloud Cluster"
    })

@app.route('/api/records', methods=['GET', 'POST'])
def api_records():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unreachable"}), 503

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if request.method == 'POST':
                data = request.get_json(force=True, silent=True) or {}
                title = data.get("title", "Nouvel élément cloud")
                cur.execute(
                    "INSERT INTO cloud_records (title, source_node) VALUES (%s, %s) RETURNING id, title, source_node, created_at;",
                    (title, NODE_NAME)
                )
                new_row = cur.fetchone()
                conn.commit()
                # Invalidate cache
                r = get_redis_client()
                if r:
                    r.delete("cached_records")
                return jsonify({"status": "created", "record": new_row}), 201
            else:
                cur.execute("SELECT id, title, source_node, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at FROM cloud_records ORDER BY id DESC LIMIT 20;")
                rows = cur.fetchall()
                return jsonify({"records": rows})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/cache-benchmark')
def api_cache_benchmark():
    start = time.time()
    r = get_redis_client()
    cache_hit = False

    if r:
        cached = r.get("benchmark_data")
        if cached:
            cache_hit = True
            CACHE_OPERATIONS.labels(node=NODE_NAME, result="hit").inc()
            duration_ms = round((time.time() - start) * 1000, 2)
            return jsonify({
                "cache_hit": True,
                "duration_ms": duration_ms,
                "node": NODE_NAME,
                "message": "Données servies directement depuis la mémoire RAM de Redis (Ultra-rapide)."
            })

    # Cache miss: simulate computation + DB query
    CACHE_OPERATIONS.labels(node=NODE_NAME, result="miss").inc()
    time.sleep(0.04) # Simulate network/IO cost
    conn = get_db_connection()
    count = 0
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cloud_records;")
            count = cur.fetchone()[0]
        conn.close()

    result_payload = json.dumps({"count": count, "computed_at": time.time()})
    if r:
        r.setex("benchmark_data", 30, result_payload)

    duration_ms = round((time.time() - start) * 1000, 2)
    return jsonify({
        "cache_hit": False,
        "duration_ms": duration_ms,
        "node": NODE_NAME,
        "message": "Données calculées et récupérées depuis PostgreSQL puis stockées dans le cache."
    })

@app.route('/api/cache-flush', methods=['POST'])
def api_cache_flush():
    r = get_redis_client()
    if r:
        r.delete("benchmark_data")
        return jsonify({"status": "ok", "message": "Cache Redis réinitialisé avec succès."})
    return jsonify({"status": "error", "message": "Redis indisponible"}), 503

@app.route('/health')
def health():
    db_ok = get_db_connection() is not None
    redis_ok = get_redis_client() is not None
    status_code = 200 if (db_ok and redis_ok) else 503
    return jsonify({
        "node": NODE_NAME,
        "status": "healthy" if status_code == 200 else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "redis": "connected" if redis_ok else "unreachable"
    }), status_code

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
