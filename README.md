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

## Capacité : faire tenir les modèles en VRAM

### Budget (GPU 16 Go), ordres de grandeur

| Élément                                  | VRAM      |
|------------------------------------------|-----------|
| `deepseek-r1:14b` q4 (poids)             | ~9 Go     |
| son cache KV, 8192 tokens                | ~1,5 Go   |
| `kev:4b-q8_0`                            | ~4,5 Go   |
| **Total**                                | **~15 Go** |

C'est juste : le moindre écart (contexte plus grand, autre application sur le GPU)
fait déborder.

### Diagnostiquer

```bash
ollama ps      # modèles chargés, mémoire, répartition GPU/CPU
nvidia-smi     # VRAM réellement occupée sur la carte
```

Les deux modèles doivent apparaître à `100% GPU`. Symptômes d'un débordement :
- un modèle affiche une part de CPU (`30%/70% CPU/GPU`, etc.) : il tourne en partie
  sur le processeur, et les réponses deviennent très lentes ;
- un seul modèle apparaît : Ollama décharge l'autre pour faire de la place, et
  chaque changement de modèle coûte quelques secondes de rechargement.

### Astuces, de la plus simple à la plus coûteuse

1. **Réduire le contexte du cerveau** : `BRAIN_NUM_CTX=4096 .venv/bin/python router.py`.
   Le cache KV est proportionnel au contexte (4096 ≈ 0,75 Go au lieu de 1,5 Go), mais
   la réflexion de deepseek-r1 compte dans ce contexte : trop petit, elle est tronquée.
2. **Quantifier le cache KV** : cache ÷ 2 à contexte égal, perte de qualité minime.
   Ce sont des réglages du serveur, pas de la requête :
   ```bash
   OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve
   ```
   `q4_0` divise encore par deux, avec une perte de qualité plus visible.
3. **Une seule requête à la fois** : `OLLAMA_NUM_PARALLEL=1` (réglage serveur). Chaque
   requête parallèle réserve son propre cache, donc la mémoire du cache est multipliée
   par le nombre de requêtes servies en même temps.
4. **Des modèles plus petits** : une variante q4 de kev si la bibliothèque en propose
   une (`DECISION_MODEL=...`), ou `BRAIN_MODEL=deepseek-r1:8b` (~5 Go au lieu de ~9 Go,
   au prix de la qualité du raisonnement).
5. **Libérer le GPU** : fermer les autres applications qui l'utilisent (navigateur
   avec accélération matérielle, jeux, autres serveurs de modèles).

### Rendre les réglages serveur permanents

`OLLAMA_FLASH_ATTENTION`, `OLLAMA_KV_CACHE_TYPE` et `OLLAMA_NUM_PARALLEL` sont lus au
démarrage du serveur. Si Ollama tourne en service, il faut les déclarer là :

- **Linux (systemd)** : `sudo systemctl edit ollama`, puis ajouter
  ```ini
  [Service]
  Environment="OLLAMA_FLASH_ATTENTION=1"
  Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
  Environment="OLLAMA_NUM_PARALLEL=1"
  ```
  et `sudo systemctl restart ollama`.
- **macOS (application)** : `launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0` (idem pour
  les autres), puis relancer l'application Ollama.
- **Windows** : ajouter les variables dans les variables d'environnement de
  l'utilisateur, puis quitter et relancer Ollama.
