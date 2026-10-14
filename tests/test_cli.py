"""Ligne de commande : fichier .bib d'exemple, sans réseau et sans Google ADK."""
import os, sys, io, contextlib, shutil, tempfile
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
sys.modules["google.adk"] = None          # simule l'absence d'ADK : la ligne de commande doit suffire
sys.modules["google.adk.tools"] = None
sys.modules["google.adk.tools.tool_context"] = None

import verif_refs.core as C
from verif_refs import cli

def cr(titre, auteurs, annee, revue, vol, num, pages, doi="10.x/y"):
    return {"titre": titre, "sous_titre": "", "auteurs": auteurs, "annees": {annee}, "revue": revue,
            "volume": vol, "numero": num, "pages": pages, "doi": doi}
NOTICES = {
    "ideologically diverse": cr("Exposure to ideologically diverse news and opinion on Facebook", [("Bakshy","Eytan"),("Messing","Solomon"),("Adamic","Lada A.")], 2015, "Science", "348", "6239", "1130-1132", "10.1126/science.aaa1160"),
    "better measures": cr("A Paradigm for Developing Better Measures of Marketing Constructs", [("Churchill","Gilbert A.")], 1979, "Journal of Marketing Research", "16", "1", "64-73"),
    "extrinsic": cr("Extrinsic and Intrinsic Motivation to Use Computers in the Workplace", [("Davis","Fred D."),("Bagozzi","Richard P."),("Warshaw","Paul R.")], 1992, "Journal of Applied Social Psychology", "22", "14", "1111-1132"),
    "willingness to pay": cr("An Empirical Study of Factors that Influence the Willingness to Pay for Online News", [("Goyanes","Manuel")], 2014, "Journalism Practice", "8", "6", "742-757"),
}
C._crossref = lambda brute, doi: [v for k, v in NOTICES.items() if k in brute.lower()]
C._datacite = lambda doi: {}
C._openalex = lambda doi: {}
C._openlibrary = lambda t, a: [{"titre": "Work and motivation", "sous_titre": "", "auteurs": [("Vroom","Victor Harold")], "annees": {1964}, "editeurs": ["Wiley"]}] if "motivation" in t.lower() else []

tmp = tempfile.mkdtemp()
bib = os.path.join(tmp, "exemple.bib")
shutil.copy(os.path.join(RACINE, "examples", "exemple.bib"), bib)
sortie = io.StringIO()
with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(io.StringIO()):
    cli.main([bib, "--contact", "test@example.org", "--pause", "0", "--lang", "fr"])
lignes = [l for l in sortie.getvalue().splitlines() if l.startswith("| ") and not l.startswith("| n°")]
verdicts = [l.split(" | ")[2] for l in lignes]
attendu = ["CONFIRMÉE", "ERREUR", "ERREUR", "ERREUR", "ERREUR", "NON VÉRIFIABLE"]
print(("OK  " if verdicts == attendu else "XX  ") + f"CLI .bib : {verdicts} (attendu {attendu})")
print(("OK  " if os.path.exists(os.path.join(tmp, "exemple_verification.csv")) else "XX  ") + "rapport .csv enregistré à côté du fichier")
print(("OK  " if "google.adk" not in [m for m in sys.modules if sys.modules[m] is not None] else "XX  ") + "aucune dépendance à Google ADK")

# Mode texte : types devinés par des règles
txt = os.path.join(tmp, "biblio.txt")
with open(txt, "w", encoding="utf-8") as f:
    f.write("""Bakshy, E., Messing, S., & Adamic, L. A. (2015). Exposure to ideologically diverse news and opinion on Facebook. Science, 348(6239), 1130–1132. https://doi.org/10.1126/science.aaa1160

Vroom, V. C. (1964). Work and motivation. Wiley.

Wanta, W., & Ghanem, S. (2007). Effects of agenda setting. In R. W. Preiss et al. (Eds.), Mass media effects research (pp. 37-51). Erlbaum.
""")
sortie = io.StringIO()
with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(io.StringIO()):
    cli.main([txt, "--contact", "test@example.org", "--pause", "0", "--lang", "fr"])
lignes = [l for l in sortie.getvalue().splitlines() if l.startswith("| ") and not l.startswith("| n°")]
verdicts = [l.split(" | ")[2] for l in lignes]
attendu = ["CONFIRMÉE", "ERREUR", "NON VÉRIFIABLE"]
print(("OK  " if verdicts == attendu else "XX  ") + f"CLI texte : {verdicts} (attendu {attendu})")

# Rapport en anglais (langue par défaut)
sortie = io.StringIO()
with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(io.StringIO()):
    cli.main([bib, "--contact", "test@example.org", "--pause", "0"])
lignes = [l for l in sortie.getvalue().splitlines() if l.startswith("| ") and not l.startswith("| no.")]
verdicts = [l.split(" | ")[2] for l in lignes]
attendu = ["CONFIRMED", "ERROR", "ERROR", "ERROR", "ERROR", "NOT VERIFIABLE"]
print(("OK  " if verdicts == attendu else "XX  ") + f"CLI anglais : {verdicts}")
en = sortie.getvalue()
print(("OK  " if "journal: reference “Journal of Marketing” → source “Journal of Marketing Research”" in en
       and "initials of Vroom" in en and "book chapter: manual check" in en else "XX  ")
      + "CLI anglais : écarts et notes traduits")
print(("OK  " if os.path.exists(os.path.join(tmp, "exemple_check.csv")) else "XX  ") + "rapport anglais .csv enregistré")
