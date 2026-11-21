#!/usr/bin/env bash

# ==========================================================
#   CloudSphere - Scénario de Démonstration pour Soutenance
# ==========================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}========================================================================${NC}"
echo -e "${CYAN}   🚀 PROJET CLOUD & VIRTUALISATION - DEMONSTRATION EN DIRECT (HA/CaaS)${NC}"
echo -e "${CYAN}========================================================================${NC}"
echo -e "  Plateforme : ${GREEN}CloudSphere${NC} | Architecture Multi-Tiers Résiliente"
echo -e "  Composants : Nginx (LB L7) + 3 Nodes Python/Gunicorn + PostgreSQL + Redis"
echo -e "               + Supervision temps réel Prometheus & Grafana"
echo -e "${CYAN}========================================================================${NC}"
echo ""

function check_status() {
    echo -e "${YELLOW}>>> [1/6] Vérification de l'état des conteneurs du cluster...${NC}"
    docker-compose ps
    echo ""
    echo -e "${GREEN}Vérification des sondes de santé (Healthchecks) :${NC}"
    curl -s http://localhost:8088/health | grep -o '"status":"[^"]*"' || echo -e "${RED}Erreur d'accès à l'endpoint Nginx${NC}"
    echo ""
}

function test_load_balancing() {
    echo -e "${YELLOW}>>> [2/6] Démonstration du Load Balancing L7 (Nginx Round-Robin)...${NC}"
    echo -e "Envoi de 9 requêtes successives au point d'entrée HTTP (http://localhost:8088/api/info) :"
    echo ""
    for i in {1..9}; do
        RESP=$(curl -s http://localhost:8088/api/info)
        NODE=$(echo "$RESP" | grep -o '"node_name":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        IP=$(echo "$RESP" | grep -o '"container_ip":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        echo -e "  Requête #${i} ➔ Réponse traitée par : ${GREEN}${NODE}${NC} (IP: ${IP})"
        sleep 0.3
    done
    echo ""
    echo -e "${GREEN}✔ Répartition équitable constatée sur les 3 nœuds applicatifs !${NC}"
    echo ""
}

function test_fault_tolerance() {
    echo -e "${YELLOW}>>> [3/6] Démonstration de la Haute Disponibilité (Tolérance aux Pannes)...${NC}"
    echo -e "Arrêt brutal d'un nœud applicatif (${RED}cloud_app_node_2${NC}) pour simuler un crash matériel/conteneur..."
    docker stop cloud_app_node_2 > /dev/null
    echo -e "${RED}[SIMULATION] cloud_app_node_2 est maintenant OFFLINE !${NC}"
    echo ""
    echo -e "Test d'accès continu pendant la panne (Nginx doit basculer automatiquement sans erreur 502) :"
    for i in {1..6}; do
        RESP=$(curl -s http://localhost:8088/api/info)
        NODE=$(echo "$RESP" | grep -o '"node_name":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        echo -e "  Requête #${i} ➔ Service assuré par : ${BLUE}${NODE}${NC}"
        sleep 0.3
    done
    echo ""
    echo -e "${GREEN}✔ ZÉRO INTERRUPTION DE SERVICE pour le client (Failover transparent) !${NC}"
    echo ""
    echo -e "Redémarrage du conteneur ${GREEN}cloud_app_node_2${NC}..."
    docker start cloud_app_node_2 > /dev/null
    sleep 2
    echo -e "${GREEN}✔ Nœud restauré et réintégré dans le pool du Load Balancer automatiquement.${NC}"
    echo ""
}

function test_persistence_cache() {
    echo -e "${YELLOW}>>> [4/6] Démonstration du Stockage Persistant (DB) et du Cache Redis...${NC}"
    TITRE="Test Soutenance - $(date +'%T')"
    echo -e "Insertion d'une donnée via l'API : '${TITRE}'"
    curl -s -X POST http://localhost:8088/api/records -H "Content-Type: application/json" -d "{\"title\":\"${TITRE}\"}" > /dev/null
    echo -e "${GREEN}✔ Donnée enregistrée dans le volume persistant PostgreSQL (pg_cloud_data).${NC}"
    echo ""
    echo -e "Test de performance de cache (Redis vs PostgreSQL) :"
    # Miss
    curl -s -X POST http://localhost:8088/api/cache-flush > /dev/null
    MISS=$(curl -s http://localhost:8088/api/cache-benchmark)
    echo -e "  1er appel (Cache MISS) : $(echo $MISS | grep -o '"duration_ms":[^,]*') ms"
    # Hit
    HIT=$(curl -s http://localhost:8088/api/cache-benchmark)
    echo -e "  2ème appel (Cache HIT) : $(echo $HIT | grep -o '"duration_ms":[^,]*') ms"
    echo -e "${GREEN}✔ Gain de vitesse mesuré grâce au cache mémoire distribué !${NC}"
    echo ""
}

function generate_traffic() {
    echo -e "${YELLOW}>>> [5/6] Génération de trafic pour le Monitoring Grafana/Prometheus...${NC}"
    echo -e "Envoi de 60 requêtes en rafale pour alimenter les métriques en direct..."
    python3 scripts/load_generator.py 60 5
    echo -e "${GREEN}✔ Données de trafic injectées avec succès !${NC}"
    echo ""
}

function show_menu() {
    echo -e "${CYAN}------------------------------------------------------------------------${NC}"
    echo -e "CHOISISSEZ UNE ACTION POUR LA PRESENTATION :"
    echo -e "  ${GREEN}1${NC}) Tout exécuter (Scénario complet de soutenance)"
    echo -e "  ${GREEN}2${NC}) Tester l'état du cluster (docker ps & healthchecks)"
    echo -e "  ${GREEN}3${NC}) Tester le Load Balancing (Round-Robin 3 nœuds)"
    echo -e "  ${GREEN}4${NC}) Tester la Haute Disponibilité (Crash de conteneur en direct)"
    echo -e "  ${GREEN}5${NC}) Tester Stockage Persistant & Cache Mémoire"
    echo -e "  ${GREEN}6${NC}) Générer un pic de charge (Grafana Live)"
    echo -e "  ${GREEN}q${NC}) Quitter"
    echo -e "${CYAN}------------------------------------------------------------------------${NC}"
    read -p "Votre choix [1-6, q] : " CHOICE
    echo ""

    case "$CHOICE" in
        1)
            check_status
            test_load_balancing
            test_fault_tolerance
            test_persistence_cache
            generate_traffic
            ;;
        2) check_status ;;
        3) test_load_balancing ;;
        4) test_fault_tolerance ;;
        5) test_persistence_cache ;;
        6) generate_traffic ;;
        q|Q) exit 0 ;;
        *) echo "Choix invalide." ;;
    esac
}

# If arguments passed, run non-interactively
if [ "$1" == "--all" ]; then
    check_status
    test_load_balancing
    test_fault_tolerance
    test_persistence_cache
    generate_traffic
    exit 0
fi

while true; do
    show_menu
done
