"""Traduction des résultats et des rapports (français / anglais).

La vérification (core.py) produit ses messages en français. La traduction intervient
uniquement à l'affichage : les verdicts et la logique ne changent pas selon la langue.
Un message inconnu est laissé tel quel (en français) plutôt que mal traduit.
"""

import csv
import os
import re

LANGUES = ("en", "fr")

VERDICTS = {  # ordre d'affichage : du plus urgent au moins urgent
    "ERREUR": {"en": "ERROR", "fr": "ERREUR"},
    "À VÉRIFIER": {"en": "TO CHECK", "fr": "À VÉRIFIER"},
    "À COMPLÉTER": {"en": "INCOMPLETE", "fr": "À COMPLÉTER"},
    "CONFIRMÉE": {"en": "CONFIRMED", "fr": "CONFIRMÉE"},
    "NON VÉRIFIABLE": {"en": "NOT VERIFIABLE", "fr": "NON VÉRIFIABLE"},
}

EXPLICATIONS = {
    "ERREUR": {"en": "the reference contradicts the source", "fr": "la référence contredit la source"},
    "À VÉRIFIER": {"en": "a discrepancy the source cannot settle", "fr": "écart que la source ne permet pas de trancher"},
    "À COMPLÉTER": {"en": "nothing wrong, but a field is missing", "fr": "rien de faux, un champ manque"},
    "CONFIRMÉE": {"en": "no discrepancy on the fields checked", "fr": "aucun écart sur les champs vérifiés"},
    "NON VÉRIFIABLE": {"en": "document not found in the sources queried", "fr": "document absent des sources consultées"},
}

CHAMPS_EN = {
    "titre": "title",
    "sous-titre": "subtitle",
    "titre (partie manquante)": "title (missing part)",
    "auteur (majuscules)": "author (capitalisation)",
    "nom de famille composé": "compound surname",
    "auteur": "author",
    "dernier auteur (abréviation APA)": "last author (APA abbreviation)",
    "auteur omis": "missing author",
    "ordre des auteurs": "author order",
    "coauteurs non vérifiables (notice incomplète)": "co-authors not verifiable (incomplete record)",
    "noms absents de la source": "names not in the source",
    "DOI": "DOI",
    "revue": "journal",
    "numéro cumulé": "cumulative issue number",
    "volume": "volume",
    "numero": "issue",
    "pages": "pages",
    "année": "year",
    "éditeur": "publisher",
}

TYPES_EN = {
    "chapitre d'ouvrage": "book chapter",
    "thèse": "thesis",
    "mémoire": "master's thesis",
    "rapport": "report",
    "page web": "web page",
    "article de presse": "press article",
    "document non publié": "unpublished document",
    "document": "document",
    "chapitre, rapport ou page web": "chapter, report or web page",
    "communication": "conference paper",
    "presse professionnelle": "trade press",
    "prépublication": "preprint",
}


def _champ_en(c: str) -> str:
    if c in CHAMPS_EN:
        return CHAMPS_EN[c]
    m = re.fullmatch(r"initiales de (.+) \(en excès\)", c)
    if m:
        return f"initials of {m.group(1)} (extra)"
    m = re.fullmatch(r"initiales de (.+)", c)
    if m:
        return f"initials of {m.group(1)}"
    return c


def _type_en(t: str) -> str:
    m = re.fullmatch(r"erreur de traitement \((.*)\)", t)
    if m:
        return f"processing error ({m.group(1)})"
    return TYPES_EN.get(t, t)


# (motif français, traduction anglaise) — du plus précis au plus général
NOTES_EN = [
    (r"auteurs absents de la source", lambda m: "no authors in the source record"),
    (r"la notice d'ouvrage mentionne aussi « (.+) » \(non bloquant\)",
     lambda m: f"the book record also lists “{m[1]}” (non-blocking)"),
    (r"initiales de (.+) : la notice d'ouvrage n'en donne que (.+) \(non bloquant\)",
     lambda m: f"initials of {m[1]}: the book record only gives {m[2]} (non-blocking)"),
    (r"initiales de (.+) confirmées par OpenAlex \((.+)\)",
     lambda m: f"initials of {m[1]} confirmed by OpenAlex ({m[2]})"),
    (r"titre recopié par le modèle différent du texte brut \(à vérifier\)",
     lambda m: "title copied by the model differs from the raw text (to check)"),
    (r"erreur d'accès à (.+?) \((.*)\)", lambda m: f"could not reach {m[1]} ({m[2]})"),
    (r"DOI (\S+) absent de Crossref et de DataCite", lambda m: f"DOI {m[1]} not found in Crossref or DataCite"),
    (r"aucune notice correspondante dans Crossref", lambda m: "no matching record in Crossref"),
    (r"année : divergence Crossref \((.+)\), confirmée par OpenAlex",
     lambda m: f"year: Crossref differs ({m[1]}); the reference is confirmed by OpenAlex"),
    (r"document apparenté \(autre publication\) : (.+)",
     lambda m: f"related document (another publication): {m[1]}"),
    (r"numéro double « (.+) » : la source n'en enregistre qu'une partie \((.+)\)",
     lambda m: f"double issue “{m[1]}”: the source records only part of it ({m[2]})"),
    (r"pages : la source ne donne que la première page \((.+)\)",
     lambda m: f"pages: the source only gives the first page ({m[1]})"),
    (r"pages : divergence Crossref \((.+)\), les pages (.+) sont confirmées par le DOI lui-même",
     lambda m: f"pages: Crossref differs ({m[1]}); pages {m[2]} are confirmed by the DOI itself"),
    (r"(.+) : divergence Crossref \((.+)\), confirmé par OpenAlex",
     lambda m: f"{_champ_en(m[1])}: Crossref differs ({m[2]}); the reference is confirmed by OpenAlex"),
    (r"OpenAlex reprend souvent Crossref : second avis non indépendant",
     lambda m: "OpenAlex often copies Crossref: not an independent second opinion"),
    (r"année à vérifier : référence (.+), source (.+) \(date de mise en ligne ou de dépôt possible\)",
     lambda m: f"year to check: reference {m[1]}, source {m[2]} (possibly an online or deposit date)"),
    (r"DOI disponible, absent de la référence : (.+)",
     lambda m: f"DOI available, missing from the reference: {m[1]}"),
    (r"édition (.+) absente d'Open Library \(titre et année non vérifiables\)",
     lambda m: f"{m[1]} edition not in Open Library (title and year not verifiable)"),
    (r"ouvrage absent d'Open Library", lambda m: "book not found in Open Library"),
    (r"(.+) : vérification manuelle", lambda m: f"{_type_en(m[1])}: manual check"),
    (r"DOI (\S+)", lambda m: f"DOI {m[1]}"),
]

SOURCES_EN = [
    (r"renvoie à « (.+) »", lambda m: f"points to “{m[1]}”"),
    (r"la notice ne cite que (.+)", lambda m: f"the record only lists {m[1]}"),
]


def _par_motifs(texte: str, motifs) -> str:
    for motif, f in motifs:
        m = re.fullmatch(motif, texte)
        if m:
            return f(m)
    return texte


def note_en(note: str) -> str:
    return _par_motifs(note, NOTES_EN)


def verdict(v: str, lang: str) -> str:
    return VERDICTS.get(v, {}).get(lang, v)


def ecarts(r: dict, lang: str) -> str:
    """Chaîne « écarts et notes » dans la langue voulue."""
    if lang != "en" or "details" not in r:
        return r["ecarts"]
    lignes = [f"{_champ_en(c)}: reference “{ref}” → source “{_par_motifs(src, SOURCES_EN)}”"
              for c, ref, src in r["details"]]
    lignes += [note_en(" ".join(str(n).split())) for n in r.get("notes", [])]
    return " ; ".join(lignes) or "—"


def traduire(r: dict, lang: str) -> dict:
    """Copie d'un résultat, verdict et écarts traduits."""
    t = dict(r)
    t["verdict_affiche"] = verdict(r["verdict"], lang)
    t["ecarts"] = ecarts(r, lang)
    return t


ENTETES = {
    "fr": ["n°", "référence", "verdict", "écarts et notes", "sources"],
    "en": ["no.", "reference", "verdict", "discrepancies and notes", "sources"],
}
TITRE_RAPPORT = {"fr": "Vérification bibliographique", "en": "Bibliography check"}
SYNTHESE = {"fr": "Synthèse", "en": "Summary"}
SOURCE = {"fr": "Source", "en": "Source"}


def tableau(resultats: list, lang: str) -> str:
    h = ENTETES[lang]
    lignes = ["| " + " | ".join(h) + " |", "|---|---|---|---|---|"]
    compte = {v: 0 for v in ("CONFIRMÉE", "ERREUR", "À VÉRIFIER", "À COMPLÉTER", "NON VÉRIFIABLE")}
    for r in sorted(resultats, key=lambda r: int(r["numero"])):
        compte[r["verdict"]] = compte.get(r["verdict"], 0) + 1
        lignes.append(f"| {r['numero']} | {r['reference']} | {verdict(r['verdict'], lang)} | "
                      f"{ecarts(r, lang)} | {r['sources']} |")
    lignes.append("")
    lignes.append(f"{SYNTHESE[lang]} : " + ", ".join(f"{n} {verdict(v, lang)}" for v, n in compte.items())
                  + f" (total {len(resultats)})")
    return "\n".join(lignes)


def ecrire_rapport(resultats: list, origine: str, lang: str) -> dict:
    """Enregistre …_verification.md et .csv à côté du fichier d'origine, dans la langue voulue."""
    tab = tableau(resultats, lang)
    base = os.path.splitext(origine)[0] + ("_verification" if lang == "fr" else "_check")
    fichiers = []
    try:
        with open(base + ".md", "w", encoding="utf-8") as f:
            f.write(f"# {TITRE_RAPPORT[lang]}\n\n{SOURCE[lang]} : {os.path.basename(origine)}\n\n{tab}\n")
        with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(ENTETES[lang])
            for r in sorted(resultats, key=lambda r: int(r["numero"])):
                w.writerow([r["numero"], r["reference"], verdict(r["verdict"], lang),
                            ecarts(r, lang), r["sources"]])
        fichiers = [base + ".md", base + ".csv"]
    except OSError as e:
        fichiers = [f"échec de l'enregistrement / could not save: {e}"]
    return {"tableau": tab, "fichiers": fichiers}
