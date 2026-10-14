"""Chaîne d'agents Google ADK pour verif-refs.

Le modèle de langage ne fait que trois choses : lire la demande, classer chaque référence
(article, livre, autre) et en recopier les champs. Toutes les comparaisons, tous les verdicts
et le décompte sont faits par le code de `core.py`.

Lancement : depuis le dossier parent, `adk web --port 8000`, puis choisir « verif_refs ».
"""

import os

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from .core import (charger_fichier, charger_texte, enregistrer_non_verifiable, lot_suivant,
                   rapport_final, verifier_article, verifier_ouvrage)

# =====================================================================
# Chaîne d'agents
# =====================================================================

MODELE = Gemini(
    model=os.environ.get("VERIF_REFS_MODELE", "gemini-flash-lite-latest"),
    # Niveau gratuit de Gemini : environ 15 requêtes par minute. Les nouvelles tentatives
    # sont espacées pour attendre la libération du quota au lieu d'abandonner.
    retry_options=types.HttpRetryOptions(attempts=8, initial_delay=15, max_delay=60,
                                         http_status_codes=[429, 503]),
)

chargeur = LlmAgent(
    name="chargeur",
    model=MODELE,
    description="Charge la bibliographie fournie par l'utilisateur.",
    instruction="""Tu charges la bibliographie à vérifier.
- Si le message de l'utilisateur contient un chemin de fichier (.docx, .txt, .md, .bib, .ris),
  appelle charger_fichier avec ce chemin exact.
- Sinon, s'il contient des références collées, appelle charger_texte avec tout ce texte, recopié exactement.
- Sinon, n'appelle aucun outil.
Réponds ensuite en une phrase : nombre de références trouvées et nombre de lots,
ou le problème rencontré. N'annonce aucune vérification toi-même.""",
    tools=[charger_fichier, charger_texte],
)

verificateur = LlmAgent(
    name="verificateur",
    model=MODELE,
    description="Vérifie un lot de références.",
    instruction="""Tu vérifies UN lot de références.
1. Appelle lot_suivant(). Si « termine » vaut true, réponds seulement « Vérification terminée. » et arrête-toi.
2. Pour CHAQUE référence du lot, avec son « numero » :
   - article de revue, ou toute référence qui contient un DOI → verifier_article ;
   - livre, manuel, nouvelle édition → verifier_ouvrage ;
   - thèse, rapport, communication de colloque, presse, chapitre, page web → enregistrer_non_verifiable.
   Recopie les champs EXACTEMENT, caractère par caractère, sans rien corriger ; champ absent → "".
   N'ajoute JAMAIS d'information absente de la référence (aucun DOI, aucune page, aucun nom).
   reference_brute = la référence entière, telle quelle.
3. Quand tous les résultats sont revenus, réponds seulement « Lot traité : » suivi de la progression.
Tu ne compares rien toi-même : les outils décident des verdicts.""",
    tools=[lot_suivant, verifier_article, verifier_ouvrage, enregistrer_non_verifiable],
)

boucle_verification = LoopAgent(
    name="boucle_verification",
    description="Répète la vérification lot par lot jusqu'à épuisement de la bibliographie.",
    sub_agents=[verificateur],
    max_iterations=60,
)

rapporteur = LlmAgent(
    name="rapporteur",
    model=MODELE,
    description="Produit le rapport final.",
    instruction="""Appelle rapport_final() une seule fois.
- Si « tableau » est vide, recopie seulement « message ».
- Sinon, recopie EXACTEMENT le « tableau », sans rien modifier, ajouter ni commenter,
  puis une dernière ligne : « Rapport enregistré : » suivi des chemins de « fichiers ».""",
    tools=[rapport_final],
)

root_agent = SequentialAgent(
    name="verificateur_references",
    description="Chaîne de vérification bibliographique : chargement, vérification par lots, rapport.",
    sub_agents=[chargeur, boucle_verification, rapporteur],
)
