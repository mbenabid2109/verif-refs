"""Vérification en ligne de commande, sans modèle de langage ni clé API.

Usage :
    python -m verif_refs.cli mabiblio.bib --contact moi@universite.fr
    python -m verif_refs.cli mabiblio.ris --contact moi@universite.fr
    python -m verif_refs.cli manuscrit.docx --contact moi@universite.fr   (mode texte, expérimental)

Pour les exports .bib et .ris (Zotero, Mendeley, EndNote), les champs sont déjà structurés :
aucun modèle n'est nécessaire. Pour un texte libre (.txt, .md, .docx), le type de chaque
référence est deviné par des règles simples ; la chaîne d'agents ADK reste préférable.
Le rapport est enregistré à côté du fichier source (…_verification.md et …_verification.csv).
"""

import argparse
import os
import re
import sys
import time

from . import core, i18n


class _Contexte:
    """Remplace le contexte d'ADK : un simple état en mémoire."""

    class _Etat(dict):
        def to_dict(self):
            return dict(self)

    def __init__(self, origine):
        self.state = self._Etat(origine=origine)


TYPES_ARTICLE = {"article", "jour", "ejour", "mgzn", "inproceedings", "conference", "conf", "cpaper"}
TYPES_LIVRE = {"book", "book_", "edbook", "ebook", "mvbook"}
LIBELLES = {"incollection": "chapitre d'ouvrage", "inbook": "chapitre d'ouvrage", "chap": "chapitre d'ouvrage",
            "phdthesis": "thèse", "mastersthesis": "mémoire", "thes": "thèse", "techreport": "rapport",
            "rprt": "rapport", "report": "rapport", "online": "page web", "elec": "page web",
            "news": "article de presse", "unpublished": "document non publié", "misc": "document",
            "gen": "document"}
TYPES_AUTRES = {"incollection", "inbook", "chap", "phdthesis", "mastersthesis", "thes", "techreport",
                "rprt", "report", "misc", "online", "elec", "news", "unpublished", "gen"}


def _premier_auteur(auteurs: list, brute: str) -> str:
    if auteurs:
        a = auteurs[0]
        return a.split(",")[0].strip() if "," in a else a.split()[-1]
    m = re.match(r"\s*((?:(?:van|von|der|de|del|di|da|du|le|la)\s+)*[^\s,(]+)", brute)
    return m.group(1) if m else ""


def _verifier_structure(n: int, c: dict, ctx) -> dict:
    brute = core._ref_depuis_champs(c)
    t = (c.get("type") or "").lower()
    if c.get("doi") or t in TYPES_ARTICLE or (c.get("revue") and t not in TYPES_LIVRE | TYPES_AUTRES):
        return core.verifier_article(n, brute, c.get("titre", ""), c.get("annee", ""), c.get("revue", ""),
                                     c.get("volume", ""), c.get("numero", ""), c.get("pages", ""),
                                     tool_context=ctx)
    if t in TYPES_LIVRE or not t:
        return core.verifier_ouvrage(n, brute, c.get("titre", ""), c.get("annee", ""),
                                     _premier_auteur(c.get("auteurs", []), brute), c.get("editeur", ""),
                                     tool_context=ctx)
    return core.enregistrer_non_verifiable(n, brute, LIBELLES.get(t, t or "document"), tool_context=ctx)


def _verifier_texte(n: int, brute: str, ctx) -> dict:
    """Mode texte : règles simples pour deviner le type (moins fiable que l'agent ADK)."""
    lu = core._extraire(brute)
    titre = core._titre_brut(brute)
    annee = lu.get("annee", "")
    if core._doi_brut(brute) or re.search(r"\bvol\b|\bn\s*[°o]|\d+\s*\(\d+[^)]*\)\s*,", brute, re.I):
        return core.verifier_article(n, brute, titre, annee, tool_context=ctx)
    if re.search(r"\bIn\s+[A-Z][^.]*\(Eds?\.|\(dir\.\)|thèse|thesis|dissertation|rapport|report|"
                 r"https?://(?!doi)", brute, re.I):
        return core.enregistrer_non_verifiable(n, brute, "chapitre, rapport ou page web", tool_context=ctx)
    return core.verifier_ouvrage(n, brute, titre, annee, _premier_auteur([], brute), tool_context=ctx)


def preparer(chemin: str):
    """Lit un fichier et renvoie (contexte, tâches, mode). Chaque tâche vérifie une référence.

    Lève ValueError si le fichier est illisible ou ne contient aucune référence.
    """
    ext = os.path.splitext(chemin)[1].lower()
    ctx = _Contexte(chemin)
    if ext in (".bib", ".ris"):
        with open(chemin, encoding="utf-8-sig", errors="replace") as f:
            texte = f.read()
        entrees = core._champs_bib(texte) if ext == ".bib" else core._champs_ris(texte)
        taches = [(lambda n, c=c: _verifier_structure(n, c, ctx)) for c in entrees]
        mode = "structuré"
    else:
        r = core.charger_fichier(chemin, tool_context=ctx)
        if r.get("statut") != "ok":
            raise ValueError(r.get("detail", "lecture impossible"))
        taches = [(lambda n, b=b: _verifier_texte(n, b, ctx)) for b in ctx.state["refs"]]
        mode = "texte"
    if not taches:
        raise ValueError("aucune référence reconnue dans ce fichier")
    return ctx, taches, mode


def verifier_fichier(chemin: str, pause: float = 0.3, progression=None, lang: str = "en"):
    """Vérifie toutes les références d'un fichier ; renvoie (résultats, rapport, mode).

    lang : langue du rapport ("en" ou "fr") ; la vérification elle-même ne change pas.

    progression(n, total, resultat) est appelée après chaque référence, si elle est fournie.
    """
    ctx, taches, mode = preparer(chemin)
    resultats = []
    for n, tache in enumerate(taches, 1):
        try:
            r = tache(n)
        except Exception as e:                       # une référence en échec n'arrête pas le reste
            r = core.enregistrer_non_verifiable(n, "référence n° %d" % n,
                                                "erreur de traitement (%s)" % core._message(e),
                                                tool_context=ctx)
        resultats.append(r)
        if progression:
            progression(n, len(taches), r)
        if pause:
            time.sleep(pause)
    return resultats, i18n.ecrire_rapport(resultats, chemin, lang), mode


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m verif_refs.cli",
                                 description="Audit de références bibliographiques (Crossref, DataCite, "
                                             "OpenAlex, Open Library), sans modèle de langage.")
    ap.add_argument("fichier", help=".bib, .ris, .txt, .md ou .docx")
    ap.add_argument("--contact", help="votre adresse électronique (demandée par Crossref et OpenAlex)")
    ap.add_argument("--pause", type=float, default=0.3, help="pause entre deux références, en secondes")
    ap.add_argument("--lang", choices=i18n.LANGUES, default="en",
                    help="langue du rapport : en (par défaut) ou fr / report language")
    a = ap.parse_args(argv)

    if a.contact:
        core.CONTACT = a.contact
    elif core.CONTACT.endswith("example.org"):
        print("Tip: give your e-mail address with --contact (Crossref usage policy). / "
              "Conseil : indiquez votre adresse avec --contact.", file=sys.stderr)

    chemin = os.path.abspath(a.fichier)
    if not os.path.isfile(chemin):
        sys.exit(f"Fichier introuvable : {chemin}")
    try:
        _, _, mode = preparer(chemin)
    except ValueError as e:
        sys.exit(str(e))
    if mode == "texte":
        print("Text mode (experimental): each reference type is guessed." if a.lang == "en" else
              "Mode texte (expérimental) : le type de chaque référence est deviné.", file=sys.stderr)
    _, rapport, _ = verifier_fichier(
        chemin, a.pause,
        lambda n, t, r: print(f"[{n}/{t}] {i18n.verdict(r['verdict'], a.lang):<15} {r['reference']}",
                              file=sys.stderr),
        lang=a.lang)
    print(rapport["tableau"])
    print(("\nReport saved: " if a.lang == "en" else "\nRapport enregistré : ")
          + ", ".join(rapport.get("fichiers", [])))


if __name__ == "__main__":
    main()
