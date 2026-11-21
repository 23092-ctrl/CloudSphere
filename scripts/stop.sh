#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "Arrêt propre de la plateforme CloudSphere..."
docker-compose down
echo "Tous les conteneurs et réseaux virtuels ont été stoppés."
