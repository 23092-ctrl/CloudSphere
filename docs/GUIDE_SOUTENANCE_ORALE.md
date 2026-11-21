# 🎓 Guide de Soutenance Orale — Démonstration Mini-Projet Cloud & Virtualisation

> **Durée estimée de la présentation :** 10 à 15 minutes + 5 minutes de questions  
> **Groupe :** 4 Étudiants  
> **Projet :** CloudSphere — Architecture Cloud Native Haute Disponibilité & Observabilité

---

## ⏱️ Déroulé Minute par Minute (Scénario de Présentation)

### 🎙️ [00:00 - 02:30] Introduction & Contexte — *Présenté par l'Étudiant 1 (Lead DevOps)*
- **Ce qu'il faut dire :**
  > *"Bonjour Monsieur / Madame. Notre projet porte sur la conception et le déploiement d'une infrastructure Cloud Native conteneurisée baptisée **CloudSphere**."*
  > *"Dans les infrastructures traditionnelles, une panne serveur entraîne l'interruption complète du service. Notre objectif a été de concevoir une architecture hautement disponible, découplée, tolérante aux pannes et totalement supervisée en temps réel selon le modèle CaaS (Container as a Service)."*
- **Ce qu'il faut montrer :**
  - Ouvrir le terminal dans le dossier du projet :
    ```bash
    cd ~/MiniProjet_Cloud_Virtualisation
    docker-compose ps
    ```
  - Montrer que les 7 conteneurs sont en cours d'exécution dans un réseau virtuel isolé (`172.25.0.0/16`).

---

### 🎙️ [02:30 - 05:00] Répartition de Charge & Architecture Microservices — *Présenté par l'Étudiant 2 (Microservices) & Étudiant 3 (Réseau)*
- **Ce qu'il faut dire :**
  > *"Au niveau de la couche d'accès (Edge Tier), nous avons configuré un Load Balancer Nginx de niveau 7. Derrière ce reverse proxy, nous disposons d'un pool de 3 conteneurs applicatifs identiques (Node-Alpha, Node-Beta, Node-Gamma) exécutant notre API Python/Gunicorn."*
  > *"L'algorithme utilisé est un Round-Robin équitable. Chaque conteneur dispose de son propre environnement d'exécution isolé par des namespaces Linux et cgroups."*
- **Action Démo en Direct :**
  - Ouvrir le navigateur sur `http://localhost:8088`.
  - Rafraîchir la page ou lancer :
    ```bash
    ./scripts/demo.sh
    # Choisir l'option 3 (Tester le Load Balancing)
    ```
  - Montrer au jury que chaque requête est prise en charge successivement par `Node-Beta`, `Node-Gamma`, `Node-Alpha` avec affichage de l'IP interne du conteneur.

---

### 🎙️ [05:00 - 08:30] Scénario de Panne à Chaud (*Chaos Engineering*) — *Présenté par l'Étudiant 3 (Réseau & Sécurité)*
- **Ce qu'il faut dire :**
  > *"La force d'une architecture Cloud réside dans sa résilience face aux pannes. Que se passe-t-il si un nœud de calcul plante en pleine production ?"*
  > *"Nous allons maintenant simuler le crash brutal de l'un des trois conteneurs applicatifs."*
- **Action Démo en Direct :**
  - Dans le menu de `./scripts/demo.sh`, choisir l'**option 4** (Tester la Haute Disponibilité).
  - Le script coupe `cloud_app_node_2` via `docker stop`.
  - Observer que les requêtes suivantes aboutissent instantanément sur Alpha et Gamma **sans aucune erreur 502 Bad Gateway**.
  - Le conteneur est ensuite redémarré et réintégré automatiquement dans le pool sans intervention manuelle.

---

### 🎙️ [08:30 - 11:00] Persistance Cloud & Accélération par Cache — *Présenté par l'Étudiant 1 & 2*
- **Ce qu'il faut dire :**
  > *"Pour garantir le découplage, notre couche de calcul est sans état (Stateless). Toutes les données persistantes sont stockées dans PostgreSQL via un volume Docker managé (Stateful)."*
  > *"Pour soulager la base de données et réduire les temps de latence, nous avons intercalé un cache distribué en mémoire vive Redis 7."*
- **Action Démo en Direct :**
  - Sur l'interface web `http://localhost:8088`, ajouter une entrée dans le formulaire de test de persistance.
  - Cliquer sur le bouton **"Exécuter Test Cache vs DB"** :
    - Montrer la différence : **~60 ms** pour une requête en base contre **~1.8 ms** avec le cache Redis (accélération x30).

---

### 🎙️ [11:00 - 13:30] Observabilité & Supervision Temps Réel — *Présenté par l'Étudiant 4 (Observabilité & SRE)*
- **Ce qu'il faut dire :**
  > *"En environnement Cloud d'entreprise, on ne peut pas piloter ce qu'on ne mesure pas. Nous avons intégré la suite Prometheus et Grafana."*
  > *"Chaque nœud applicatif expose ses métriques métier sur `/metrics`. Prometheus collecte ces données toutes les 3 secondes, et Grafana les projette sous forme de graphiques décisionnels."*
- **Action Démo en Direct :**
  - Ouvrir `http://localhost:3000` (identifiants `admin` / `admin`).
  - Ouvrir le tableau de bord préconfiguré **CloudSphere - Observabilité & Haute Disponibilité**.
  - Lancer un tir de charge concurrent :
    ```bash
    python3 scripts/load_generator.py 150 10
    ```
  - Montrer en direct au jury l'aiguille du débit (RPS) grimper, la jauge de répartition de charge s'équilibrer entre les conteneurs et les courbes de latence.

---

## ❓ Questions Types du Jury & Réponses Préparées

### Q1 : *"Pourquoi avoir utilisé des conteneurs Docker plutôt que des machines virtuelles KVM / VirtualBox ?"*
- **Réponse :**
  > *"Les machines virtuelles imposent un hyperviseur et un OS complet par instance, ce qui consomme plusieurs Go de RAM et plusieurs minutes de boot. Les conteneurs partagent le noyau Linux de l'hôte via les namespaces et cgroups, permettant un démarrage en quelques millisecondes et une consommation de seulement ~30 Mo par nœud, tout en garantissant une isolation stricte."*

### Q2 : *"Que se passe-t-il si le conteneur Nginx lui-même tombe en panne ?"*
- **Réponse :**
  > *"Dans notre maquette, Nginx est le point d'entrée unique. Dans une architecture Cloud de production à grande échelle, nous utiliserions deux instances Nginx avec une IP virtuelle partagée via le protocole VRRP (Keepalived) ou un Cloud Load Balancer managé (comme AWS ALB ou GCP Cloud Load Balancing) offrant un SLA de 99.99%."*

### Q3 : *"Comment vos conteneurs communiquent-ils entre eux sans conflits de ports ?"*
- **Réponse :**
  > *"Nous avons créé un réseau virtuel bridge privé `cloud_net` avec le subnet `172.25.0.0/16`. Chaque conteneur possède sa propre adresse IP et sa propre pile réseau. Docker fournit un résolveur DNS interne permettant aux nœuds de joindre `postgres:5432` ou `redis:6379` par nom d'hôte."*

### Q4 : *"Quelle est la différence entre Stateless et Stateful dans votre projet ?"*
- **Réponse :**
  > *"Les conteneurs de calcul (App-1, App-2, App-3) sont Stateless : ils ne sauvegardent rien localement. Si l'un est détruit, aucune donnée n'est perdue. La couche Stateful regroupe PostgreSQL et son volume persistant (`pg_cloud_data`) qui garantit la durabilité des données indépendamment du cycle de vie des conteneurs."*
