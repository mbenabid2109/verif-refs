import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
DATA = os.path.join(ICI, "data")
import verif_refs.core as A
from test_v4 import cr, CR, OA, Ctx   # réutilise les notices simulées (et relance le 1er test)
print("\n--- cas réels du lot 1 ---")
# notice brute Crossref avec entités HTML
item = {"title":["Behind the newspaper paywall – lessons"],"container-title":["Media, Culture &amp; Society"],
        "author":[{"family":"Carson","given":"Andrea"}],"issued":{"date-parts":[[2015]]}}
print("unescape revue :", A._crossref_notice(item)["revue"])
CR["paywall"]["revue"] = "Media, Culture &amp; Society"
CR["paywall"] = A._crossref_notice({**item, "title":[CR["paywall"]["titre"]], "volume":"37","issue":"7","page":"1022-1041","DOI":"10.1177/x"})
CR["tuaut"]["annees"] = {2026}
CR["tuaut"]["revue"] = "Systèmes d'Information et Management (French Journal of Management Information Systems)"
CR["tuaut"]["doi"] = "10.3917/sim.091.0009"; OA["10.3917/sim.091.0009"] = {"annee":"2009"}
CR["decline"] = cr("Between Decline and a New Online Business Model: The Case of the Spanish Newspaper Industry",[("Casero-Ripollés","Andreu"),("Izquierdo-Castillo","Jessica")],[2013],"Journal of Media Business Studies","10","1","63-78")
ctx = Ctx()
cas = [
 (4, dict(reference_brute="Bourdon I. et Hollet-haudebert S. (2009), Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle TUAUT, Systèmes d’information & management, vol. 14, n° 1, p. 9-36.", titre="Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle TUAUT", annee="2009", revue="Systèmes d’information & management", volume="14", numero_fascicule="1", pages="9-36"), "ERREUR"),
 (6, dict(reference_brute="Carson A. (2015), Behind the newspaper paywall-lessons in charging for online content : a comparative analysis of why Australian newspapers are stuck in the purgatorial space between digital and print, Media, Culture & Society, vol. 37, n° 7, p. 1022-1041.", titre="Behind the newspaper paywall-lessons in charging for online content : a comparative analysis of why Australian newspapers are stuck in the purgatorial space between digital and print", annee="2015", revue="Media, Culture & Society", volume="37", numero_fascicule="7", pages="1022-1041"), "CONFIRMÉE"),
 # le modèle a mal recopié les pages (63-71 au lieu de 63-78)
 (7, dict(reference_brute="Casero-Ripollés A. & Izquierdo-Castillo J. (2013), Between decline and a new online business model : The case of the Spanish newspaper industry, Journal of Media Business Studies, vol. 10, n° 1, p. 63-78.", titre="Between decline and a new online business model : The case of the Spanish newspaper industry", annee="2013", revue="Journal of Media Business Studies", volume="10", numero_fascicule="1", pages="63-71"), "CONFIRMÉE"),
 (11, dict(reference_brute="Churchill G.A (1979), A paradigm for developing better measures of marketing constructs, Journal of marketing, vol 16, p. 64-73.", titre="A paradigm for developing better measures of marketing constructs", annee="1979", revue="Journal of marketing"), "ERREUR"),
]
for num, kw, att in cas:
    r = A.verifier_article(num, tool_context=ctx, **kw)
    print(("OK  " if r["verdict"]==att else "XX  ") + f"{num:>2} {r['verdict']:<14} | {r['ecarts']}")
print("extraction :", A._extraire("Horng S. M. (2012), A study, Total Quality Management & Business Excellence, vol. 23, n° 7-8, p. 891-912."),
      A._extraire("Dou W. (December 2004), Will..., vol. 44, n° 4, p. 349-359."),
      A._extraire("Smith, J. (2020). Title. Journal, 67(5), 422–436."))
