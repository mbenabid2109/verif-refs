import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
DATA = os.path.join(ICI, "data")
import verif_refs.core as A
from test_v4 import cr, CR, OA, OL, Ctx
DC = {}
A._datacite = lambda doi: DC.get(doi.lower(), {})
ctx = Ctx()
def voir(r, att, n):
    print(("OK  " if r["verdict"]==att else "XX  ") + f"{n:<22} {r['verdict']:<14} attendu {att:<14} | {r['ecarts'][:200]}")
print("\n--- v5.1 : cas réels (corpus 3, références publiées) ---")
# V5-2 : découpage d'un échantillon de références publiées, dont des particules en tête (« van … »)
ECHANTILLON = """Abdul-Mageed, M., Elmadany, A., & Nagoudi, E. M. B. (2021). ARBERT & MARBERT: Deep bidirectional transformers for Arabic. Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers), 7088–7105. https://doi.org/10.18653/v1/2021.acl-long.551
Gilardi, F., Alizadeh, M., & Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. Proceedings of the National Academy of Sciences, 120(30), e2305016120.
Pangakis, N., & Wolken, S. (2025). Keeping humans in the loop: Human-centered automated annotation with generative AI. Proceedings of the International AAAI Conference on Web and Social Media, 19(1), 1471–1492. https://doi.org/10.1609/icwsm.v19i1.35883
Reiss, M. V. (2023). Testing the reliability of ChatGPT for text annotation and classification: A cautionary remark (arXiv:2304.11085). arXiv. https://doi.org/10.48550/arXiv.2304.11085
Törnberg, P. (2025). Large language models outperform expert coders and supervised classifiers at annotating political social media messages. Social Science Computer Review, 43(6), 1181–1195. https://doi.org/10.1177/08944393241286471
van Atteveldt, W., van der Velden, M. A. C. G., & Boukes, M. (2021). The validity of sentiment analysis: Comparing manual annotation, crowd-coding, dictionary approaches, and machine learning algorithms. Communication Methods and Measures, 15(2), 121–140. https://doi.org/10.1080/19312458.2020.1869198
van der Velden, M. A. C. G., Loecherbach, F., van Atteveldt, W., Fokkens, A., Reuver, M., & Welbers, K. (2025). Whose truth is it anyway? An experiment on annotation bias in times of factual opinion polarization. Communication Methods and Measures, 19(4), 332–349. https://doi.org/10.1080/19312458.2025.2562034
Winata, G. I., Aji, A. F., Yong, Z. X., & Solorio, T. (2023). The decades progress on code-switching research in NLP: A systematic survey on trends and challenges. Findings of the Association for Computational Linguistics: ACL 2023, 2936–2978. https://doi.org/10.18653/v1/2023.findings-acl.185
Ziems, C., Held, W., Shaikh, O., Chen, J., Zhang, Z., & Yang, D. (2024). Can large language models transform computational social science? Computational Linguistics, 50(1), 237–291."""
r = A.charger_texte(ECHANTILLON, tool_context=ctx)
print(("OK  " if r["nombre"] == 9 else "XX  ") + f"découpage : {r['nombre']} références (attendu 9, dont 2 commençant par « van »)")
refs = ctx.state["refs"]; R = lambda debut: next(x for x in refs if x.startswith(debut))
CR.clear(); OA.clear(); OL.clear()
# V5-3 : Ziems sans DOI dans le texte ; le modèle ne peut plus en fournir
CR["transform computational"] = cr("Can Large Language Models Transform Computational Social Science?", [("Ziems","Caleb"),("Held","William"),("Shaikh","Omar"),("Chen","Jiaao"),("Zhang","Zhehao"),("Yang","Diyi")],[2024],"Computational Linguistics","50","1","237-291",doi="10.1162/coli_a_00502")
voir(A.verifier_article(40, R("Ziems"), "Can large language models transform computational social science?", "2024", "Computational Linguistics", tool_context=ctx), "CONFIRMÉE", "Ziems (sans DOI)")
try:
    A.verifier_article(40, R("Ziems"), "x", "2024", doi="10.1162/coli_a_00507", tool_context=ctx); print("XX  paramètre doi encore accepté")
except TypeError: print("OK  le paramètre « doi » n'existe plus : le modèle ne peut plus fournir de DOI")
# V5-4 : aiguillage imposé — le modèle classe ARBERT en « communication », le code vérifie quand même
CR["arbert"] = cr("ARBERT & MARBERT: Deep Bidirectional Transformers for Arabic", [("Abdul-Mageed","Muhammad"),("Elmadany","AbdelRahim"),("Nagoudi","El Moatez Billah")],[2021],"Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)","","","7088-7105",doi="10.18653/v1/2021.acl-long.551")
voir(A.enregistrer_non_verifiable(1, R("Abdul-Mageed"), "communication", tool_context=ctx), "CONFIRMÉE", "ARBERT (mal aiguillé)")
DC["10.48550/arxiv.2304.11085"] = {"titre":"Testing the Reliability of ChatGPT for Text Annotation and Classification: A Cautionary Remark","sous_titre":"","auteurs":[("Reiss","Michael V.")],"annees":{2023},"revue":"arXiv","volume":"","numero":"","pages":"","doi":"10.48550/arxiv.2304.11085"}
voir(A.enregistrer_non_verifiable(31, R("Reiss"), "prépublication", tool_context=ctx), "CONFIRMÉE", "Reiss (mal aiguillé)")
CR["keeping humans"] = cr("Keeping Humans in the Loop: Human-Centered Automated Annotation with Generative AI",[("Pangakis","Nicholas"),("Wolken","Samuel")],[2025],"Proceedings of the International AAAI Conference on Web and Social Media","19","1","1471-1492",doi="10.1609/icwsm.v19i1.35883")
voir(A.verifier_ouvrage(28, R("Pangakis"), "Keeping humans in the loop", "2025", "Pangakis", tool_context=ctx), "CONFIRMÉE", "Pangakis (pris pour un livre)")
# Gilardi : sans DOI dans le texte -> recherche ; note « DOI disponible »
CR["crowd workers"] = cr("ChatGPT outperforms crowd workers for text-annotation tasks",[("Gilardi","Fabrizio"),("Alizadeh","Meysam"),("Kubli","Maël")],[2023],"Proceedings of the National Academy of Sciences","120","30","e2305016120",doi="10.1073/pnas.2305016120")
r = A.verifier_article(13, R("Gilardi"), "ChatGPT outperforms crowd workers for text-annotation tasks", "2023", "Proceedings of the National Academy of Sciences", tool_context=ctx)
voir(r, "CONFIRMÉE", "Gilardi"); print("    note :", [x for x in r["ecarts"].split(" ; ") if "DOI" in x])
# V5-5 : Winata « G. I. » ; Crossref ne donne que « Genta » ; OpenAlex donne le nom complet
CR["code-switching"] = cr("The Decades Progress on Code-Switching Research in NLP: A Systematic Survey on Trends and Challenges",[("Winata","Genta"),("Aji","Alham Fikri"),("Yong","Zheng Xin"),("Solorio","Thamar")],[2023],"Findings of the Association for Computational Linguistics: ACL 2023","","","2936-2978",doi="10.18653/v1/2023.findings-acl.185")
OA["10.18653/v1/2023.findings-acl.185"] = {"noms_complets":["Genta Indra Winata","Alham Fikri Aji","Zheng-Xin Yong","Thamar Solorio"]}
voir(A.verifier_article(37, R("Winata"), "The decades progress on code-switching research in NLP: A systematic survey on trends and challenges", "2023", "Findings of the Association for Computational Linguistics: ACL 2023", tool_context=ctx), "CONFIRMÉE", "Winata (initiales)")
# V5-5, contre-épreuve : Ledwich « M. A. Z. », OpenAlex « Mark Ledwich » -> reste À VÉRIFIER
CR["algorithmic extremism"] = cr("Algorithmic extremism: Examining YouTube's rabbit hole of radicalization",[("Ledwich","Mark"),("Zaitsev","Anna")],[2020],"First Monday","","","",doi="10.5210/fm.v25i3.10419")
OA["10.5210/fm.v25i3.10419"] = {"noms_complets":["Mark Ledwich","Anna Zaitsev"]}
voir(A.verifier_article(29, "Ledwich, M. A. Z., & Zaitsev, A. (2020). Algorithmic extremism: Examining YouTube’s rabbit hole of radicalization. First Monday, 25(3). https://doi.org/10.5210/fm.v25i3.10419", "Algorithmic extremism: Examining YouTube’s rabbit hole of radicalization", "2020", "First Monday", tool_context=ctx), "À VÉRIFIER", "Ledwich (contre-épreuve)")
# V5-1 : GPT-3 — Sigler omis ne doit plus être « rapproché » de Ziegler
noms = [("Brown","Tom B."),("Mann","Benjamin"),("Ryder","Nick"),("Subbiah","Melanie"),("Kaplan","Jared"),("Dhariwal","Prafulla"),("Neelakantan","Arvind"),("Shyam","Pranav"),("Sastry","Girish"),("Askell","Amanda"),("Agarwal","Sandhini"),("Herbert-Voss","Ariel"),("Krueger","Gretchen"),("Henighan","Tom"),("Child","Rewon"),("Ramesh","Aditya"),("Ziegler","Daniel M."),("Wu","Jeffrey"),("Winter","Clemens"),("Hesse","Christopher"),("Chen","Mark"),("Sigler","Eric"),("Litwin","Mateusz"),("Gray","Scott"),("Chess","Benjamin"),("Clark","Jack"),("Berner","Christopher"),("McCandlish","Sam"),("Radford","Alec"),("Sutskever","Ilya"),("Amodei","Dario")]
DC["10.48550/arxiv.2005.14165"] = {"titre":"Language Models are Few-Shot Learners","sous_titre":"","auteurs":noms,"annees":{2020},"revue":"arXiv","volume":"","numero":"","pages":"","doi":"10.48550/arxiv.2005.14165"}
brown = "Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., Amodei, D. (2020). Language models are few-shot learners. Advances in Neural Information Processing Systems, 33, 1877–1901. https://doi.org/10.48550/arXiv.2005.14165"
r = A.verifier_article(3, brown, "Language models are few-shot learners", "2020", "Advances in Neural Information Processing Systems", tool_context=ctx)
bruit = [x for x in r["ecarts"].split(" ; ") if "Ziegler" in x or "ordre" in x]
print(("OK  " if not bruit else "XX  ") + f"GPT-3 : écarts parasites Ziegler/ordre = {bruit or 'aucun'} ; Sigler déclaré omis : {'Sigler' in r['ecarts']}")
# titre lu dans le texte brut
print("titre brut :", A._titre_brut(R("Abdul-Mageed"))[:70], "|", A._titre_brut("Churchill G.A (1979), A paradigm for developing better measures, Journal of marketing, vol 16, p. 64-73.")[:60])
