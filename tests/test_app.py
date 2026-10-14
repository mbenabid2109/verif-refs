"""Interface web (space/app.py) : parcours complet sans réseau. Ignoré si Gradio est absent."""
import os, re, sys, tempfile
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE); sys.path.insert(0, os.path.join(RACINE, "space"))

import verif_refs.core as C
C._crossref = lambda brute, doi: ([{"titre": "Exposure to ideologically diverse news and opinion on Facebook",
                                    "sous_titre": "", "auteurs": [("Bakshy", "Eytan"), ("Messing", "Solomon"), ("Adamic", "Lada A.")],
                                    "annees": {2015}, "revue": "Science", "volume": "348", "numero": "6239",
                                    "pages": "1130-1132", "doi": "10.1126/science.aaa1160"}]
                                  if "ideologically" in brute.lower() else [])
C._datacite = lambda doi: {}
C._openalex = lambda doi: {}
C._openlibrary = lambda t, a: []
import app

def dernier(g):
    out = None
    for out in g:
        pass
    return out

def texte(h):
    return re.sub(r"<[^>]+>", "", h)

def ok(cond, libelle):
    print(("OK  " if cond else "XX  ") + "app : " + libelle)

EX = os.path.join(RACINE, "examples", "exemple.bib")
h, f, etat = dernier(app.verifier(EX, "", "English"))
ok(h.count('class="n"') == 6 and f and len(f) == 2, "exemple .bib : 6 lignes et 2 fichiers de rapport")
ok(os.path.basename(f[1]) == "exemple_check.csv", "rapport anglais : garde le nom du fichier déposé")
ok("CONFIRMED" in h and "NOT VERIFIABLE" in h and "ERREUR" not in h and "Discrepancies" in h, "interface en anglais")
sortie = app.changer_langue("Français", etat)
ok("Vérifiez" in sortie[0] and "CONFIRMÉE" in sortie[5] and "Écarts" in sortie[5], "bascule en français : interface et tableau")
ok(any(x.endswith("exemple_verification.csv") for x in sortie[6]["value"]), "bascule en français : rapport régénéré")
h, f, _ = dernier(app.verifier(EX, "", "Français"))
ok("CONFIRMÉE" in h and "NON VÉRIFIABLE" in h and "Écarts" in h and "CONFIRMED" not in h
   and os.path.basename(f[1]) == "exemple_verification.csv",
   "vérification lancée en français")
h, f, _ = dernier(app.verifier(None, "Bakshy, E., Messing, S., & Adamic, L. A. (2015). Exposure to ideologically diverse "
                                     "news and opinion on Facebook. Science, 348(6239), 1130-1132.\n\nWanta, W., & Ghanem, S. "
                                     "(2007). Effects of agenda setting. In R. W. Preiss et al. (Eds.), Mass media effects "
                                     "research (pp. 37-51). Erlbaum.", "English"))
ok("Text mode" in h and h.count('class="n"') == 2 and "CONFIRMED" in h, "bibliographie collée (mode texte)")
ok("Drop a file" in texte(dernier(app.verifier(None, " ", "English"))[0]), "rien de fourni : message clair")
ok("Déposez" in texte(dernier(app.verifier(None, " ", "Français"))[0]), "rien de fourni : message en français")
d = tempfile.mkdtemp(); pdf = os.path.join(d, "a.pdf"); open(pdf, "w").write("x")
ok("Unsupported" in texte(dernier(app.verifier(pdf, "", "English"))[0]), "format refusé : message clair")
app.MAX_REFS = 2
ok("at most" in texte(dernier(app.verifier(EX, "", "English"))[0]), "plafond de références respecté")
ok("&lt;script" in app._tableau([{"numero": 1, "reference": "<script>", "verdict": "ERREUR", "ecarts": "x",
                                  "sources": "y"}], "en"), "texte des références échappé (pas d'injection HTML)")
class _Req:
    def __init__(self, h): self.headers = h
ok(app.langue_du_navigateur(_Req({"accept-language": "fr-FR,fr;q=0.9"})) == "Français"
   and app.langue_du_navigateur(_Req({"accept-language": "en-US"})) == "English", "langue du navigateur détectée")
