"""verif-refs : vérification déterministe de références bibliographiques.

Ce module ne dépend que de la bibliothèque standard de Python. Il interroge Crossref,
DataCite, OpenAlex et Open Library, compare les champs de chaque référence à la notice
trouvée et rend un verdict : CONFIRMÉE, ERREUR, À VÉRIFIER, À COMPLÉTER ou NON VÉRIFIABLE.

Il est utilisé de deux façons :
- par la chaîne d'agents Google ADK (`agent.py`), pour les bibliographies en texte libre ;
- par la ligne de commande (`cli.py`), sans modèle de langage, pour les fichiers .bib et .ris.

Historique des versions : voir CHANGELOG.md.
"""

import difflib
import html
import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

try:                                    # annotation reconnue par ADK quand il est installé
    from google.adk.tools.tool_context import ToolContext
except ImportError:                     # utilisation en ligne de commande, sans ADK
    ToolContext = object

# Adresse de contact transmise à Crossref et OpenAlex (règle d'usage de leurs API).
# À définir dans le fichier .env : VERIF_REFS_CONTACT=votre.adresse@exemple.org
CONTACT = os.environ.get("VERIF_REFS_CONTACT", "contact-non-renseigne@example.org")
SEUIL_IDENTITE = 0.75  # similarité minimale des titres pour considérer que c'est le même document
SEUIL_COQUILLE = 0.85  # au-delà : même titre avec une coquille


# =====================================================================
# Accès aux sources
# =====================================================================

def _get_json(url: str, essais: int = 3) -> dict:
    """Requête JSON avec nouvelles tentatives (délai dépassé, 429, erreurs 5xx)."""
    import time
    req = urllib.request.Request(
        url, headers={"User-Agent": f"verif-refs/5.2 (mailto:{CONTACT})"}
    )
    for i in range(essais):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < essais - 1:
                time.sleep(2 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError):
            if i < essais - 1:
                time.sleep(2 * (i + 1))
                continue
            raise


def _message(e: Exception) -> str:
    """Message d'erreur lisible, même quand l'exception n'en a pas (délai dépassé)."""
    return f"{type(e).__name__}{(' : ' + str(e)) if str(e) else ''}"


def _crossref_notice(item: dict) -> dict:
    u = lambda x: " ".join(re.sub(r"<sup>.*?</sup>", "", html.unescape(x or ""), flags=re.S).split())

    def _annee(cle):
        return item.get(cle, {}).get("date-parts", [[None]])[0][0]

    return {
        "titre": u((item.get("title") or [""])[0]),
        "sous_titre": u((item.get("subtitle") or [""])[0]),
        "auteurs": [(u(a.get("family")), u(a.get("given"))) for a in item.get("author", [])],
        "annees": {a for a in (_annee("issued"), _annee("published-print"),
                               _annee("published-online")) if a},
        "revue": u((item.get("container-title") or [""])[0]),
        "volume": item.get("volume") or "",
        "numero": item.get("issue") or "",
        "pages": item.get("page") or "",
        "doi": item.get("DOI") or "",
    }


def _crossref(reference_brute: str, doi: str) -> list:
    """Renvoie une liste de notices candidates (la bonne en tête si DOI)."""
    doi = (doi or "").strip().removeprefix("https://doi.org/").removeprefix("doi:")
    if doi:
        try:
            d = _get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
            return [_crossref_notice(d["message"])]
        except Exception:
            pass
    q = urllib.parse.urlencode({"query.bibliographic": reference_brute, "rows": 5})
    d = _get_json("https://api.crossref.org/works?" + q)
    return [_crossref_notice(i) for i in d["message"].get("items", [])]


def _datacite(doi: str) -> dict:
    """Notice DataCite (rapports, preprints, jeux de données) pour un DOI absent de Crossref."""
    try:
        a = _get_json("https://api.datacite.org/dois/" + urllib.parse.quote(doi))["data"]["attributes"]
    except Exception:
        return {}
    auteurs = []
    for c in a.get("creators", []):
        fam, giv = c.get("familyName"), c.get("givenName")
        if not fam and "," in (c.get("name") or ""):
            fam, giv = [x.strip() for x in c["name"].split(",", 1)]
        auteurs.append((fam or c.get("name", ""), giv or ""))
    titres = a.get("titles") or [{}]
    an = a.get("publicationYear")
    return {"titre": html.unescape(titres[0].get("title", "")), "sous_titre": "",
            "auteurs": auteurs, "annees": {int(an)} if str(an).isdigit() else set(),
            "revue": a.get("publisher") if isinstance(a.get("publisher"), str)
            else (a.get("publisher") or {}).get("name", ""),
            "volume": "", "numero": "", "pages": "", "doi": a.get("doi", doi)}


def _openalex(doi: str) -> dict:
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi)
    cle = os.environ.get("OPENALEX_API_KEY")
    if cle:
        url += "?" + urllib.parse.urlencode({"api_key": cle})
    try:
        w = _get_json(url)
        b = w.get("biblio") or {}
        d, f = b.get("first_page"), b.get("last_page")
        return {"volume": b.get("volume") or "", "numero": b.get("issue") or "",
                "pages": f"{d}-{f}" if d and f else (d or ""),
                "annee": str(w.get("publication_year") or ""),
                "noms_complets": [(a.get("author") or {}).get("display_name") or ""
                                  for a in w.get("authorships", [])]}
    except Exception:
        return {}


def _openlibrary(titre: str, auteur: str) -> list:
    q = urllib.parse.urlencode({
        "title": titre, "author": auteur, "limit": 5,
        "fields": "title,subtitle,author_name,publish_year,publisher",
    })
    d = _get_json("https://openlibrary.org/search.json?" + q)
    notices = []
    for x in d.get("docs", []):
        auteurs = []
        for nom in x.get("author_name", []):
            morceaux = nom.split()
            auteurs.append((morceaux[-1], " ".join(morceaux[:-1])) if morceaux else ("", ""))
        notices.append({
            "titre": x.get("title") or "",
            "sous_titre": x.get("subtitle") or "",
            "auteurs": auteurs,
            "annees": set(x.get("publish_year", [])),
            "editeurs": x.get("publisher") or [],
        })
    return notices


# =====================================================================
# Normalisation et comparaisons (déterministes)
# =====================================================================

TIRETS = r"[\u2010\u2011\u2012\u2013\u2014\u2015\-]"


def _sans_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _norm(s: str, garder_signes: bool = False) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"<sup>.*?</sup>", " ", s, flags=re.S)  # appels de note
    s = re.sub(r"<[^>]+>", " ", s)                      # autres balises HTML de Crossref
    s = re.sub(r"(?<=[a-z])\d+\b", "", s)               # appels de note : "Piracy1"
    s = re.sub(TIRETS, " ", s)
    s = re.sub(r"['’‘`´]", "", s)
    s = s.lower().replace("&", " and ")
    motif = r"[^\w\s?!]" if garder_signes else r"[^\w\s]"
    s = re.sub(motif, " ", s)
    s = re.sub(r"\s*([?!])", r"\1", s)
    s = _sans_accents(s)                                # v5.2 : certaines notices n'ont pas d'accents
    return re.sub(r"\s+", " ", s).strip()


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _score_titre(ref: str, notice: dict) -> float:
    r = _norm(ref)
    t = _norm(notice["titre"])
    full = _norm(notice["titre"] + " " + notice["sous_titre"])
    if not r or not t:
        return 0.0
    if r in (t, full) or (len(t) >= 15 and r.startswith(t)) or (len(r) >= 15 and full.startswith(r)):
        return 1.0
    return max(_ratio(r, t), _ratio(r, full), _ratio(r[: len(t)], t))


def _comparer_titre(ref: str, notice: dict, ecarts: list):
    r, t = _norm(ref), _norm(notice["titre"])
    full = _norm(notice["titre"] + " " + notice["sous_titre"])
    rs = _norm(ref, True)
    ts = _norm(notice["titre"] + " " + notice["sous_titre"], True)
    if r in (t, full) or (len(t) >= 15 and r.startswith(t)):
        for signe in "?!":
            if signe in ts and signe not in rs:
                ecarts.append(("ERREUR", "titre", ref, (notice["titre"] + " " + notice["sous_titre"]).strip()))
                return
        if r == t and notice["sous_titre"] and full != t:
            ecarts.append(("À COMPLÉTER", "sous-titre", "—", notice["sous_titre"]))
        return
    if len(r) >= 15 and full.startswith(r):
        ecarts.append(("À COMPLÉTER", "titre (partie manquante)", ref,
                       (notice["titre"] + " " + notice["sous_titre"]).strip()))
        return
    ecarts.append(("ERREUR", "titre", ref, (notice["titre"] + " " + notice["sous_titre"]).strip()))


def _initiales(s: str) -> list:
    s = re.sub(TIRETS, " ", s or "")
    return [m.upper() for m in re.findall(r"(?:^|[\s.])([A-Za-zÀ-ÿ])", s)]


PARTICULES = {"et", "al", "and", "jr", "sr", "ii", "iii", "eds", "ed", "dir", "coord", "de", "del",
              "der", "van", "von", "la", "le", "du", "da", "dos", "des", "y", "the"}


def _segment_auteurs(brute: str) -> str:
    """Partie de la référence qui précède l'année : « Nom, I., Nom, I. (2020) »."""
    t = unicodedata.normalize("NFKC", brute)
    m = re.search(r"\(\s*(?:[^()]*?)(?:19|20)\d{2}", t)
    return t[: m.start()] if m else t.split(".")[0]


def _noms_de_la_reference(brute: str) -> list:
    """Mots du segment auteurs qui ne sont ni des initiales ni des particules."""
    seg = _segment_auteurs(brute)
    mots = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’]+", re.sub(TIRETS, " ", seg))
    return [m for m in mots if m.lower() not in PARTICULES]


def _comparer_auteurs(brute: str, auteurs_source: list, ecarts: list, notes: list,
                      fiable: bool = True):
    """Travaille sur le texte BRUT de la référence, pas sur l'extraction du modèle.

    fiable=False (notices d'ouvrages d'Open Library, souvent incomplètes ou fusionnées) :
    les absences et les initiales supplémentaires deviennent de simples notes ; seules les
    contradictions (initiales différentes, ordre inversé, nom mal orthographié) restent signalées.
    """
    if not auteurs_source:
        notes.append("auteurs absents de la source")
        return
    texte = unicodedata.normalize("NFKC", brute)
    texte_plat = _sans_accents(texte).lower()
    segment = _segment_auteurs(texte)
    et_al = bool(re.search(r"\bet al\b", segment))
    ellipse = bool(re.search(r"\.\s?\.\s?\.|…", segment))         # V2 : abréviation APA (21 auteurs et plus)
    positions, trouves, curseur = [], [], 0
    dernier = len(auteurs_source) - 1
    for rang, (famille, prenoms) in enumerate(auteurs_source):
        famille = unicodedata.normalize("NFKC", famille or "").strip()
        if not famille:
            continue
        motif = re.compile(r"(?<!\w)" + re.escape(famille) + r"(?!\w)")
        m = motif.search(texte, curseur) or motif.search(texte)
        if m:
            pos, fin = m.start(), m.end()
        else:
            cible = _sans_accents(famille).lower()
            m2 = re.search(r"(?<!\w)" + re.escape(cible) + r"(?!\w)", texte_plat)
            if m2:
                pos, fin = m2.start(), m2.end()
                ecrit = texte[pos:fin]
                if not famille.isupper() and _sans_accents(ecrit) != _sans_accents(famille):
                    ecarts.append(("ERREUR", "auteur (majuscules)", ecrit, famille))
            else:
                # v5.2 : nom de famille composé dans la source (« Gene Zucker », « Molavi Kakhki »)
                parties = [w for w in re.split(r"[\s\-]+", famille) if len(w) >= 3]
                trouve = None
                if len(parties) >= 2:
                    for w in reversed(parties):
                        m4 = re.search(r"(?<!\w)" + re.escape(_sans_accents(w).lower()) + r"(?!\w)",
                                       _sans_accents(segment).lower())
                        if m4:
                            trouve = (w, m4)
                            break
                if trouve:
                    w, m4 = trouve
                    ecarts.append(("À VÉRIFIER", "nom de famille composé", w, famille))
                    positions.append(m4.start())
                    trouves.append((m4.start(), famille))
                    continue
                autres = {_sans_accents(f or "").lower() for f, _ in auteurs_source}
                mots = [w for w in re.findall(r"[A-Za-zÀ-ÿ][\wÀ-ÿ'\-]+", segment)
                        if _sans_accents(w).lower() not in autres]
                proche = max(mots, key=lambda w: _ratio(w.lower(), famille.lower()), default="")
                if proche and _ratio(proche.lower(), famille.lower()) >= 0.75:
                    ecarts.append(("ERREUR", "auteur", proche, famille))
                    positions.append(texte.find(proche))
                elif et_al:
                    pass
                elif ellipse and rang != dernier:
                    pass                                              # omis légitimement par l'APA
                elif ellipse and rang == dernier:
                    ecarts.append(("ERREUR", "dernier auteur (abréviation APA)", "—", famille))
                elif not fiable:
                    notes.append(f"la notice d'ouvrage mentionne aussi « {famille} » (non bloquant)")
                else:
                    ecarts.append(("ERREUR", "auteur omis", "—", famille))   # règle v5 : ERREUR
                continue
        positions.append(pos)
        trouves.append((pos, famille))
        curseur = fin
        suite = texte[fin: fin + 16]
        m3 = re.match(r"[\s,]*((?:[A-Z]\.?(?![a-z])[\s\-]*){1,4})", suite)
        if m3 and prenoms:
            ref_i = re.findall(r"[A-Z]", m3.group(1))
            src_i = _initiales(prenoms)
            if any(a != b for a, b in zip(ref_i, src_i)):
                ecarts.append(("ERREUR", f"initiales de {famille}", m3.group(1).strip(),
                               ".".join(src_i) + "."))
            elif len(ref_i) > len(src_i) and src_i:
                # V5 : initiales supplémentaires non attestées par la source
                if fiable:
                    ecarts.append(("À VÉRIFIER", f"initiales de {famille} (en excès)",
                                   m3.group(1).strip(), ".".join(src_i) + "."))
                else:
                    notes.append(f"initiales de {famille} : la notice d'ouvrage n'en donne que "
                                 f"{'.'.join(src_i)}. (non bloquant)")
    if len(positions) >= 2 and positions != sorted(positions):
        ecarts.append(("ERREUR", "ordre des auteurs",
                       ", ".join(f for _, f in sorted(trouves)),
                       ", ".join(f for f, _ in auteurs_source)))
    # V3 : contrôle inverse — noms de la référence absents de la source
    familles = " ".join(_sans_accents(f or "").lower() for f, _ in auteurs_source)
    familles += " " + " ".join(_sans_accents(p or "").lower() for _, p in auteurs_source)
    inconnus = []
    for nom in _noms_de_la_reference(brute):
        n = _sans_accents(nom).lower()
        if n not in familles and not any(_ratio(n, w) >= 0.75 for w in familles.split()):
            inconnus.append(nom)
    if inconnus and not (et_al or ellipse):
        noms = ", ".join(dict.fromkeys(inconnus))
        if not fiable and len(auteurs_source) == 1:
            # v5.2 : notice d'ouvrage réduite au premier auteur. On ne confirme pas pour autant :
            # c'est exactement la situation d'une fausse confirmation (auteur omis ou déformé).
            ecarts.append(("À VÉRIFIER", "coauteurs non vérifiables (notice incomplète)", noms,
                           f"la notice ne cite que {auteurs_source[0][0]}"))
        else:
            ecarts.append(("À VÉRIFIER", "noms absents de la source", noms,
                           "; ".join(f for f, _ in auteurs_source)))


def _norm_revue(s: str) -> str:
    s = re.sub(r"\([^)]*\)", " ", html.unescape(s or ""))
    s = " " + _sans_accents(_norm(s)) + " "
    s = s.replace(" and ", " ").replace(" et ", " ")
    return re.sub(r"\s+", " ", re.sub(r"^ the ", " ", s)).strip()


def _revues_differentes(ref: str, src: str) -> bool:
    a, b = _norm_revue(ref), _norm_revue(src)
    # V4 : les intitulés d'actes varient trop d'une source à l'autre ; le DOI identifie la publication
    actes = r"proceedings|conference|symposium|workshop|actes|colloque"
    if re.search(actes, a) and re.search(actes, b):       # les deux sont des actes : pas de comparaison
        return False
    return bool(a and b) and a != b and _ratio(a, b) < 0.92


def _pages(s: str) -> str:
    return re.sub(r"\s+", "", re.sub(TIRETS, "-", str(s or "")))


def _extraire(brute: str) -> dict:
    """Lit année, volume, numéro et pages directement dans la référence brute."""
    t = unicodedata.normalize("NFKC", brute)
    t = re.sub(TIRETS, "-", t)
    out = {}
    m = re.search(r"\((?:[^()]*?)((?:19|20)\d{2})", t) or re.search(r"\b((?:19|20)\d{2})\b", t)
    if m:
        out["annee"] = m.group(1)
    m = re.search(r"\bvol\.?\s*(\d+)", t, re.I)
    if m:
        out["volume"] = m.group(1)
    m = re.search(r"\bn\s*[°o]\.?\s*(\d+(?:\s*-\s*\d+)?)", t, re.I)
    if m:
        out["numero"] = re.sub(r"\s", "", m.group(1))
    m = re.search(r"\bpp?\.\s*(\d+(?:\s*-\s*\d+)?)", t)
    if m:
        out["pages"] = re.sub(r"\s", "", m.group(1))
    m = re.search(r",\s*(\d+)\s*\((\d+(?:-\d+)?)\)\s*,\s*(e?\d+(?:\s*-\s*\d+)?)", t)   # APA 67(5), 422-436
    if m:
        out.setdefault("volume", m.group(1))
        out.setdefault("numero", m.group(2))
        out.setdefault("pages", re.sub(r"\s", "", m.group(3)))
    m = re.search(r",\s*(\d+)\s*\((\d+(?:-\d+)?)\)\s*[.,]", t)       # APA sans pages : 25(3).
    if m:
        out.setdefault("volume", m.group(1))
        out.setdefault("numero", m.group(2))
    if "pages" not in out:                                   # actes : « …, 7088-7105. »
        sans_url = re.sub(r"https?://\S+|10\.\d{4,9}/\S+", " ", t)
        tous = re.findall(r",\s*(\d{1,6}\s*-\s*\d{1,6})\s*[.,]?\s*(?:$|[A-Z(])", sans_url)
        if tous:
            out["pages"] = re.sub(r"\s", "", tous[-1])
    return out


def _doi_brut(brute: str) -> str:
    m = re.search(r"10\.\d{4,9}/[^\s]+", re.sub(r"\s+", "", brute.split("doi.org/")[-1])
                  if "doi.org/" in brute else brute)
    return m.group().rstrip(".,;") if m else ""


def _titre_brut(brute: str) -> str:
    """Titre approximatif : ce qui suit « (année). » ou « (année), » jusqu'au point suivant."""
    t = unicodedata.normalize("NFKC", brute)
    m = re.search(r"\((?:[^()]*?)(?:19|20)\d{2}[a-z]?[^)]*\)\s*[.,]?\s*", t)
    reste = t[m.end():] if m else t
    fin = re.search(r"(?<=[a-zà-ÿ0-9)?!])[.?!]\s+(?=[A-ZÀ-Ý(])", reste)
    return (reste[: fin.start() + 1] if fin else reste[:200]).strip(" .")


def _num_norm(s) -> str:
    """« Vol. 43 » → « 43 » ; « Suppl. 1 » et « Suppl_1 » → « s1 » ; « 3–4 » → « 3-4 »."""
    s = _sans_accents(re.sub(TIRETS, "-", str(s or ""))).lower().replace("_", " ")
    s = re.sub(r"\b(vol(ume)?|tome|t|no|n|num(ero)?|issue|nr)\b\.?", " ", s)
    s = re.sub(r"\b(suppl(ement)?|supp|s)\b\.?[\s_]*", "s", s)
    s = s.replace("°", " ")
    return re.sub(r"[^0-9a-z\-]", "", s)


def _nombres(s) -> set:
    """Ensemble des entiers d'un champ, intervalles développés (« 3-4 » → {3, 4})."""
    out = set()
    for a, b in re.findall(r"(\d+)(?:\s*-\s*(\d+))?", re.sub(TIRETS, "-", str(s or ""))):
        a = int(a)
        b = int(b) if b else a
        out.update(range(a, b + 1) if 0 <= b - a <= 10 else (a, b))
    return out


def _entier(s):
    m = re.search(r"\d+", str(s or ""))
    return int(m.group()) if m else None


# =====================================================================
# Enregistrement des résultats (dans l'état de la session)
# =====================================================================

def _verdict(ecarts: list) -> str:
    niveaux = {e[0] for e in ecarts}
    for v in ("ERREUR", "À VÉRIFIER", "À COMPLÉTER"):
        if v in niveaux:
            return v
    return "CONFIRMÉE"


def _etiquette(brute: str) -> str:
    tete = brute.split(")")[0] + ")" if ")" in brute else brute
    return tete[:60]


def _enregistrer(tool_context, numero, brute, verdict, ecarts, sources, notes):
    net = lambda x: " ".join(str(x).split())
    lignes = [f"{c} : référence « {net(r)} » → source « {net(s)} »" for _, c, r, s in ecarts]
    notes = [net(n) for n in notes]
    resultat = {
        "numero": numero,
        "reference": _etiquette(brute),
        "verdict": verdict,
        "ecarts": " ; ".join(lignes + notes) or "—",
        "sources": ", ".join(sources) or "—",
        # forme structurée, utilisée pour traduire le rapport (verif_refs.i18n)
        "details": [(c, net(r), net(s_)) for _, c, r, s_ in ecarts],
        "notes": notes,
    }
    if tool_context is not None:
        tool_context.state[f"res_{int(numero):03d}"] = resultat
    return resultat


# =====================================================================
# Outils exposés au modèle
# =====================================================================

def verifier_article(numero: int, reference_brute: str, titre: str, annee: str,
                     revue: str = "", volume: str = "", numero_fascicule: str = "",
                     pages: str = "",
                     tool_context: ToolContext = None) -> dict:
    """Vérifie un ARTICLE DE REVUE contre Crossref (et OpenAlex en cas de divergence).

    Args:
        numero: le numéro de la référence dans la liste.
        reference_brute: la référence complète, copiée exactement, caractère par caractère.
        titre: le titre de l'article (avec sous-titre), copié tel quel.
        annee: l'année indiquée dans la référence.
        revue: le nom de la revue tel qu'écrit ("" si absent).
        volume: le volume ("" si absent).
        numero_fascicule: le numéro du fascicule ("" si absent).
        pages: les pages, par ex. "63-71" ("" si absent).
    """
    sources, notes, ecarts = ["Crossref"], [], []
    # les champs numériques sont relus dans le texte brut : le modèle peut mal les recopier
    lu = _extraire(reference_brute)
    annee = lu.get("annee", annee)
    volume = lu.get("volume", volume if (str(volume) in reference_brute
                                         and not re.search(r"n\s*[°o]", str(volume), re.I)) else "")
    numero_fascicule = lu.get("numero", numero_fascicule if str(numero_fascicule) in reference_brute else "")
    pages = lu.get("pages", pages if _pages(pages) in _pages(reference_brute) else "")
    doi = _doi_brut(reference_brute)          # V5-3 : uniquement le DOI écrit dans la référence
    if titre and _norm(titre) not in _norm(reference_brute):
        notes.append("titre recopié par le modèle différent du texte brut (à vérifier)")
    try:
        candidats = _crossref(reference_brute, doi)
    except Exception as e:
        return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                            sources, [f"erreur d'accès à Crossref ({_message(e)})"])
    if doi:
        # V1 : si la référence porte un DOI, seule une notice portant CE DOI peut être le même document
        memes = [c for c in candidats if c.get("doi", "").lower() == doi.lower()]
        if not memes:
            dc = _datacite(doi)
            if dc:
                sources.append("DataCite")
                candidats = [dc]
            else:
                return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                                    sources, [f"DOI {doi} absent de Crossref et de DataCite"])
        else:
            candidats = memes
    scores = [(_score_titre(titre, c), c) for c in candidats]
    score, n = max(scores, key=lambda x: x[0]) if scores else (0, None)
    if not n or score < SEUIL_IDENTITE:
        if doi and n and n.get("doi", "").lower() == doi.lower():
            return _enregistrer(tool_context, numero, reference_brute, "ERREUR",
                                [("ERREUR", "DOI", doi, f"renvoie à « {n['titre']} »")], sources, [])
        return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                            sources, ["aucune notice correspondante dans Crossref"])

    oa = None

    def openalex():
        nonlocal oa
        if oa is None:
            oa = _openalex(n["doi"]) if n["doi"] else {}
            if oa:
                sources.append("OpenAlex")
        return oa

    a_ref = _entier(annee)
    revue_diff = bool(revue) and _revues_differentes(revue, n["revue"])
    annee_diff = bool(a_ref and n["annees"] and a_ref not in n["annees"])
    if annee_diff and _entier(openalex().get("annee")) == a_ref:
        annee_diff = False
        notes.append(f"année : divergence Crossref ({'/'.join(map(str, sorted(n['annees'])))}), "
                     f"confirmée par OpenAlex")
    if revue_diff and annee_diff:
        return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                            sources, [f"document apparenté (autre publication) : {n['titre']}, "
                                      f"{n['revue']}, {min(n['annees'])}, DOI {n['doi']}"])

    _comparer_auteurs(reference_brute, n["auteurs"], ecarts, notes)
    _comparer_titre(titre, n, ecarts)
    annee_src = "/".join(map(str, sorted(n["annees"])))
    if revue_diff:
        ecarts.append(("ERREUR", "revue", revue, n["revue"]))

    # volume / numéro / pages : les valeurs contradictoires passent par OpenAlex
    def second_avis(champ, valeur_ref):
        v = openalex().get(champ, "")
        return v and (_pages(v) if champ == "pages" else str(v)) == valeur_ref

    for champ, v_ref, v_src in (("volume", str(volume).strip(), str(n["volume"])),
                                ("numero", str(numero_fascicule).strip(), str(n["numero"]))):
        if not v_src:
            continue
        if not v_ref:
            # v5.2 : la référence donne la numérotation de la revue sous forme de numéro (« 106–107 »)
            # là où la source enregistre un volume (106) : même information, rangée autrement
            if champ == "volume" and _nombres(numero_fascicule) & _nombres(v_src):
                continue
            # numéro cumulé rangé par Crossref dans « volume » alors que la référence le donne comme numéro
            if champ == "volume" and re.search(r"n\s*[°o]", v_src, re.I):
                e_num = _entier(numero_fascicule)
                if e_num and _entier(v_src) == e_num:
                    continue
                ecarts.append(("À COMPLÉTER", "numéro cumulé", str(numero_fascicule) or "—", v_src))
                continue
            ecarts.append(("À COMPLÉTER", champ, "—", v_src))
        elif v_ref != v_src:
            e_ref, e_src = _entier(v_ref), _entier(v_src)
            if _num_norm(v_ref) == _num_norm(v_src):
                continue                                  # v5.2 : même valeur, écriture différente
            if champ == "numero" and len(_nombres(v_ref)) > 1 and (
                    _nombres(v_ref) & (_nombres(v_src) | _nombres(n["volume"]))):
                notes.append(f"numéro double « {v_ref} » : la source n'en enregistre qu'une partie ({v_src})")
                continue                                  # v5.2 : numéros doubles (Persée, Cairn)
            if e_ref and e_src and e_src >= 5 * e_ref and e_src > 12:
                ecarts.append(("À COMPLÉTER", "numéro cumulé", v_ref, v_src))
            elif second_avis(champ, v_ref):
                notes.append(f"{champ} : divergence Crossref ({v_src}), confirmé par OpenAlex")
            else:
                ecarts.append(("ERREUR", champ, v_ref, v_src))

    p_ref, p_src = _pages(pages), _pages(n["pages"])
    if p_src:
        if not p_ref:
            ecarts.append(("À COMPLÉTER", "pages", "—", p_src))
        elif p_ref != p_src:
            if "-" not in p_ref and p_src.split("-")[0] == p_ref:
                ecarts.append(("À COMPLÉTER", "pages", p_ref, p_src))
            elif "-" not in p_src and p_ref.split("-")[0] == p_src:
                notes.append(f"pages : la source ne donne que la première page ({p_src})")
            elif "-" in p_ref and re.search(
                    r"(?<!\d)" + r"\D{1,3}".join(map(re.escape, p_ref.split("-"))) + r"$", n["doi"].lower()):
                notes.append(f"pages : divergence Crossref ({p_src}), les pages {p_ref} "
                             f"sont confirmées par le DOI lui-même")
            elif second_avis("pages", p_ref):
                notes.append(f"pages : divergence Crossref ({p_src}), confirmé par OpenAlex")
            else:
                ecarts.append(("ERREUR", "pages", p_ref, p_src))
                if oa:
                    notes.append("OpenAlex reprend souvent Crossref : second avis non indépendant")

    excedents = [e for e in ecarts if e[1].endswith("(en excès)")]
    if excedents and n["doi"]:
        complets = openalex().get("noms_complets") or []
        for e in excedents:
            famille = e[1][len("initiales de "):-len(" (en excès)")]
            for nom in complets:
                if _sans_accents(famille).lower() in _sans_accents(nom).lower():
                    prenoms = re.sub(re.escape(famille), " ", nom, flags=re.I)
                    ref_i = re.findall(r"[A-Z]", e[2])
                    if _initiales(prenoms)[: len(ref_i)] == ref_i:
                        ecarts.remove(e)
                        notes.append(f"initiales de {famille} confirmées par OpenAlex ({nom})")
                    break
    if annee_diff:
        concordance = (p_ref and p_ref == p_src) or (
            str(volume).strip() and str(volume).strip() == str(n["volume"])
            and str(numero_fascicule).strip() == str(n["numero"]))
        if concordance and not any(e[1] in ("volume", "numero", "pages") and e[0] == "ERREUR"
                                   for e in ecarts):
            notes.append(f"année à vérifier : référence {annee}, source {annee_src} "
                         f"(date de mise en ligne ou de dépôt possible)")
        else:
            ecarts.append(("ERREUR", "année", annee, annee_src))
    note_doi = (f"DOI {n['doi']}" if doi else
                f"DOI disponible, absent de la référence : {n['doi']}" if n["doi"] else "")
    return _enregistrer(tool_context, numero, reference_brute, _verdict(ecarts),
                        ecarts, sources, notes + ([note_doi] if note_doi else []))


def verifier_ouvrage(numero: int, reference_brute: str, titre: str, annee: str,
                     premier_auteur: str, editeur: str = "",
                     tool_context: ToolContext = None) -> dict:
    """Vérifie un LIVRE contre Open Library.

    Args:
        numero: le numéro de la référence dans la liste.
        reference_brute: la référence complète, copiée exactement, caractère par caractère.
        titre: le titre de l'ouvrage (avec sous-titre), copié tel quel.
        annee: l'année indiquée dans la référence.
        premier_auteur: le nom de famille du premier auteur, tel qu'écrit.
        editeur: l'éditeur tel qu'écrit ("" si absent).
    """
    if _doi_brut(reference_brute):              # V5-4 : un DOI impose la vérification par le DOI
        return verifier_article(numero, reference_brute, _titre_brut(reference_brute),
                                annee, tool_context=tool_context)
    sources, notes, ecarts = ["Open Library"], [], []
    annee = _extraire(reference_brute).get("annee", annee)
    try:
        candidats = _openlibrary(re.split(r"\s[:.]\s|:\s", titre)[0], premier_auteur)
    except Exception as e:
        return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                            sources, [f"erreur d'accès à Open Library ({_message(e)})"])
    scores = [(_score_titre(titre, c), c) for c in candidats]
    score, n = max(scores, key=lambda x: x[0]) if scores else (0, None)
    if not n or score < SEUIL_IDENTITE:
        return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                            sources, ["ouvrage absent d'Open Library"])

    _comparer_auteurs(reference_brute, n["auteurs"], ecarts, notes, fiable=False)
    a_ref = _entier(annee)
    if a_ref and n["annees"] and a_ref not in n["annees"]:
        # édition non recensée : seules les erreurs d'auteur restent significatives
        notes.append(f"édition {a_ref} absente d'Open Library (titre et année non vérifiables)")
        verdict = "ERREUR" if any(e[0] == "ERREUR" for e in ecarts) else "NON VÉRIFIABLE"
        return _enregistrer(tool_context, numero, reference_brute, verdict,
                            [e for e in ecarts if e[0] == "ERREUR"], sources, notes)
    if score < 1.0:
        _comparer_titre(titre, n, ecarts)
    if not editeur.strip() and n["editeurs"]:
        ecarts.append(("À COMPLÉTER", "éditeur", "—", " / ".join(n["editeurs"][:3])))
    return _enregistrer(tool_context, numero, reference_brute, _verdict(ecarts),
                        ecarts, sources, notes)


def enregistrer_non_verifiable(numero: int, reference_brute: str, type_document: str,
                               tool_context: ToolContext = None) -> dict:
    """Enregistre un document hors du champ des sources (thèse, rapport, communication,
    presse professionnelle, chapitre, page web).

    Args:
        numero: le numéro de la référence dans la liste.
        reference_brute: la référence complète, copiée exactement.
        type_document: par exemple "thèse", "rapport", "communication", "presse professionnelle".
    """
    if _doi_brut(reference_brute):              # V5-4 : un DOI impose la vérification par le DOI
        return verifier_article(numero, reference_brute, _titre_brut(reference_brute),
                                _extraire(reference_brute).get("annee", ""), tool_context=tool_context)
    return _enregistrer(tool_context, numero, reference_brute, "NON VÉRIFIABLE", [],
                        [], [f"{type_document} : vérification manuelle"])


def synthese(tool_context: ToolContext = None) -> dict:
    """Renvoie le tableau final et le décompte. À appeler UNE SEULE FOIS, dans un tour séparé,
    APRÈS avoir reçu les résultats de TOUTES les vérifications (jamais en même temps qu'elles)."""
    etat = tool_context.state.to_dict() if tool_context is not None else {}
    res = sorted((v for k, v in etat.items() if k.startswith("res_") and v),
                 key=lambda r: int(r["numero"]))
    lignes = ["| n° | référence | verdict | écarts et notes | sources |",
              "|---|---|---|---|---|"]
    compte = {"CONFIRMÉE": 0, "ERREUR": 0, "À VÉRIFIER": 0, "À COMPLÉTER": 0, "NON VÉRIFIABLE": 0}
    for r in res:
        compte[r["verdict"]] = compte.get(r["verdict"], 0) + 1
        lignes.append(f"| {r['numero']} | {r['reference']} | {r['verdict']} | "
                      f"{r['ecarts']} | {r['sources']} |")
    lignes.append("")
    lignes.append("Synthèse : " + ", ".join(f"{v} {k}" for k, v in compte.items())
                  + f" (total {len(res)})")
    if tool_context is not None:
        for k in list(etat):
            if k.startswith("res_"):
                tool_context.state[k] = None
    return {"tableau": "\n".join(lignes)}


# =====================================================================
# Chargement d'une bibliographie (fichier ou texte collé)
# =====================================================================

TAILLE_LOT = 10
TITRES_BIBLIO = re.compile(r"^\s*(r[ée]f[ée]rences(\s+bibliographiques)?|bibliograph(ie|y)|works cited|sources)\s*:?\s*$", re.I)
FIN_BIBLIO = re.compile(r"^\s*(annexes?|appendix|appendices|tables?|figures?|notes?)\b", re.I)
DEBUT_REF = re.compile(r"^(?:(?:van|von|der|den|de|del|della|di|da|dos|du|le|la|ter|ten)\s+|d['’])*"
                       r"[A-ZÀ-Ý][\w’'\-]+(?:[ -][A-ZÀ-Ý]?[\w’'\-]+)*,?\s+(?:[A-ZÀ-Ý]\.|[A-ZÀ-Ý][a-z]+\b)")


def _paragraphes_docx(chemin: str) -> list:
    import zipfile
    import xml.etree.ElementTree as ET
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(chemin) as z:
        racine = ET.fromstring(z.read("word/document.xml"))
    paras = []
    for p in racine.iter("{%s}p" % ns["w"]):
        morceaux = []
        for el in p.iter():
            if el.tag == "{%s}t" % ns["w"] and el.text:
                morceaux.append(el.text)
            elif el.tag in ("{%s}tab" % ns["w"], "{%s}br" % ns["w"]):
                morceaux.append(" ")
        paras.append("".join(morceaux).strip())
    return paras


def _section_biblio(lignes: list) -> list:
    """Garde ce qui suit le dernier titre « Références / Bibliographie », jusqu'aux annexes."""
    debut = max((i for i, l in enumerate(lignes) if TITRES_BIBLIO.match(l)), default=-1)
    corps = lignes[debut + 1:] if debut >= 0 else lignes
    for i, l in enumerate(corps):
        if i > 3 and FIN_BIBLIO.match(l) and len(l) < 40:
            return corps[:i]
    return corps


def _en_tete_de_page(l: str) -> bool:
    """« POLITICAL COMMUNICATION 25 », « 26 M. A. BROWN ET AL. », numéro de page seul."""
    l = l.strip()
    lettres = [c for c in l if c.isalpha()]
    return bool(l) and (re.fullmatch(r"\d{1,4}", l) is not None or (
        len(l) < 70 and re.search(r"\d", l) and lettres
        and sum(c.isupper() for c in lettres) / len(lettres) > 0.8))


def _nettoyer(refs: list) -> list:
    propres = []
    for r in refs:
        r = re.sub(r"\s+", " ", r).strip()
        r = re.sub(r"^\s*(\d+[.)]|[-•*])\s+", "", r)
        r = re.sub(r"\s*Consulter( sur Cairn\.info)?\s*$", "", r)
        if len(r) < 25 or re.match(r"^\d+\s*$|^Consulter", r):
            continue
        propres.append(r)
    return propres


def _decouper_texte(texte: str) -> list:
    """Découpe un texte en références : lignes vides si présentes, sinon débuts de référence."""
    texte = texte.replace("\r\n", "\n")
    lignes = [l.rstrip() for l in texte.split("\n") if not _en_tete_de_page(l)]
    lignes = _section_biblio([l for l in lignes]) if any(TITRES_BIBLIO.match(l) for l in lignes) else lignes
    blocs = [b for b in re.split(r"\n\s*\n", "\n".join(lignes)) if b.strip()]
    if len(blocs) >= 3 and sum(len(b.split("\n")) for b in blocs) / len(blocs) <= 4:
        refs = [" ".join(b.split("\n")) for b in blocs]
    else:
        refs = []
        for l in (x for x in lignes if x.strip()):
            l = re.sub(r"^\s*(\d+[.)]|[-•*])\s+", "", l)
            if refs and DEBUT_REF.match(l) and re.search(r"[.)]\s*$|\S+/\S*$", refs[-1]):
                refs.append(l)
            elif not refs:
                refs.append(l)
            elif refs[-1].endswith(("/", "doi.", "https://", "-")):
                refs[-1] += l
            else:
                refs[-1] += " " + l
    return _nettoyer(refs)


def _auteurs_apa(noms: list) -> str:
    def un(n):
        if "," in n:
            fam, giv = [x.strip() for x in n.split(",", 1)]
        else:
            morceaux = n.split()
            fam, giv = morceaux[-1], " ".join(morceaux[:-1])
        ini = " ".join(f"{x}." for x in _initiales(giv))
        return f"{fam}, {ini}".strip().rstrip(",")
    noms = [un(n) for n in noms if n.strip()]
    if len(noms) <= 1:
        return "".join(noms)
    return ", ".join(noms[:-1]) + ", & " + noms[-1]


def _ref_depuis_champs(c: dict) -> str:
    """Reconstitue une référence de type APA à partir des champs d'un export .bib ou .ris."""
    r = f"{_auteurs_apa(c.get('auteurs', []))} ({c.get('annee', 's.d.')}). {c.get('titre', '').rstrip('.')}."
    if c.get("revue"):
        r += f" {c['revue']}"
        if c.get("volume"):
            r += f", {c['volume']}"
            if c.get("numero"):
                r += f"({c['numero']})"
        if c.get("pages"):
            r += f", {c['pages']}"
        r += "."
    elif c.get("editeur"):
        r += f" {c['editeur']}."
    if c.get("doi"):
        r += f" https://doi.org/{c['doi']}"
    return r


LATEX = {"\\'": "\u0301", "\\`": "\u0300", "\\^": "\u0302", '\\"': "\u0308", "\\~": "\u0303", "\\c": "\u0327"}


def _delatex(s: str) -> str:
    """Accents et symboles LaTeX courants des exports BibTeX : {\\'e} → é, \\& → &."""
    s = s or ""
    for cmd, diacritique in LATEX.items():
        s = re.sub(r"\{?" + re.escape(cmd) + r"\{?\s*([A-Za-z])\}?\}?",
                   lambda m: unicodedata.normalize("NFC", m.group(1) + diacritique), s)
    s = s.replace("\\&", "&").replace("---", "—").replace("--", "–")
    return re.sub(r"\s+", " ", re.sub(r"[{}]", "", s)).strip()


def _champs_bib(texte: str) -> list:
    """Entrées BibTeX → dictionnaires de champs (type, auteurs, titre, revue, volume…)."""
    entrees = []
    for entree in re.split(r"(?=@\w+\s*\{)", texte):
        m = re.match(r"\s*@(\w+)\s*\{", entree)
        if not m or m.group(1).lower() in ("comment", "string", "preamble"):
            continue
        champs = dict((k.lower(), v) for k, v in
                      re.findall(r"(\w+)\s*=\s*(\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|\"[^\"]*\"|\d+)", entree))
        champs = {k: _delatex(v.strip('"')) for k, v in champs.items()}
        entrees.append({
            "type": m.group(1).lower(),
            "auteurs": [a.strip() for a in re.split(r"\s+and\s+", champs.get("author", "")) if a.strip()],
            "annee": champs.get("year", "") or champs.get("date", "")[:4],
            "titre": champs.get("title", ""),
            "revue": champs.get("journal") or champs.get("journaltitle") or champs.get("booktitle", ""),
            "volume": champs.get("volume", ""), "numero": champs.get("number", "") or champs.get("issue", ""),
            "pages": champs.get("pages", "").replace("–", "-"),
            "editeur": champs.get("publisher", ""), "doi": champs.get("doi", "")})
    return entrees


def _champs_ris(texte: str) -> list:
    """Entrées RIS (Zotero, Mendeley, EndNote) → dictionnaires de champs."""
    entrees, c = [], None
    for l in texte.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", l)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            c = {"type": val.lower(), "auteurs": []}
        elif c is None:
            continue
        elif tag in ("AU", "A1"):
            c["auteurs"].append(val)
        elif tag in ("PY", "Y1", "DA") and "annee" not in c:
            c["annee"] = val[:4]
        elif tag in ("TI", "T1"):
            c["titre"] = val
        elif tag in ("JO", "JF", "T2", "JA") and "revue" not in c:
            c["revue"] = val
        elif tag == "VL":
            c["volume"] = val
        elif tag == "IS":
            c["numero"] = val
        elif tag == "SP":
            c["pages"] = val
        elif tag == "EP":
            c["pages"] = f"{c.get('pages', '')}-{val}"
        elif tag == "PB":
            c["editeur"] = val
        elif tag == "DO":
            c["doi"] = val
        elif tag == "ER":
            entrees.append(c)
            c = None
    return entrees


def _lire_bib(texte: str) -> list:
    return [_ref_depuis_champs(c) for c in _champs_bib(texte)]


def _lire_ris(texte: str) -> list:
    return [_ref_depuis_champs(c) for c in _champs_ris(texte)]


def _initialiser(tool_context, refs: list, origine: str) -> dict:
    if tool_context is not None:
        etat = tool_context.state.to_dict()
        for k in etat:
            if k.startswith("res_"):
                tool_context.state[k] = None
        tool_context.state["refs"] = refs
        tool_context.state["curseur"] = 0
        tool_context.state["origine"] = origine
    return {"statut": "ok", "nombre": len(refs), "lots": -(-len(refs) // TAILLE_LOT),
            "apercu": refs[:3], "origine": origine}


def charger_fichier(chemin: str, tool_context: ToolContext = None) -> dict:
    """Charge la bibliographie d'un fichier local (.docx, .txt, .md, .bib, .ris).

    Pour un manuscrit Word, seule la section qui suit le titre « Références » ou
    « Bibliographie » est retenue.

    Args:
        chemin: chemin complet du fichier, par exemple C:\\Users\\papa\\Documents\\manuscrit.docx
    """
    chemin = os.path.expanduser(chemin.strip().strip('"').strip("'"))
    if not os.path.isfile(chemin):
        return {"statut": "erreur", "detail": f"fichier introuvable : {chemin}"}
    ext = os.path.splitext(chemin)[1].lower()
    try:
        if ext == ".docx":
            refs = _nettoyer(_section_biblio([p for p in _paragraphes_docx(chemin)
                                              if p.strip() and not _en_tete_de_page(p)]))
        else:
            with open(chemin, encoding="utf-8-sig", errors="replace") as f:
                texte = f.read()
            refs = (_lire_bib(texte) if ext == ".bib" else
                    _lire_ris(texte) if ext == ".ris" else _decouper_texte(texte))
    except Exception as e:
        return {"statut": "erreur", "detail": _message(e)}
    if not refs:
        return {"statut": "erreur", "detail": "aucune référence reconnue dans ce fichier"}
    return _initialiser(tool_context, refs, chemin)


def charger_texte(texte: str, tool_context: ToolContext = None) -> dict:
    """Charge une bibliographie collée directement dans la conversation.

    Args:
        texte: la liste de références, copiée exactement telle que l'utilisateur l'a fournie.
    """
    refs = _decouper_texte(texte)
    if not refs:
        return {"statut": "erreur", "detail": "aucune référence reconnue dans ce texte"}
    return _initialiser(tool_context, refs, "")


def lot_suivant(tool_context: ToolContext = None) -> dict:
    """Renvoie le prochain lot de références à vérifier. Quand tout est traité, met fin à la boucle."""
    etat = tool_context.state if tool_context is not None else {}
    refs, i = etat.get("refs") or [], etat.get("curseur") or 0
    if i >= len(refs):
        if tool_context is not None:
            tool_context.actions.escalate = True        # condition d'arrêt explicite de la boucle
        return {"termine": True, "message": "Toutes les références ont été traitées."
                if refs else "Aucune bibliographie chargée."}
    lot = refs[i: i + TAILLE_LOT]
    if tool_context is not None:
        tool_context.state["curseur"] = i + len(lot)
    return {"termine": False, "lot": [{"numero": i + k + 1, "reference": r} for k, r in enumerate(lot)],
            "progression": f"{i + len(lot)}/{len(refs)}"}


def rapport_final(tool_context: ToolContext = None) -> dict:
    """Construit le tableau final et le décompte, et les enregistre en .md et .csv."""
    import csv
    etat = tool_context.state.to_dict() if tool_context is not None else {}
    res = sorted((v for k, v in etat.items() if k.startswith("res_") and v),
                 key=lambda r: int(r["numero"]))
    if not res:
        return {"tableau": "", "message": "Aucun résultat : aucune bibliographie n'a été vérifiée."}
    tableau = synthese(tool_context)["tableau"]
    origine = etat.get("origine") or os.path.join(os.getcwd(), "bibliographie")
    base = os.path.splitext(origine)[0] + "_verification"
    fichiers = []
    try:
        with open(base + ".md", "w", encoding="utf-8") as f:
            f.write(f"# Vérification bibliographique\n\nSource : {origine}\n\n{tableau}\n")
        with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["n°", "référence", "verdict", "écarts et notes", "sources"])
            for r in res:
                w.writerow([r["numero"], r["reference"], r["verdict"], r["ecarts"], r["sources"]])
        fichiers = [base + ".md", base + ".csv"]
    except Exception as e:
        fichiers = [f"échec de l'enregistrement : {_message(e)}"]
    return {"tableau": tableau, "fichiers": fichiers}
