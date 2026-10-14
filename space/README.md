---
title: verif-refs
emoji: 📚
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
pinned: false
license: mit
short_description: Check bibliographic references, field by field
---

# verif-refs — interface web

Déposez une bibliographie (.bib, .ris, .docx, .txt, .md) ou collez-la : chaque référence est comparée
aux notices de Crossref, DataCite, OpenAlex et Open Library, et les écarts sont signalés champ par champ.
Aucune clé, aucun modèle de langage : les verdicts sont calculés par du code déterministe.

Variables à définir dans *Settings → Variables and secrets* du Space :

- `VERIF_REFS_CONTACT` : adresse transmise à Crossref et OpenAlex (règle d'usage de leurs API) ;
- `VERIF_REFS_DEPOT` : adresse du dépôt GitHub, affichée en bas de page ;
- `VERIF_REFS_MAX` (facultatif) : nombre maximal de références par fichier (150 par défaut).

Matériel : ZeroGPU convient (gratuit) ; CPU Basic aussi, s'il est disponible pour votre compte. L'outil n'utilise pas de carte graphique.

Code, méthode et limites : voir le dépôt GitHub du projet.
