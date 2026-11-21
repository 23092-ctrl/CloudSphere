#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=========================================================="
echo "   🚀 Démarrage de la Plateforme CloudSphere (HA Cluster)"
echo "=========================================================="

docker-compose up -d

echo ""
echo "⏳ Attente de la convergence des services (Healthchecks)..."
sleep 4

echo ""
echo "✅ Plateforme opérationnelle avec succès !"
echo "----------------------------------------------------------"
echo "🌐 Application Web (Nginx Load Balancer) : http://localhost:8088"
echo "📊 Dashboard Grafana                    : http://localhost:3000 (admin / admin)"
echo "📈 Prometheus Server                    : http://localhost:9090"
echo "----------------------------------------------------------"
echo "💡 Pour lancer la démonstration interactive : ./scripts/demo.sh"
