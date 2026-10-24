#!/usr/bin/env bash
# Installe Ollama, télécharge les modèles et prépare l'environnement Python.
# Usage : ./setup.sh   (Linux ou macOS ; sous Windows, installer Ollama
# depuis https://ollama.com/download puis lancer les étapes 3 à 5 à la main)
#
# Modèles réglables par variables d'environnement, par exemple :
#   DECISION_MODEL=kev:4b-q8_0 ./setup.sh
set -euo pipefail

DECISION_MODEL="${DECISION_MODEL:-kev:4b}"
BRAIN_MODEL="${BRAIN_MODEL:-deepseek-r1:14b}"
MIN_OLLAMA="0.35.0"

# 1. Ollama (>= 0.35 pour l'endpoint /v1/systemone)
if ! command -v ollama >/dev/null; then
    echo "==> Installation d'Ollama"
    curl -fsSL https://ollama.com/install.sh | sh
fi
version="$(ollama --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
if [ "$(printf '%s\n' "$MIN_OLLAMA" "$version" | sort -V | head -1)" != "$MIN_OLLAMA" ]; then
    echo "Ollama $version trop ancien (>= $MIN_OLLAMA requis) : relancer l'installeur." >&2
    exit 1
fi

# 2. Serveur Ollama (l'installeur Linux le lance comme service ; sinon on le démarre)
if ! curl -fsS http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "==> Démarrage du serveur Ollama"
    ollama serve >/tmp/ollama.log 2>&1 &
    until curl -fsS http://localhost:11434/api/version >/dev/null 2>&1; do sleep 1; done
fi

# 3. Modèles
echo "==> Téléchargement de $DECISION_MODEL et $BRAIN_MODEL"
ollama pull "$DECISION_MODEL"
ollama pull "$BRAIN_MODEL"

# 4. Vérification rapide des deux modèles
echo "==> Test du modèle de décision"
echo "What is the capital of France?" | ollama run "$DECISION_MODEL" --ask "Is this a simple question?"
echo "==> Test du modèle cerveau"
ollama run "$BRAIN_MODEL" --think=false "Say hello in one word."

# 5. Environnement Python (le client HTTP httpx suffit, pas besoin de SDK)
echo "==> Environnement Python"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

echo "Prêt : DECISION_MODEL=$DECISION_MODEL BRAIN_MODEL=$BRAIN_MODEL .venv/bin/python router.py"
