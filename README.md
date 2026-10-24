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
Les mêmes valeurs servent à `setup.sh` et à `router.py`. `BRAIN_NUM_CTX` (défaut
`8192`, lu par `router.py`) fixe la taille du contexte de deepseek-r1.

Budget VRAM (16 Go), ordres de grandeur :

| Élément                                  | VRAM      |
|------------------------------------------|-----------|
| `deepseek-r1:14b` q4 (poids)             | ~9 Go     |
| son cache KV, 8192 tokens                | ~1,5 Go   |
| `kev:4b-q8_0`                            | ~4,5 Go   |
| **Total**                                | **~15 Go** |

C'est juste. Vérifier avec `ollama ps` que les deux modèles sont à `100% GPU`.
Sinon : baisser `BRAIN_NUM_CTX` (4096 divise le cache par deux, mais la réflexion
risque d'être tronquée), ou quantifier le cache en lançant le serveur avec
`OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve` (cache ÷ 2).
