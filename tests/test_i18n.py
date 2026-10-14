"""Traductions : chaque message produit par les scénarios de test doit avoir sa version anglaise."""
import contextlib, io, os, runpy, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
sys.modules["google.adk"] = None; sys.modules["google.adk.tools"] = None
sys.modules["google.adk.tools.tool_context"] = None

import verif_refs.core as C
from verif_refs import i18n

vus = []
_orig = C._enregistrer
def _espion(*a, **k):
    r = _orig(*a, **k)
    vus.append(r)
    return r
C._enregistrer = _espion

for f in ("test_v4.py", "test_reels.py", "test_d.py", "test_v5.py", "test_v51.py", "test_v52.py"):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            runpy.run_path(os.path.join(ICI, f), run_name="__main__")
        except SystemExit:
            pass
        except Exception as e:
            print("XX  i18n : scénario", f, "interrompu :", type(e).__name__, e, file=sys.__stdout__)
        C._enregistrer = _espion          # certains scénarios rechargent des fonctions : on garde l'espion

champs, notes = set(), set()
for r in vus:
    for c, _, _ in r.get("details", []):
        champs.add(c)
    for n in r.get("notes", []):
        notes.add(" ".join(str(n).split()))
champs_ko = sorted(c for c in champs if i18n._champ_en(c) == c and c not in ("DOI", "volume", "pages"))
notes_ko = sorted(n for n in notes if i18n.note_en(n) == n and not n.startswith("DOI 10."))
print(("OK  " if len(vus) >= 90 else "XX  ") + f"i18n : {len(vus)} résultats observés dans les scénarios")
print(("OK  " if not champs_ko else "XX  ") + f"i18n : {len(champs)} libellés de champ traduits" + (f" — manquants : {champs_ko}" if champs_ko else ""))
print(("OK  " if not notes_ko else "XX  ") + f"i18n : {len(notes)} notes traduites" + (f" — manquantes : {notes_ko[:5]}" if notes_ko else ""))
for v in i18n.VERDICTS:
    print(("OK  " if i18n.verdict(v, "en") != v and i18n.verdict(v, "fr") == v else "XX  ") + f"i18n : verdict {v}")
