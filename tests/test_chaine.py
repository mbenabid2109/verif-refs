import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
DATA = os.path.join(ICI, "data")
"""Test de bout en bout de la chaîne d'agents, avec un modèle simulé (pas d'appel à Gemini ni au réseau)."""
import asyncio, os, json, shutil, tempfile
TMP = tempfile.mkdtemp()
shutil.copy(os.path.join(DATA, "corpus2_texte_brut_pdf.txt"), os.path.join(TMP, "biblio.txt"))
with open(os.path.join(TMP, "biblio.txt"), encoding="utf-8") as _f: _t = _f.read()
with open(os.path.join(TMP, "biblio.txt"), "w", encoding="utf-8") as _f: _f.write("References\n" + _t.replace("Schroeder, J. (2019). Racists are recruiting. Watch your whi", ""))
BIBLIO = os.path.join(TMP, "biblio.txt")
import verif_refs.agent as A  # chaîne ADK
import verif_refs.core as C
C._crossref = lambda brute, doi: []        # aucun accès réseau pendant le test
C._datacite = lambda doi: {}
C._openalex = lambda doi: {}
C._openlibrary = lambda t, a: []
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

def appel(nom, **args):
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=nom, args=args))]))
def plusieurs(calls):
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=n, args=a)) for n, a in calls]))
def texte(t):
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=t)]))

class ModeleSimule(BaseLlm):
    model: str = "simule"
    async def generate_content_async(self, req, stream=False):
        agent = req.config.system_instruction or ""
        derniere = req.contents[-1].parts if req.contents else []
        reponses = [p.function_response for p in derniere if p.function_response]
        if "Tu charges la bibliographie" in str(agent):
            if reponses:
                yield texte(f"{reponses[0].response.get('nombre')} références chargées.")
            else:
                yield appel("charger_fichier", chemin=BIBLIO)
        elif "Tu vérifies UN lot" in str(agent):
            if not reponses:
                yield appel("lot_suivant")
            elif reponses[0].name == "lot_suivant":
                r = reponses[0].response
                if r.get("termine"):
                    yield texte("Vérification terminée.")
                else:
                    yield plusieurs([("enregistrer_non_verifiable", {"numero": x["numero"], "reference_brute": x["reference"], "type_document": "test"}) for x in r["lot"]])
            else:
                yield texte("Lot traité.")
        else:
            if reponses:
                yield texte(reponses[0].response.get("tableau", "")[-120:])
            else:
                yield appel("rapport_final")

m = ModeleSimule()
for ag in (A.chargeur, A.verificateur, A.rapporteur):
    ag.model = m

async def main():
    runner = InMemoryRunner(agent=A.root_agent, app_name="test")
    s = await runner.session_service.create_session(app_name="test", user_id="u")
    msg = types.Content(role="user", parts=[types.Part(text="Vérifie " + BIBLIO)])
    appels_lot, iterations = 0, 0
    async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call and p.function_call.name == "lot_suivant": appels_lot += 1
            if p.text: print(f"[{ev.author}] {p.text.strip()[:130]}")
        if ev.actions and ev.actions.escalate: print(f"[{ev.author}] >>> escalate (fin de boucle)")
    print("appels à lot_suivant :", appels_lot, "(attendu : 4 lots + 1 appel final = 5)")
    for f in (os.path.join(TMP, "biblio_verification.md"), os.path.join(TMP, "biblio_verification.csv")):
        print(f, os.path.exists(f), os.path.getsize(f) if os.path.exists(f) else "")
asyncio.run(main())
