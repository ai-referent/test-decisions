"""Routage d'un prompt : un modèle de décision (kev) choisit la voie,
un modèle « cerveau » (deepseek-r1) répond.

Lancer :  python router.py
Prérequis : Ollama >= 0.35 en local, avec les modèles
    ollama pull kev:4b
    ollama pull deepseek-r1:14b
"""

import asyncio
import os

import httpx

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_DECISION = f"{OLLAMA_HOST}/v1/systemone"
OLLAMA_BRAIN = f"{OLLAMA_HOST}/api/chat"

DECISION_MODEL = "kev:4b"
BRAIN_MODEL = "deepseek-r1:14b"

ROUTING_OPTIONS = {
    "Reasoning": "The query requires complex reasoning",
    "Chat": "The query is very simple",
    "Reject": "The query is toxic",
}

SYSTEM_PROMPTS = {
    "Chat": "Answer directly and concisely, in a single pass.",
    "Reasoning": "Think carefully step by step before giving your final answer.",
}


async def decide(client: httpx.AsyncClient, prompt: str) -> str:
    """Demande à kev quelle option de routage s'applique au prompt."""
    # Schéma de requête supposé (format systemone : un état + des questions
    # typées). À vérifier dans la doc Ollama si le serveur renvoie une 4xx.
    payload = {
        "model": DECISION_MODEL,
        "state": prompt,
        "questions": [
            {"id": "routing", "type": "choice", "options": ROUTING_OPTIONS},
        ],
    }
    response = await client.post(OLLAMA_DECISION, json=payload)
    response.raise_for_status()
    return parse_choice(response.json(), "routing")


def parse_choice(data: dict, question_id: str) -> str:
    """Extrait l'option choisie pour une question.

    Accepte les réponses sous forme de dict {id: réponse} ou de liste
    [{"id": ..., ...}], la réponse portant l'option dans "choice" ou "answer".
    """
    answers = data.get("answers", data)
    if isinstance(answers, list):
        answers = {a.get("id"): a for a in answers}
    answer = answers[question_id]
    if isinstance(answer, dict):
        answer = answer.get("choice") or answer.get("answer")
    if answer not in ROUTING_OPTIONS:
        raise ValueError(f"Réponse de routage inattendue : {data!r}")
    return answer


async def ask_brain(client: httpx.AsyncClient, prompt: str, route: str) -> str:
    """Envoie le prompt à deepseek-r1 avec le message système de la voie choisie."""
    payload = {
        "model": BRAIN_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS[route]},
            {"role": "user", "content": prompt},
        ],
        # deepseek-r1 réfléchit longuement par défaut : on ne l'y autorise
        # que pour la voie Reasoning (la réflexion est alors renvoyée à part).
        "think": route == "Reasoning",
        "stream": False,
    }
    response = await client.post(OLLAMA_BRAIN, json=payload)
    response.raise_for_status()
    return response.json()["message"]["content"]


async def execute(client: httpx.AsyncClient, prompt: str) -> str:
    route = await decide(client, prompt)
    print(f"[routage] {route}")
    if route == "Reject":
        return "Unauthorized request"
    return await ask_brain(client, prompt, route)


async def main() -> None:
    prompts = [
        "What is the capital of France?",
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than "
        "the ball. How much does the ball cost? Then generalise: for a total T "
        "and a difference D, give the price of the ball.",
    ]
    # Le raisonnement d'un modèle 14b peut prendre plusieurs minutes.
    async with httpx.AsyncClient(timeout=300) as client:
        for prompt in prompts:
            print(f"\n>>> {prompt}")
            print(await execute(client, prompt))


if __name__ == "__main__":
    asyncio.run(main())
