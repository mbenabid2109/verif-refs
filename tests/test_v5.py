import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
DATA = os.path.join(ICI, "data")
import verif_refs.core as A
from test_v4 import cr, CR, OA, OL, Ctx
DC = {}
A._datacite = lambda doi: DC.get(doi.lower(), {})
ctx = Ctx()
R = {l.split(". ",1)[0]: l.strip() for l in open(os.path.join(DATA, "corpus2_43refs.txt"), encoding="utf-8")}  # non utilisé
refs = [l.strip() for l in open(os.path.join(DATA, "corpus2_43refs.txt"), encoding="utf-8")]
def brut(n): return refs[n-1]
def art(n, att, **kw):
    b = brut(n)
    r = A.verifier_article(n, reference_brute=b, titre=kw.pop("titre"), annee=kw.pop("annee"), tool_context=ctx, **kw)
    print(("OK  " if r["verdict"]==att else "XX  ") + f"{n:>2} {r['verdict']:<14} attendu {att:<14} | {r['ecarts'][:230]}")
def ouv(n, att, **kw):
    r = A.verifier_ouvrage(n, reference_brute=brut(n), tool_context=ctx, **kw)
    print(("OK  " if r["verdict"]==att else "XX  ") + f"{n:>2} {r['verdict']:<14} attendu {att:<14} | {r['ecarts'][:230]}")
CR.clear()
# notices simulées (métadonnées réelles connues)
CR["amicus"] = cr("The Ideologies of Organized Interests and Amicus Curiae Briefs: Large-Scale, Social Network Imputation of Ideal Points", [("Abi-Hassan","Sahar"),("Box-Steffensmeier","Janet M."),("Christenson","Dino P."),("Kaufman","Aaron R."),("Libgober","Brian")],[2023],"Political Analysis","31","3","396-413",doi="10.1017/pan.2022.34")
CR["echo chambers"] = cr("Echo Chambers and Filter Bubbles",[],[2024],"Cambridge chapter","","","72-86",doi="10.1017/9781009214414.008")
DC["10.60625/risj-etxj-7k60"] = {"titre":"Echo chambers, filter bubbles, and polarisation: a literature review","sous_titre":"","auteurs":[("Arguedas","Amy Ross"),("Robertson","Craig T."),("Fletcher","Richard"),("Nielsen","Rasmus Kleis")],"annees":{2022},"revue":"Reuters Institute for the Study of Journalism","volume":"","numero":"","pages":"","doi":"10.60625/risj-etxj-7k60"}
CR["exposure to ideologically"] = cr("Exposure to ideologically diverse news and opinion on Facebook",[("Bakshy","Eytan"),("Messing","Solomon"),("Adamic","Lada A.")],[2015],"Science","348","6239","1130-1132",doi="10.1126/science.aaa1160")
CR["birds of the same"] = cr("Birds of the Same Feather Tweet Together: Bayesian Ideal Point Estimation Using Twitter Data",[("Barberá","Pablo")],[2015,2014],"Political Analysis","23","1","76-91",doi="10.1093/pan/mpu011")
CR["quantifying social media"] = cr("Quantifying Social Media’s Political Space: Estimating Ideology from Publicly Revealed Preferences on Facebook",[("BOND","ROBERT"),("MESSING","SOLOMON")],[2015],"American Political Science Review","109","1","62-78",doi="10.1017/s0003055414000525")
CR["political sectarianism"] = cr("Political sectarianism in America",[("Finkel","Eli J."),("Bail","Christopher A."),("Cikara","Mina"),("Ditto","Peter H."),("Iyengar","Shanto"),("Klar","Samara"),("Mason","Lilliana"),("McGrath","Mary C."),("Nyhan","Brendan"),("Rand","David G."),("Skitka","Linda J."),("Tucker","Joshua A."),("Van Bavel","Jay J."),("Wang","Cynthia S."),("Druckman","James N.")],[2020],"Science","370","6516","533-536",doi="10.1126/science.abe1715")
noms29 = [("Guess","Andrew M."),("Malhotra","Neil"),("Pan","Jennifer"),("Barberá","Pablo"),("Allcott","Hunt"),("Brown","Taylor"),("Crespo-Tenorio","Adriana"),("Dimmery","Drew"),("Freelon","Deen"),("Gentzkow","Matthew"),("González-Bailón","Sandra"),("Kennedy","Edward"),("Kim","Young Mie"),("Lazer","David"),("Moehler","Devra"),("Nyhan","Brendan"),("Rivera","Carlos Velasco"),("Settle","Jaime"),("Thomas","Daniel Robert"),("Thorson","Emily"),("Tromble","Rebekah"),("Wilkins","Arjun"),("Wojcieszak","Magdalena"),("Xiong","Beixian"),("de Jonge","Chad Kiewiet"),("Franco","Annie"),("Mason","Winter"),("Stroud","Natalie Jomini"),("Tucker","Joshua A.")]
CR["feed algorithms"] = cr("How do social media feed algorithms affect attitudes and behavior in an election campaign?",noms29,[2023],"Science","381","6656","398-404",doi="10.1126/science.abp9364")
CR["measuring personalization"] = cr("Measuring personalization of web search",[("Hannak","Aniko"),("Sapiezynski","Piotr"),("Molavi Kakhki","Arash"),("Krishnamurthy","Balachander"),("Lazer","David"),("Mislove","Alan"),("Wilson","Christo")],[2013],"Proceedings of the 22nd international conference on World Wide Web","","","527-538",doi="10.1145/2488388.2488435")
CR["algorithmic extremism"] = cr("Algorithmic extremism: Examining YouTube's rabbit hole of radicalization",[("Ledwich","Mark"),("Zaitsev","Anna")],[2020],"First Monday","","","",doi="10.5210/fm.v25i3.10419")
CR["auditing algorithms: understanding"] = cr("Auditing Algorithms: Understanding Algorithmic Systems from the Outside In",[("Metaxa","Danaë"),("Park","Joon Sung"),("Robertson","Ronald E."),("Karahalios","Karrie"),("Wilson","Christo"),("Hancock","Jeff"),("Sandvig","Christian")],[2021],"Foundations and Trends® in Human-Computer Interaction","14","4","272-344",doi="10.1561/1100000083")
CR["radicalization pathways"] = cr("Auditing radicalization pathways on YouTube",[("Ribeiro","Manoel Horta"),("Ottoni","Raphael"),("West","Robert"),("Almeida","Virgílio A. F."),("Meira","Wagner")],[2020],"Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency","","","131-141",doi="10.1145/3351095.3372879")
CR["search engine results"] = cr("Auditing the Personalization and Composition of Politically-Related Search Engine Results Pages",[("Robertson","Ronald E."),("Lazer","David"),("Wilson","Christo")],[2018],"Proceedings of the 2018 World Wide Web Conference on World Wide Web - WWW '18","","","955-965",doi="10.1145/3178876.3186143")
CR["information foraging"] = cr("Information foraging.",[("Pirolli","Peter"),("Card","Stuart")],[1999],"Psychological Review","106","4","643-675",doi="10.1037/0033-295x.106.4.643")
CR["selective exposure"] = cr("Selective Exposure to Information: A Critical Review",[("Sears","David O."),("Freedman","Jonathan L.")],[1967],"Public Opinion Quarterly","31","2","194",doi="10.1086/267513")
CR["discrimination in online"] = cr("Discrimination in online ad delivery",[("Sweeney","Latanya")],[2013],"Queue","11","3","10-29",doi="10.1145/2460276.2460278",sub="Google ads, black names and white names, racial discrimination, and click advertising")
OL.clear()
OL["the people"] = {"titre":"The people's choice","sous_titre":"how the voter makes up his mind in a presidential campaign","auteurs":[("Lazarsfeld","Paul Felix")],"annees":{1944,1948,1968},"editeurs":["Columbia University Press"]}

T = lambda s: s
art(1, "ERREUR", titre="The ideologies of organized interests and amicus curiae briefs: Large-scale, social network imputation of ideal points", annee="2023", revue="Political Analysis")
art(2, "CONFIRMÉE", titre="Echo chambers, filter bubbles, and polarisation: A literature review", annee="2022", revue="Reuters Institute for the Study of Journalism")
art(4, "ERREUR", titre="Exposure to ideologically diverse news and opinion on Facebook", annee="2015", revue="Science")
art(5, "CONFIRMÉE", titre="Birds of the same feather tweet together. Bayesian ideal point estimation using Twitter data", annee="2015", revue="Political Analysis")
art(8, "ERREUR", titre="Quantifying social media’s political space: Estimating ideology from publicly revealed preferences on Facebook", annee="2015", revue="The American Political Science Review")
art(15, "CONFIRMÉE", titre="Political sectarianism in America", annee="2020", revue="Science")
art(18, "ERREUR", titre="How do social media feed algorithms affect attitudes and behavior in an election campaign?", annee="2023", revue="Science")
art(19, "ERREUR", titre="Measuring personalization of web search", annee="2013", revue="Proceedings of the 22nd International Conference on World Wide Web")
art(29, "À VÉRIFIER", titre="Algorithmic extremism: Examining YouTube’s rabbit hole of radicalization", annee="2020", revue="First Monday")
art(30, "CONFIRMÉE", titre="Auditing algorithms: Understanding algorithmic systems from the outside in", annee="2021", revue="Foundations and Trends in Human-Computer Interaction")
art(32, "À VÉRIFIER", titre="Information foraging", annee="1999", revue="Psychological Review")
art(34, "CONFIRMÉE", titre="Auditing radicalization pathways on YouTube", annee="2020", revue="Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency")
art(35, "ERREUR", titre="Auditing the personalization and composition of politically-related search engine results pages", annee="2018", revue="Proceedings of the 2018 World Wide Web Conference")
art(39, "À VÉRIFIER", titre="Selective exposure to information: A critical review", annee="1967", revue="Public Opinion Quarterly")
art(41, "CONFIRMÉE", titre="Discrimination in online ad delivery: Google ads, black names and white names, racial discrimination, and click advertising", annee="2013", revue="Queue")
ouv(28, "À VÉRIFIER", titre="The people’s choice: How the voter makes up his mind in a presidential campaign", annee="1968", premier_auteur="Lazarsfeld", editeur="Columbia University Press")
