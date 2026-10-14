"""Interface web bilingue (anglais / français) de verif-refs (Gradio), pour Hugging Face Spaces.

Aucune clé ni modèle de langage : la vérification est celle de la ligne de commande
(verif_refs.cli), entièrement déterministe.

Lancement local :  python space/app.py   puis ouvrir http://127.0.0.1:7860
Sur Hugging Face Spaces, définissez la variable VERIF_REFS_CONTACT (votre adresse),
transmise à Crossref et OpenAlex comme le demandent leurs règles d'usage.
"""

import html
import os
import shutil
import sys
import queue
import re
import tempfile
import threading

ICI = os.path.dirname(os.path.abspath(__file__))
for chemin in (ICI, os.path.dirname(ICI)):          # Space (verif_refs/ à côté) ou dépôt GitHub
    if os.path.isdir(os.path.join(chemin, "verif_refs")):
        sys.path.insert(0, chemin)
        break
else:
    # Space « à plat » : core.py et cli.py déposés à côté de app.py (l'envoi par le navigateur
    # transfère mal les sous-dossiers). On les regroupe en paquet verif_refs à la volée.
    import types
    if os.path.isfile(os.path.join(ICI, "core.py")) and os.path.isfile(os.path.join(ICI, "cli.py")):
        _paquet = types.ModuleType("verif_refs")
        _paquet.__path__ = [ICI]
        _paquet.__version__ = "5.2.0"
        sys.modules["verif_refs"] = _paquet

import gradio as gr

# Matériel ZeroGPU (seule option gratuite pour les nouveaux comptes Hugging Face) : le Space refuse
# de démarrer sans fonction marquée @spaces.GPU. L'outil n'utilise aucune carte graphique ; cette
# fonction vide, jamais appelée, sert uniquement à satisfaire ce contrôle de démarrage.
try:
    import spaces

    @spaces.GPU(duration=1)
    def _controle_zerogpu():
        return None
except ImportError:
    pass

CSS = """
.vr-wrap{max-width:100%;overflow-x:auto}
.vr-table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.45;border:none!important;margin:0!important}
.vr-table th,.vr-table td{border-left:none!important;border-right:none!important;border-top:none!important;background:transparent!important}
.vr-table th{text-align:left;font-weight:600;padding:8px 10px;border-bottom:2px solid var(--border-color-primary)!important}
.vr-table td{padding:8px 10px;border-bottom:1px solid var(--border-color-primary)!important;vertical-align:top}
.vr-table td.n{color:var(--body-text-color-subdued);width:2.5em}
.vr-table td.ref{min-width:11em}
.vr-table td.ec{min-width:16em}
.vr-badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.vr-badge.err{background:rgba(220,38,38,.14);color:#b91c1c}
.vr-badge.chk{background:rgba(217,119,6,.16);color:#a35a00}
.vr-badge.inc{background:rgba(37,99,235,.13);color:#1d4ed8}
.vr-badge.ok{background:rgba(22,163,74,.14);color:#15803d}
.vr-badge.nv{background:rgba(100,116,139,.16);color:#475569}
.dark .vr-badge.err{color:#fca5a5}.dark .vr-badge.chk{color:#fcd34d}.dark .vr-badge.inc{color:#93c5fd}
.dark .vr-badge.ok{color:#86efac}.dark .vr-badge.nv{color:#cbd5e1}
.vr-compte{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 12px}
.vr-compte span{font-size:13px}
.vr-src{color:var(--body-text-color-subdued);font-size:12px}
.vr-note{font-size:13px;color:var(--body-text-color-subdued)}
.vr-table tr,.vr-table thead,.vr-table tbody{border:none!important;background:transparent!important}
.vr-wrap{border:none!important}
@media (max-width:640px){
 .vr-table thead{display:none}
 .vr-table tr{display:block;padding:10px 0;border-bottom:1px solid var(--border-color-primary)!important}
 .vr-table td{display:block;border:none!important;padding:2px 0!important;min-width:0!important}
 .vr-table td.n{display:none}
 .vr-table td.ref{font-weight:600}
}
"""


from verif_refs import __version__, i18n
from verif_refs.cli import preparer, verifier_fichier

MAX_REFS = int(os.environ.get("VERIF_REFS_MAX", "150"))
EXEMPLE = next((p for p in (os.path.join(ICI, "exemple.bib"),
                            os.path.join(os.path.dirname(ICI), "examples", "exemple.bib"))
                if os.path.isfile(p)), None)
DEPOT = os.environ.get("VERIF_REFS_DEPOT", "https://github.com/")

CLASSES = {"ERREUR": "err", "À VÉRIFIER": "chk", "À COMPLÉTER": "inc", "CONFIRMÉE": "ok", "NON VÉRIFIABLE": "nv"}
ORDRE = list(i18n.VERDICTS)
LANGUES = {"English": "en", "Français": "fr"}

T = {
    "en": {
        "intro": "# verif-refs\n**Check your bibliography, field by field.** Each reference is compared with the "
                 "records of Crossref, DataCite, OpenAlex and Open Library: authors, initials, journal, volume, "
                 "issue, pages, subtitle, DOI. No sign-up, no key.",
        "fichier": "File · Fichier (.bib, .ris, .docx, .txt, .md)",
        "texte": "… or paste your bibliography",
        "exemple_texte": "One reference per paragraph, for example:\nWeaver, D. H. (1980). Audience need for "
                         "orientation and media effects. Communication Research, 7(3), 361-376.",
        "bouton": "Check",
        "rapport": "Report to download (.md, and .csv for Excel)",
        "entetes": ("No.", "Reference", "Verdict", "Discrepancies and notes · sources"),
        "format": "Unsupported format: use .bib, .ris, .txt, .md or .docx.",
        "rien": "Drop a file or paste a bibliography.",
        "lecture": "Could not read the file: {e}.",
        "trop": "{n} references found: this online version accepts {m} at most. Split the file, or use the command line.",
        "detectees": "{n} references found. Checking…",
        "en_cours": "{k}/{n} checked…",
        "interruption": "Interrupted: {e}",
        "mode_texte": "Text mode: each reference type (article, book…) is guessed by simple rules. "
                      "A .bib or .ris export from Zotero gives more reliable results.",
        "aide": "**How to read the results.** CONFIRMED only applies to the fields that were checked. "
                "TO CHECK on a book usually means an incomplete Open Library record, not an error. "
                "Reports, press articles, chapters and conference papers without a DOI are NOT VERIFIABLE: "
                "the sources queried do not hold them.\n\n"
                "**Privacy.** Your file is processed, then discarded; it is not kept. The text of each reference "
                "is sent to the public services Crossref, OpenAlex, DataCite and Open Library to be looked up.\n\n"
                "*Research prototype, no guaranteed support. Version {v}.* [Code, method and limitations]({d})",
    },
    "fr": {
        "intro": "# verif-refs\n**Vérifiez votre bibliographie, champ par champ.** Chaque référence est comparée aux "
                 "notices de Crossref, DataCite, OpenAlex et Open Library : auteurs, initiales, revue, volume, "
                 "numéro, pages, sous-titre, DOI. Aucune inscription, aucune clé.",
        "fichier": "File · Fichier (.bib, .ris, .docx, .txt, .md)",
        "texte": "… ou collez votre bibliographie",
        "exemple_texte": "Une référence par paragraphe, par exemple :\nWeaver, D. H. (1980). Audience need for "
                         "orientation and media effects. Communication Research, 7(3), 361-376.",
        "bouton": "Vérifier",
        "rapport": "Rapport à télécharger (.md, et .csv pour Excel)",
        "entetes": ("n°", "Référence", "Verdict", "Écarts et notes · sources"),
        "format": "Format non pris en charge : utilisez .bib, .ris, .txt, .md ou .docx.",
        "rien": "Déposez un fichier ou collez une bibliographie.",
        "lecture": "Lecture impossible : {e}.",
        "trop": "{n} références détectées : cette version en ligne en accepte {m} au plus. Découpez le fichier, "
                "ou utilisez la ligne de commande.",
        "detectees": "{n} références détectées. Vérification en cours…",
        "en_cours": "{k}/{n} vérifiées…",
        "interruption": "Interruption : {e}",
        "mode_texte": "Mode texte : le type de chaque référence (article, livre…) est deviné par des règles simples. "
                      "Un export .bib ou .ris de Zotero donne des résultats plus fiables.",
        "aide": "**Comment lire les résultats.** Un verdict CONFIRMÉE ne vaut que pour les champs vérifiés. "
                "À VÉRIFIER sur un livre signale le plus souvent une notice Open Library incomplète, pas une erreur. "
                "Les rapports, la presse, les chapitres et les communications sans DOI sont NON VÉRIFIABLE : "
                "les sources consultées ne les contiennent pas.\n\n"
                "**Confidentialité.** Le fichier est traité puis abandonné ; il n'est pas conservé. Le texte de "
                "chaque référence est envoyé aux services publics Crossref, OpenAlex, DataCite et Open Library "
                "pour y être recherché.\n\n"
                "*Prototype de recherche, sans support garanti. Version {v}.* [Code, méthode et limites]({d})",
    },
}


def _badge(verdict: str, lang: str) -> str:
    return (f'<span class="vr-badge {CLASSES.get(verdict, "nv")}" '
            f'title="{html.escape(i18n.EXPLICATIONS.get(verdict, {}).get(lang, ""))}">'
            f'{html.escape(i18n.verdict(verdict, lang))}</span>')


def _message(texte: str) -> str:
    return f'<p class="vr-note">{html.escape(texte)}</p>'


def _tableau(resultats: list, lang: str, total: int = 0) -> str:
    if not resultats:
        return ""
    compte = {v: 0 for v in ORDRE}
    for r in resultats:
        compte[r["verdict"]] = compte.get(r["verdict"], 0) + 1
    en_cours = (" — " + T[lang]["en_cours"].format(k=len(resultats), n=total)
                if total and len(resultats) < total else "")
    tete = ('<div class="vr-compte">' + "".join(f"<span>{_badge(v, lang)} {compte[v]}</span>"
                                                 for v in ORDRE if compte.get(v))
            + f'<span class="vr-note">{html.escape(en_cours)}</span></div>')
    lignes = []
    for r in sorted(resultats, key=lambda r: (ORDRE.index(r["verdict"]) if r["verdict"] in ORDRE else 9,
                                              int(r["numero"]))):
        ecarts = html.escape(i18n.ecarts(r, lang)).replace(" ; ", "<br>")
        lignes.append(
            f'<tr><td class="n">{r["numero"]}</td><td class="ref">{html.escape(r["reference"])}</td>'
            f'<td>{_badge(r["verdict"], lang)}</td><td class="ec">{ecarts}'
            f'<div class="vr-src">{html.escape(r["sources"])}</div></td></tr>')
    h = T[lang]["entetes"]
    return (tete + '<div class="vr-wrap"><table class="vr-table"><thead><tr>'
            + "".join(f"<th>{x}</th>" for x in h) + "</tr></thead><tbody>"
            + "".join(lignes) + "</tbody></table></div>")


def _avis(mode: str, lang: str) -> str:
    return "" if mode == "structuré" else _message(T[lang]["mode_texte"])


def verifier(fichier, texte_colle, langue):
    """Générateur : affiche les résultats au fur et à mesure. Renvoie (html, fichiers, état)."""
    lang = LANGUES.get(langue, "en")
    t = T[lang]
    dossier = tempfile.mkdtemp(prefix="verif_refs_")   # nettoyé par le système ; gardé pour le téléchargement
    if fichier:
        source = fichier if isinstance(fichier, str) else fichier.name
        nom = os.path.basename(source)
        ext = os.path.splitext(nom)[1].lower()
        if ext not in (".bib", ".ris", ".txt", ".md", ".docx"):
            yield _message(t["format"]), None, None
            return
        base = re.sub(r"[^\w-]+", "_", os.path.splitext(nom)[0]).strip("_")[:60] or "bibliography"
        chemin = os.path.join(dossier, base + ext)
        shutil.copy(source, chemin)
    elif texte_colle and texte_colle.strip():
        chemin = os.path.join(dossier, "bibliography.txt")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(texte_colle)
    else:
        yield _message(t["rien"]), None, None
        return

    try:
        _, taches, mode = preparer(chemin)
    except ValueError as e:
        yield _message(t["lecture"].format(e=e)), None, None
        return
    if len(taches) > MAX_REFS:
        yield _message(t["trop"].format(n=len(taches), m=MAX_REFS)), None, None
        return

    avis = _avis(mode, lang)
    resultats = []
    q = queue.Queue()        # verifier_fichier tourne dans un fil ; chaque résultat est affiché à son arrivée
    sortie = {}

    def travail():
        try:
            sortie["res"] = verifier_fichier(chemin, pause=0.2, lang=lang,
                                             progression=lambda n, tt, r: q.put(r))
        except Exception as e:  # noqa: BLE001
            sortie["erreur"] = e
        finally:
            q.put(None)

    threading.Thread(target=travail, daemon=True).start()
    total = len(taches)
    yield avis + _message(t["detectees"].format(n=total)), None, None
    while True:
        r = q.get()
        if r is None:
            break
        resultats.append(r)
        yield avis + _tableau(resultats, lang, total), None, None

    if "erreur" in sortie:
        yield avis + _tableau(resultats, lang) + _message(t["interruption"].format(e=sortie["erreur"])), None, None
        return
    _, rapport, _ = sortie["res"]
    fichiers = [f for f in rapport.get("fichiers", []) if os.path.isfile(f)]
    etat = {"resultats": resultats, "origine": chemin, "mode": mode}
    yield avis + _tableau(resultats, lang), fichiers or None, etat


def changer_langue(langue, etat):
    """Traduit l'interface et, s'il existe, le dernier résultat (tableau et rapport)."""
    lang = LANGUES.get(langue, "en")
    t = T[lang]
    sorties = [t["intro"], gr.update(label=t["fichier"]),
               gr.update(label=t["texte"], placeholder=t["exemple_texte"]),
               gr.update(value=t["bouton"]), t["aide"].format(v=__version__, d=DEPOT)]
    if etat and etat.get("resultats"):
        rapport = i18n.ecrire_rapport(etat["resultats"], etat["origine"], lang)
        fichiers = [f for f in rapport["fichiers"] if os.path.isfile(f)]
        sorties += [_avis(etat["mode"], lang) + _tableau(etat["resultats"], lang),
                    gr.update(label=t["rapport"], value=fichiers or None)]
    else:
        sorties += [gr.update(), gr.update(label=t["rapport"])]
    return sorties


def langue_du_navigateur(request: gr.Request):
    """Français si le navigateur le préfère ; anglais sinon."""
    try:
        accept = (request.headers.get("accept-language") or "").lower()
    except Exception:  # noqa: BLE001
        accept = ""
    return "Français" if accept.startswith("fr") else "English"


def au_chargement(request: gr.Request):
    """À l'ouverture : choisit la langue du navigateur et traduit toute l'interface d'un coup."""
    langue = langue_du_navigateur(request)
    return [langue] + changer_langue(langue, None)


def construire():
    t = T["en"]
    with gr.Blocks(title="verif-refs") as demo:
        etat = gr.State(None)
        with gr.Row():
            with gr.Column(scale=5):
                intro = gr.Markdown(t["intro"])
            with gr.Column(scale=1, min_width=200):
                langue = gr.Radio(list(LANGUES), value="English", show_label=False, container=False)
        with gr.Row(equal_height=False):
            with gr.Column(scale=1, min_width=280):
                fichier = gr.File(label=t["fichier"], file_types=[".bib", ".ris", ".docx", ".txt", ".md"],
                                  type="filepath")
                texte = gr.Textbox(label=t["texte"], lines=8, placeholder=t["exemple_texte"])
                bouton = gr.Button(t["bouton"], variant="primary")
                if EXEMPLE:
                    gr.Examples([[EXEMPLE]], inputs=[fichier], label="Example · Exemple (6 references)")
            with gr.Column(scale=2, min_width=320):
                resultat = gr.HTML()
                telechargement = gr.File(label=t["rapport"], file_count="multiple", interactive=False)
        aide = gr.Markdown(t["aide"].format(v=__version__, d=DEPOT))

        bouton.click(verifier, inputs=[fichier, texte, langue], outputs=[resultat, telechargement, etat],
                     concurrency_limit=4)
        langue.change(changer_langue, inputs=[langue, etat],
                      outputs=[intro, fichier, texte, bouton, aide, resultat, telechargement])
        demo.load(au_chargement, inputs=None,
                  outputs=[langue, intro, fichier, texte, bouton, aide, resultat, telechargement])
    return demo


if __name__ == "__main__":
    construire().queue(default_concurrency_limit=4).launch(css=CSS)
