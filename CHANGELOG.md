# Historique des versions

Le détail des évaluations figure dans [docs/note_methodologique.md](docs/note_methodologique.md).

## 5.2.0 — octobre 2026 (première version publique)
- Titres comparés sans tenir compte des accents (notices Persée enregistrées sans accents).
- Volumes et numéros normalisés : « Vol. 43 » = « 43 », « Suppl. 1 » = « Suppl_1 », « n° 194 » = « 194 ».
- Numéros doubles (« 106–107 », « 3–4 ») acceptés lorsque la source n'en enregistre qu'une partie.
- Notices d'ouvrages (Open Library) : un auteur supplémentaire dans la notice, des initiales en plus ou un nom de famille composé ne produisent plus d'ERREUR (note ou À VÉRIFIER).
- Prudence maintenue lorsqu'une notice d'ouvrage ne cite que le premier auteur (À VÉRIFIER), pour éviter les fausses confirmations.
- Code réparti en trois modules : `core.py` (vérification, bibliothèque standard), `cli.py` (ligne de commande sans modèle de langage, lecture .bib et .ris), `agent.py` (chaîne Google ADK).
- Interface bilingue anglais / français : sélecteur dans l'interface web (langue du navigateur par défaut), option `--lang` en ligne de commande (anglais par défaut), rapports traduits. La vérification est identique dans les deux langues.
- Interface web (Gradio) hébergeable sur Hugging Face Spaces : dépôt d'un fichier ou bibliographie collée, résultats affichés au fur et à mesure, rapport téléchargeable.
- Adresse de contact et modèle Gemini configurables par variables d'environnement.
- Non encore validée sur un corpus indépendant.

## 5.1 — septembre 2026
- Le modèle de langage ne peut plus transmettre de DOI : seul le DOI écrit dans la référence est lu.
- Toute référence contenant un DOI est vérifiée par ce DOI, quel que soit le classement du modèle.
- Particules (« van », « de », « von ») reconnues en début de référence ; rapprochement de noms voisins corrigé ; initiales en excès recoupées avec OpenAlex.
- Stabilité de 100 % sur deux exécutions (corpus de stabilité non distribué).

## 5.0
- Chaîne de trois agents ADK : chargeur (.docx, .txt, .bib, .ris ou texte collé), boucle de vérification par lots de dix, rapporteur (.md et .csv).
- Ajout de DataCite et du cinquième verdict, À VÉRIFIER.
- Correctifs V1 à V5 issus du test de validation (DOI différent, points de suspension APA, contrôle inverse des auteurs, actes de conférence, initiales en excès).

## 4.0 – 4.2
- Partage des rôles : le modèle classe et recopie ; le code compare, décide les verdicts et compte.
- 57/60 sur le corpus de développement ; version 4.2 figée pour la validation.

## 3
- Deux sources ajoutées et règles de normalisation confiées au modèle : régression, abandonnée.

## 1 – 2
- Prototypes : le modèle interroge Crossref et compare lui-même les champs (54/60 en v2).
