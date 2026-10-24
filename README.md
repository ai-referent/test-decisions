# test-decisions

Programmes Python qui routent un prompt : un modèle de décision choisit la voie,
un modèle « cerveau » répond.

## router.py

1. `kev:4b-q8_0` ([endpoint de décision Ollama `/v1/systemone`](https://docs.ollama.com/api/systemone)) classe le prompt :
   `Reasoning`, `Chat` ou `Reject`.
2. `Reject` renvoie `Unauthorized request`.
3. `Chat` et `Reasoning` envoient le prompt à `deepseek-r1:14b` (`/api/chat`) avec
   un message système adapté ; la réflexion du modèle n'est activée que pour `Reasoning`.

```bash
./setup.sh                      # installe Ollama, les modèles et le venv Python
.venv/bin/python router.py
```

Variables d'environnement : `DECISION_MODEL` (défaut `kev:4b-q8_0`), `BRAIN_MODEL`
(défaut `deepseek-r1:14b`) et `OLLAMA_HOST` (défaut `http://localhost:11434`).
Les mêmes valeurs servent à `setup.sh` et à `router.py`.

Budget VRAM (16 Go) : `deepseek-r1:14b` en q4 occupe environ 9 Go, cache compris ;
avec `kev:4b-q8_0` (4,5 Go), on arrive à environ 13,5 Go : ça tient, avec peu de marge.
