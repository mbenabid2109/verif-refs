import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
DATA = os.path.join(ICI, "data")
import verif_refs.core as A
from test_v4 import cr, CR, OA, OL, Ctx
import urllib.error
print("\n--- défauts D1-D5 (observations réelles des lots 1-5) ---")
ctx = Ctx()
def run(num, kw, att):
    r = A.verifier_article(num, tool_context=ctx, **kw)
    print(("OK  " if r["verdict"]==att else "XX  ") + f"{num:>2} {r['verdict']:<14} | {r['ecarts']}")
# D1 Bourdon : Crossref ET OpenAlex donnent 2026
CR["tuaut"]["annees"]={2026}; CR["tuaut"]["doi"]="10.3917/sim.091.0009"; OA["10.3917/sim.091.0009"]={"annee":"2026"}
run(4, dict(reference_brute="Bourdon I. et Hollet-haudebert S. (2009), Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle TUAUT, Systèmes d’information & management, vol. 14, n° 1, p. 9-36.", titre="Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle TUAUT", annee="2009", revue="Systèmes d’information & management"), "ERREUR")
# D1 Dejean : 2011 partout, « n° 194 » rangé en volume
CR["gratuité"]["annees"]={2011}; CR["gratuité"]["volume"]="n° 194"; CR["gratuité"]["doi"]="10.3917/ecop.194.0015"; OA["10.3917/ecop.194.0015"]={"annee":"2011"}
run(21, dict(reference_brute="Dejean S., Pénard T. & Suire R. (2010), La gratuité est-elle une fatalité sur les marchés numériques ? Une étude sur le consentement à payer pour des offres de contenus audiovisuels sur internet, Economie & prévision, n° 3, p. 15-32.", titre="La gratuité est-elle une fatalité sur les marchés numériques ? Une étude sur le consentement à payer pour des offres de contenus audiovisuels sur internet", annee="2010", revue="Economie & prévision"), "À COMPLÉTER")
# D3 Jelassi : Crossref « n° 45 » en volume, le modèle recopie « n° 5 » comme volume
CR["continuité"]["volume"]="n° 45"; CR["continuité"]["numero"]=""
run(35, dict(reference_brute="Jelassi K. & Ammi C. (2011), Les services Internet Mobile en France : une proposition de mesure de la continuité d’usage, Management & Avenir, n° 5, p. 238-256.", titre="Les services Internet Mobile en France : une proposition de mesure de la continuité d’usage", annee="2011", revue="Management & Avenir", volume="n° 5"), "À COMPLÉTER")
# D2 Davis 1992 : appel de note <sup>
item={"title":["Extrinsic and Intrinsic Motivation to Use Computers in the Workplace\n                <sup>1</sup>"],"author":[{"family":"Davis","given":"Fred D."},{"family":"Bagozzi","given":"Richard P."},{"family":"Warshaw","given":"Paul R."}],"issued":{"date-parts":[[1992]]},"container-title":["Journal of Applied Social Psychology"],"volume":"22","issue":"14","page":"1111-1132","DOI":"10.1111/j.1559-1816.1992.tb00945.x"}
CR["extrinsic"]=A._crossref_notice(item)
run(20, dict(reference_brute="Davis F.D., Bagozzi R.P. & Warshaw P.R. (1992), Extrinsic and intrinsic motivation to use computers in the workplace, Journal of Applied Social Psychology, vol. 22, n° 14, p. 111-1132.", titre="Extrinsic and intrinsic motivation to use computers in the workplace", annee="1992", revue="Journal of Applied Social Psychology"), "ERREUR")
# D4 Jones : DOI en minuscules, OpenAlex = Crossref (63-70)
CR["just say no"]["doi"]="10.2501/jar-41-5-63-71"; OA["10.2501/jar-41-5-63-71"]={"pages":"63-70","volume":"41","numero":"5"}
run(38, dict(reference_brute="Jones W. L. & Sonner B. S. (2001), Just say no to traditional student samples, Journal of Advertising Research, vol. 41, n° 5, p. 63-71.", titre="Just say no to traditional student samples", annee="2001", revue="Journal of Advertising Research"), "CONFIRMÉE")
# D5 : message d'un délai dépassé
print("D5 message :", A._message(TimeoutError()), "|", A._message(urllib.error.URLError("timed out")))
# Règle DOI : lecture dans le texte brut (43 références de validation)
for l in open(os.path.join(DATA, "corpus2_43refs.txt"),encoding="utf-8"):
    d=A._doi_brut(l)
    if d: print("   DOI", d)
