# test-decisions

Programmes Python qui routent un prompt : un modèle de décision choisit la voie,
un modèle « cerveau » répond.

## router.py

1. `kev:4b` (endpoint de décision Ollama `/v1/systemone`) classe le prompt :
   `Reasoning`, `Chat` ou `Reject`.
2. `Reject` renvoie `Unauthorized request`.
3. `Chat` et `Reasoning` envoient le prompt à `deepseek-r1:14b` (`/api/chat`) avec
   un message système adapté ; la réflexion du modèle n'est activée que pour `Reasoning`.

```bash
ollama pull kev:4b
ollama pull deepseek-r1:14b
pip install -r requirements.txt
python router.py
```

`OLLAMA_HOST` (défaut `http://localhost:11434`) permet de viser un autre serveur.
