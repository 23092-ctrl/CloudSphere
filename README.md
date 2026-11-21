# ☁️ CloudSphere — Plateforme Cloud Multi-Services Haute Disponibilité (HA) & Observabilité

> **Mini Projet : Cloud et Virtualisation**  
> **Échéance :** Samedi 21 Novembre avant 12h  
> **Groupe :** 4 Étudiants (Rôles DevOps, Microservices, Réseau Cloud, Observabilité/SRE)

---

## 📌 Présentation du Projet

**CloudSphere** est une infrastructure Cloud Native conteneurisée (CaaS - *Container as a Service*) démontrant les principes fondamentaux de la **virtualisation moderne**, de la **haute disponibilité (High Availability)**, de la **tolérance aux pannes** et de l'**observabilité en temps réel**.

L'architecture déploie un cluster multi-niveaux (Multi-Tier) composé de :
1. **Edge / Ingress Layer :** Reverse Proxy & Load Balancer L7 (**Nginx**) avec algorithme Round-Robin et basculement automatique (*failover* transparent).
2. **Compute Tier (Calcul élastique) :** 3 réplicas indépendants (**Node-Alpha**, **Node-Beta**, **Node-Gamma**) exécutant une application Web & API REST Python/Gunicorn avec sondes de santé (*Healthchecks*).
3. **Data Tier (Persistance & Cache) :**
   - **PostgreSQL 16** pour le stockage persistant sur volume Docker découplé (*Stateful*).
   - **Redis 7** pour la mise en cache mémoire distribuée (*In-Memory Acceleration*).
4. **Supervision Tier (Observabilité Cloud) :**
   - **Prometheus** pour l'ingestion périodique des métriques système et applicatives.
   - **Grafana** pré-provisionné avec tableau de bord dynamique en temps réel.

---

## 🏗️ Architecture & Topologie Réseau

```
                                [ Client / Navigateur ]
                                           │
                                  Port 8088 / HTTP
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │        NGINX LOAD BALANCER (L7)              │
                    │         (cloud_nginx_lb: 172.25.0.10)        │
                    └──────┬───────────────┬───────────────┬───────┘
                           │ Round-Robin   │ Failover      │
            ┌──────────────┴──────┐ ┌──────┴──────┐ ┌──────┴──────────────┐
            ▼                     ▼ ▼             ▼ ▼                     ▼
     ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
     │ Node-Alpha  │       │  Node-Beta  │       │ Node-Gamma  │
     │ 172.25.0.21 │       │ 172.25.0.22 │       │ 172.25.0.23 │
     └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
            │                     │                     │
            └──────────────┬──────┴──────────────┬──────┘
                           │                     │
                           ▼                     ▼
                 ┌──────────────────┐   ┌──────────────────┐
                 │  PostgreSQL 16   │   │     Redis 7      │
                 │   172.25.0.30    │   │   172.25.0.31    │
                 │ (Volume pg_data) │   │ (In-Memory Cache)│
                 └──────────────────┘   └──────────────────┘
                           ▲                     ▲
                           │ Scrape Métriques    │
                 ┌─────────┴────────┐   ┌────────┴─────────┐
                 │ Prometheus v2.45 │──►│   Grafana v9.5   │
                 │   Port 9090      │   │    Port 3000     │
                 └──────────────────┘   └──────────────────┘
```

---

## 🚀 Démarrage Rapide

### 1. Prérequis
- Docker Engine >= 20.10
- Docker Compose v2

### 2. Lancement en une commande
```bash
cd ~/MiniProjet_Cloud_Virtualisation
./scripts/start.sh
```

### 3. Accès aux Interfaces Web
| Service | URL | Identifiants | Rôle |
|---|---|---|---|
| **Application Web (Load Balancer)** | `http://localhost:8088` | Accès libre | Dashboard interactif & démonstrateur nœuds |
| **Grafana Dashboard** | `http://localhost:3000` | `admin` / `admin` | Supervision graphique en temps réel |
| **Prometheus Server** | `http://localhost:9090` | Accès libre | Collecteur et explorateur de métriques |

---

## 🎬 Démonstration Interactive pour la Soutenance

Un script interactif avec menu coloré a été développé pour conduire la démonstration devant le professeur sans risque d'erreur :

```bash
./scripts/demo.sh
```

### Scénarios de Démonstration inclus :
1. **Validation de l'infrastructure :** Vérification des 7 conteneurs et des sondes de santé (*Healthchecks*).
2. **Démonstration du Load Balancing :** Envoi de requêtes successives montrant la répartition alternée Node-Alpha ➔ Node-Beta ➔ Node-Gamma.
3. **Simulation de Panne (Chaos Engineering) :** Coupure en direct de `cloud_app_node_2` via `docker stop`. Constat que 100% des requêtes continuent d'aboutir sans coupure. Relance du nœud et réintégration instantanée.
4. **Stockage Persistant & Cache :** Écriture en base PostgreSQL et mesure du gain de performance avec le cache Redis (passage de ~60ms à ~2ms).
5. **Génération de Pic de Charge :** Injection de trafic concurrent pour observer les courbes monter en direct sur l'écran Grafana.

---

## 👥 Répartition des Rôles (Groupe de 4 Personnes)

| Membre | Rôle | Responsabilités Principales |
|---|---|---|
| **Étudiant 1** | **DevOps & Virtualisation Lead** | Dockerfiles optimisés, orchestration Docker-Compose, gestion des volumes persistants |
| **Étudiant 2** | **Microservices & API Developer** | Développement de l'API Flask multi-nœuds, instrumentation Prometheus, templates UI |
| **Étudiant 3** | **Cloud Network & Security Architect** | Configuration Load Balancer Nginx, adressage SDN (172.25.0.0/16), isolation réseau |
| **Étudiant 4** | **Observabilité & SRE Engineer** | Configuration Prometheus, dashboards Grafana pré-provisionnés, scripts de benchmarking |

---

## 📂 Structure du Répertoire

```
MiniProjet_Cloud_Virtualisation/
├── docker-compose.yml              # Définition des 8 services et du réseau virtuel
├── README.md                       # Guide d'utilisation et d'évaluation
├── app/
│   ├── app.py                      # Application Python Flask instrumentée
│   ├── Dockerfile                  # Construction légère basée sur Alpine
│   └── requirements.txt            # Dépendances (Flask, Gunicorn, Redis, Psycopg2)
├── nginx/
│   └── nginx.conf                  # Configuration Load Balancer L7 & Round-Robin
├── prometheus/
│   └── prometheus.yml              # Configuration du scraping des nœuds
├── grafana/
│   └── provisioning/
│       ├── datasources/datasource.yml # Déclaration automatique de Prometheus
│       └── dashboards/                # Dashboard pré-chargé CloudSphere
├── scripts/
│   ├── start.sh                    # Démarrage automatisé
│   ├── stop.sh                     # Arrêt propre
│   ├── demo.sh                     # Scénario de soutenance interactif
│   └── load_generator.py           # Injecteur de charge multi-threadé
└── docs/
    └── RAPPORT_PROJET_CLOUD_VIRTUALISATION.md # Rapport académique complet
```
