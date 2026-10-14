"""Tests de la v5.2 : fausses alertes observées sur deux bibliographies réelles (oct. 2026).

Les notices sont simulées d'après ce que Crossref et Open Library ont réellement renvoyé.
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)

import verif_refs.core as A
from test_v4 import cr, CR, OA, OL, Ctx

print("\n--- v5.2 : fausses alertes des revues francophones et des notices d'ouvrages ---")
ctx = Ctx()
CR.clear(); OA.clear(); OL.clear()
A._datacite = lambda doi: {}


import itertools
_num = itertools.count(1)


def art(n, brute, titre, annee, att, absent=None, **kw):
    r = A.verifier_article(next(_num), brute, titre, annee, tool_context=ctx, **kw)
    ok = r["verdict"] == att and (absent is None or absent not in r["ecarts"])
    print(("OK  " if ok else "XX  ") + f"{n:<14} {r['verdict']:<14} attendu {att:<14} | {r['ecarts'][:170]}")


def ouv(n, brute, titre, annee, auteur, att, editeur=""):
    r = A.verifier_ouvrage(next(_num), brute, titre, annee, auteur, editeur, tool_context=ctx)
    print(("OK  " if r["verdict"] == att else "XX  ") + f"{n:<14} {r['verdict']:<14} attendu {att:<14} | {r['ecarts'][:170]}")


# Numéro double (Persée) : la source n'enregistre qu'une partie de « 106–107 »
CR["cause de la science"] = cr("La cause de la science", [("Bourdieu", "Pierre")], [1995],
                               "Actes de la recherche en sciences sociales", "106", "1", "3-10",
                               sub="Comment l'histoire sociale des sciences sociales peut servir le progrès de ces sciences",
                               doi="10.3406/arss.1995.3131")
art("Bourdieu", "Bourdieu, P. (1995). La cause de la science : Comment l’histoire sociale des sciences sociales peut servir le progrès de ces sciences. Actes de la recherche en sciences sociales, 106–107, 3–10. https://doi.org/10.3406/arss.1995.3131",
    "La cause de la science : Comment l’histoire sociale des sciences sociales peut servir le progrès de ces sciences",
    "1995", "CONFIRMÉE", revue="Actes de la recherche en sciences sociales", numero_fascicule="106–107", pages="3–10")

CR["robert park"] = cr("Robert Park, journaliste et sociologue", [("Bourmeau", "Sylvain")], [1988], "Politix",
                       "1", "3", "50-61", doi="10.3406/polix.1988.1351")
art("Bourmeau", "Bourmeau, S. (1988). Robert Park, journaliste et sociologue. Politix, 1(3–4), 50–61. https://doi.org/10.3406/polix.1988.1351",
    "Robert Park, journaliste et sociologue", "1988", "CONFIRMÉE", revue="Politix")

# Préfixe « Vol. » dans la notice Cairn
CR["zola"] = cr("Quand Zola mène l'enquête", [("Giraud", "Frédérique")], [2013], "Ethnologie française",
                "Vol. 43", "1", "147-153", sub="Le terrain comme caution scientifique", doi="10.3917/ethn.131.0147")
art("Giraud", "Giraud, F. (2013). Quand Zola mène l’enquête : Le terrain comme caution scientifique. Ethnologie française, 43(1), 147–153.",
    "Quand Zola mène l’enquête : Le terrain comme caution scientifique", "2013", "CONFIRMÉE", revue="Ethnologie française")

# Titre enregistré sans accents
CR["sous-champs"] = cr("Les sous-champs specialises du journalisme", [("Marchetti", "Dominique")], [2002], "Réseaux",
                       "111", "1", "22", doi="10.3917/res.111.0022")
art("Marchetti", "Marchetti, D. (2002). Les sous-champs spécialisés du journalisme. Réseaux, 111(1), 22–55. https://doi.org/10.3917/res.111.0022",
    "Les sous-champs spécialisés du journalisme", "2002", "CONFIRMÉE", revue="Réseaux")

# Supplément écrit autrement
CR["anti-academic"] = cr("Is Autobiography Anti-academic and Uneconomical?", [("Popkin", "Jeremy D.")], [2007],
                         "History of Political Economy", "39", "Suppl_1", "30-47",
                         sub="Some Thoughts on Academic Autobiography", doi="10.1215/00182702-2006-037")
art("Popkin", "Popkin, J. D. (2007). Is autobiography anti-academic and uneconomical? Some thoughts on academic autobiography. History of Political Economy, 39(Suppl. 1), 30–47. https://doi.org/10.1215/00182702-2006-037",
    "Is autobiography anti-academic and uneconomical? Some thoughts on academic autobiography", "2007", "CONFIRMÉE",
    revue="History of Political Economy", volume="39", numero_fascicule="Suppl. 1")

# Contre-épreuve : la vraie erreur de volume doit rester détectée
CR["chercheur-acteur"] = cr("Production de la connaissance et de l'action en sciences de gestion", [("Lallé", "Bernard")],
                            [2004], "Revue française de gestion", "30", "148", "45-65",
                            sub="Le statut expérimenté de « chercheur-acteur »", doi="10.3166/rfg.148.45-65")
art("Lallé", "Lallé, B. (2004). Production de la connaissance et de l’action en sciences de gestion : Le statut expérimenté de « chercheur-acteur ». Revue française de gestion, 158(1), 45–65. https://doi.org/10.3166/rfg.148.45-65",
    "Production de la connaissance et de l’action en sciences de gestion : Le statut expérimenté de « chercheur-acteur »",
    "2004", "ERREUR", revue="Revue française de gestion")

# Contre-épreuve : erreur de pagination (Weaver, 361-376 au lieu de 361-373)
CR["need for orientation"] = cr("Audience Need for Orientation and Media Effects", [("Weaver", "David H.")], [1980],
                                "Communication Research", "7", "3", "361-373", doi="10.1177/009365028000700305")
OA["10.1177/009365028000700305"] = {"volume": "7", "numero": "3", "pages": "361-373"}
art("Weaver", "Weaver, D. H. (1980). Audience need for orientation and media effects. Communication Research, 7(3), 361-376.",
    "Audience need for orientation and media effects", "1980", "ERREUR", revue="Communication Research")

# Nom de famille composé mal découpé par la source (« Gene Zucker ») : plus d'« auteur omis »
CR["variable nature"] = cr("The Variable Nature of News Media Influence", [("Gene Zucker", "Harold")], [1978],
                           "Annals of the International Communication Association", "2", "1", "225-240",
                           doi="10.1080/23808985.1978.11923728")
art("Zucker", "Zucker, H. G. (1978). The variable nature of news media influence. Communication Yearbook, 2, 225-240.",
    "The variable nature of news media influence", "1978", "ERREUR", absent="auteur omis",
    revue="Communication Yearbook", volume="2")

# Notices d'ouvrages (Open Library)
OL["la démocratie"] = {"titre": "De la démocratie en Amérique", "sous_titre": "",
                       "auteurs": [("Tocqueville", "Alexis de"), ("Beaumont", "Gustave de")],
                       "annees": {1835, 1840, 1981}, "editeurs": ["C. Gosselin"]}
ouv("Tocqueville", "Tocqueville, A. de (1835). De la démocratie en Amérique. Gosselin.",
    "De la démocratie en Amérique", "1835", "Tocqueville", "CONFIRMÉE", "Gosselin")
OL["personal influence"] = {"titre": "Personal influence", "sous_titre": "the part played by people in the flow of mass communications",
                            "auteurs": [("Katz", "Elihu"), ("Lazarsfeld", "Paul")], "annees": {1955, 1964}, "editeurs": ["Free Press"]}
ouv("Katz", "Katz, E., & Lazarsfeld, P. F. (1955). Personal influence. Free Press.",
    "Personal influence", "1955", "Katz", "CONFIRMÉE", "Free Press")
OL["nature and origins"] = {"titre": "The nature and origins of mass opinion", "sous_titre": "",
                            "auteurs": [("Zaller", "John")], "annees": {1992}, "editeurs": ["Cambridge University Press"]}
ouv("Zaller", "Zaller, J. R. (1992). The nature and origins of mass opinion. Cambridge University Press.",
    "The nature and origins of mass opinion", "1992", "Zaller", "CONFIRMÉE", "Cambridge University Press")
# Notice réduite au premier auteur : prudence maintenue (risque de fausse confirmation)
OL["pulse of democracy"] = {"titre": "The pulse of democracy", "sous_titre": "",
                            "auteurs": [("Gallup", "George")], "annees": {1940}, "editeurs": ["Simon and Schuster"]}
ouv("Gallup", "Gallup, G., & Rae, S. F. (1940). The pulse of democracy. Simon & Schuster.",
    "The pulse of democracy", "1940", "Gallup", "À VÉRIFIER", "Simon & Schuster")
# Contre-épreuve : initiales contradictoires (Vroom V.C. au lieu de V.H.) toujours en ERREUR
OL["work and motivation"] = {"titre": "Work and motivation", "sous_titre": "", "auteurs": [("Vroom", "Victor Harold")],
                             "annees": {1964}, "editeurs": ["Wiley"]}
ouv("Vroom", "Vroom V.C. (1964), Work and motivation, New York : John Wiley Sons.",
    "Work and motivation", "1964", "Vroom", "ERREUR", "John Wiley Sons")

# Normalisation des numéros
for a, b, egal in (("Vol. 43", "43", True), ("Suppl. 1", "Suppl_1", True), ("n° 194", "194", True),
                   ("158", "30", False), ("3–4", "3-4", True)):
    ok = (A._num_norm(a) == A._num_norm(b)) == egal
    print(("OK  " if ok else "XX  ") + f"_num_norm({a!r}) {'=' if egal else '≠'} _num_norm({b!r})")
