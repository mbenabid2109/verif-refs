import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI)); sys.path.insert(0, ICI)
DATA = os.path.join(ICI, "data")
import verif_refs.core as A

class FakeState(dict):
    def to_dict(self): return dict(self)
class Ctx:
    def __init__(self): self.state = FakeState()

def cr(title, fam_giv, years, revue, vol="", iss="", page="", sub="", doi="10.x/y"):
    return {"titre": title, "sous_titre": sub, "auteurs": fam_giv, "annees": set(years),
            "revue": revue, "volume": vol, "numero": iss, "pages": page, "doi": doi}

CR = {}   # clé = mot du titre -> notice
OA = {}
OL = {}
A._crossref = lambda brute, doi: [v for k, v in CR.items() if k in brute.lower()]
A._openalex = lambda doi: OA.get(doi, {})
A._openlibrary = lambda t, a: [v for k, v in OL.items() if k in t.lower()]

CR["inequity"] = cr("Towards an understanding of inequity.", [("Adams","J. Stacy")], [1963], "The Journal of Abnormal and Social Psychology","67","5","422-436")
CR["paywall"] = cr("Behind the newspaper paywall – lessons in charging for online content: a comparative analysis of why Australian newspapers are stuck in the purgatorial space between digital and print", [("Carson","Andrea")], [2015], "Media, Culture & Society","37","7","1022-1041")
CR["mobile news adoption"] = cr("Mobile News Adoption among Young Adults", [("Chan-Olmsted","Sylvia"),("Rim","Hyejoon"),("Zerba","Amy")],[2013],"Journalism & Mass Communication Quarterly","90","1","126-147", sub="Examining the Roles of Perceptions, News Consumption, and Media Usage")
CR["tuaut"] = cr("Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle UTAUT", [("BOURDON","Isabelle"),("HOLLET-HAUDEBERT","Sandrine")],[2009],"Systèmes d'Information et Management","14","1","9-36")
CR["better measures"] = cr("A Paradigm for Developing Better Measures of Marketing Constructs", [("Churchill","Gilbert A.")],[1979],"Journal of Marketing Research","16","1","64-73")
CR["news on new devices"] = cr("News on New Devices", [("Chyi","Hsiang Iris"),("Chadha","Monica")],[2012],"Journalism Practice","6","4","431-449", sub="Is multi-platform news consumption a reality?")
CR["social cognitive"] = cr("Social Cognitive Theory and Individual Reactions to Computing Technology: A Longitudinal Study", [("Compeau","Deborah"),("Higgins","Christopher A."),("Huff","Sid")],[1999],"MIS Quarterly","23","2","145")
CR["extrinsic"] = cr("Extrinsic and Intrinsic Motivation to Use Computers in the Workplace", [("Davis","Fred D."),("Bagozzi","Richard P."),("Warshaw","Paul R.")],[1992],"Journal of Applied Social Psychology","22","14","1111-1132")
CR["gratuité"] = cr("La gratuité est-elle une fatalité sur les marchés numériques ? Une étude sur le consentement à payer pour des offres de contenus audiovisuels sur internet", [("Dejean","Sylvain"),("Pénard","Thierry"),("Suire","Raphaël")],[2010,2011],"Économie & prévision","194","3","15-32")
CR["will internet users"] = cr("Will Internet Users Pay for Online Content?", [("Dou","Wenyu")],[2004],"Journal of Advertising Research","44","4","349-359")
CR["long tail"] = cr("The long tail of social networking.", [("Enders","Albrecht"),("Hungenberg","Harald"),("Denker","Hans-Peter"),("Mauch","Sebastian")],[2008],"European Management Journal","26","3","199-211")
CR["willingness to pay for online news."] = cr("An Empirical Study of Factors that Influence the Willingness to Pay for Online News", [("Goyanes","Manuel")],[2014],"Journalism Practice","8","6","742-757")
CR["social commerce"] = cr("Social commerce constructs and consumer's intention to buy", [("Hajli","Nick")],[2015],"International Journal of Information Management","35","2","183-191")
CR["continuité"] = cr("Les services Internet Mobile en France : une proposition de mesure de la continuité d'usage", [("Jelassi","Kaouther"),("Ammi","Chantal")],[2011],"Management & Avenir","","45","238-256")
CR["just say no"] = cr("Just Say No to Traditional Student Samples", [("Jones","William L"),("Sonner","Brenda S")],[2001],"Journal of Advertising Research","41","5","63-70", doi="10.2501/JAR-41-5-63-71")
OA["10.2501/JAR-41-5-63-71"] = {"volume":"41","numero":"5","pages":"63-71"}
CR["who survives"] = cr("Social networking websites: who survives?", [("Mangani","Andrea")],[2017],"Applied Economics","49","48","4885-4896")
CR["movie broadcasts"] = cr("Competing with Free: The Impact of Movie Broadcasts on DVD Sales and Internet Piracy1", [("Smith","Michael D."),("Telang","Rahul")],[2009],"MIS Quarterly","33","2","321")
CR["student samples :"] = cr("The use and misuse of student samples: An empirical investigation of European marketing research", [("Ashraf","Rohail"),("Merunka","Dwight")],[2016,2017],"Journal of Consumer Behaviour","16","4","295-308")
CR["pavlou"] = cr("Consumer Acceptance of Electronic Commerce: Integrating Trust and Risk with the Technology Acceptance Model", [],[2003],"International Journal of Electronic Commerce","7","3","101-134")
CR["factors influencing online music"] = cr("Factors influencing online music purchase intention in Taiwan", [("Chu","Ching‐Wen"),("Lu","Hsi‐Peng")],[2007],"Internet Research","17","2","139-155", sub="An empirical study based on the value‐intention framework")

OL["work and motivation"] = {"titre":"Work and motivation","sous_titre":"","auteurs":[("Vroom","Victor Harold")],"annees":{1964,1982,1995},"editeurs":["Wiley"]}
OL["a beginner"] = {"titre":"A beginner's guide to structural equation modeling","sous_titre":"","auteurs":[("Schumacker","Randall E."),("Lomax","Richard G.")],"annees":{1996,2004,2010},"editeurs":["Psychology Press","L. Erlbaum"]}
OL["market"] = {"titre":"Market","sous_titre":"études et recherches en marketing","auteurs":[("Evrard","Yves"),("Pras","Bernard"),("Roux","Elyette")],"annees":{1993,2000,2003},"editeurs":["Dunod"]}
OL["equity"] = {"titre":"Equity","sous_titre":"theory and research","auteurs":[("Walster","Elaine"),("Walster","G. William"),("Berscheid","Ellen")],"annees":{1978},"editeurs":["Allyn and Bacon"]}
OL["belief, attitude"] = {"titre":"Belief, attitude, intention, and behavior","sous_titre":"","auteurs":[("Fishbein","Martin"),("Ajzen","Icek")],"annees":{1975,1977},"editeurs":["Addison-Wesley"]}

ctx = Ctx()
art = A.verifier_article
ouv = A.verifier_ouvrage
cas = [
 (1,  art, dict(reference_brute="Adams J. S. (1963), Towards an understanding of inequity. The Journal of Abnormal and Social Psychology, vol. 67, n° 5, p. 422.", titre="Towards an understanding of inequity", annee="1963", revue="The Journal of Abnormal and Social Psychology", volume="67", numero_fascicule="5", pages="422"), "À COMPLÉTER"),
 (3,  art, dict(reference_brute="Ashraf R. & Merunka D. (2017), The use and misuse of student samples : An empirical investigation of European marketing research, Journal of Consumer Behaviour, vol. 16, n° 4, p. 295-308.", titre="The use and misuse of student samples : An empirical investigation of European marketing research", annee="2017", revue="Journal of Consumer Behaviour", volume="16", numero_fascicule="4", pages="295-308"), "CONFIRMÉE"),
 (4,  art, dict(reference_brute="Bourdon I. et Hollet-haudebert S. (2009), Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle TUAUT, Systèmes d’information & management, vol. 14, n° 1, p. 9-36.", titre="Pourquoi contribuer à des bases de connaissances ? Une exploration des facteurs explicatifs à la lumière du modèle TUAUT", annee="2009", revue="Systèmes d’information & management", volume="14", numero_fascicule="1", pages="9-36"), "ERREUR"),
 (6,  art, dict(reference_brute="Carson A. (2015), Behind the newspaper paywall-lessons in charging for online content : a comparative analysis of why Australian newspapers are stuck in the purgatorial space between digital and print, Media, Culture & Society, vol. 37, n° 7, p. 1022-1041.", titre="Behind the newspaper paywall-lessons in charging for online content : a comparative analysis of why Australian newspapers are stuck in the purgatorial space between digital and print", annee="2015", revue="Media, Culture & Society", volume="37", numero_fascicule="7", pages="1022-1041"), "CONFIRMÉE"),
 (8,  art, dict(reference_brute="Chan-olmsted S., Rim H. & Zerba A. (2013), Mobile news adoption among young adults : Examining the roles of perceptions, news consumption, and media usage, Journalism & Mass Communication Quarterly, vol. 90, n° 1, p. 126-147.", titre="Mobile news adoption among young adults : Examining the roles of perceptions, news consumption, and media usage", annee="2013", revue="Journalism & Mass Communication Quarterly", volume="90", numero_fascicule="1", pages="126-147"), "ERREUR"),
 (9,  art, dict(reference_brute="Chu C.-W. & Lu H.-P. (2007), Factors influencing online music purchase intention in Taiwan : An empirical study based on the value-intention framework, Internet Research, vol. 17, n° 2, p. 139-155.", titre="Factors influencing online music purchase intention in Taiwan : An empirical study based on the value-intention framework", annee="2007", revue="Internet Research", volume="17", numero_fascicule="2", pages="139-155"), "CONFIRMÉE"),
 (11, art, dict(reference_brute="Churchill G.A (1979), A paradigm for developing better measures of marketing constructs, Journal of marketing, vol 16, p. 64-73.", titre="A paradigm for developing better measures of marketing constructs", annee="1979", revue="Journal of marketing", volume="16", pages="64-73"), "ERREUR"),
 (13, art, dict(reference_brute="Chyi H. I. & Chadha M. (2011, April), News on new devices : Examining multiplatform news consumption in the digital age, In International Symposium on Online Journalism, Austin, Texas.", titre="News on new devices : Examining multiplatform news consumption in the digital age", annee="2011", revue="International Symposium on Online Journalism"), "NON VÉRIFIABLE"),
 (15, art, dict(reference_brute="Compeau D., Higgins C. A. & Huff S. (1999), Social cognitive theory and individual reactions to computing technology : A longitudinal study, MIS quarterly, p. 145-158.", titre="Social cognitive theory and individual reactions to computing technology : A longitudinal study", annee="1999", revue="MIS quarterly", pages="145-158"), "À COMPLÉTER"),
 (20, art, dict(reference_brute="Davis F.D., Bagozzi R.P. & Warshaw P.R. (1992), Extrinsic and intrinsic motivation to use computers in the workplace, Journal of Applied Social Psychology, vol. 22, n° 14, p. 111-1132.", titre="Extrinsic and intrinsic motivation to use computers in the workplace", annee="1992", revue="Journal of Applied Social Psychology", volume="22", numero_fascicule="14", pages="111-1132"), "ERREUR"),
 (21, art, dict(reference_brute="Dejean S., Pénard T. & Suire R. (2010), La gratuité est-elle une fatalité sur les marchés numériques ? Une étude sur le consentement à payer pour des offres de contenus audiovisuels sur internet, Economie & prévision, n° 3, p. 15-32.", titre="La gratuité est-elle une fatalité sur les marchés numériques ? Une étude sur le consentement à payer pour des offres de contenus audiovisuels sur internet", annee="2010", revue="Economie & prévision", numero_fascicule="3", pages="15-32"), "À COMPLÉTER"),
 (22, art, dict(reference_brute="Dou W. (December 2004), Will Internet users pay for online content, Journal of Advertising Research, vol. 44, n° 4, p. 349-359.", titre="Will Internet users pay for online content", annee="2004", revue="Journal of Advertising Research", volume="44", numero_fascicule="4", pages="349-359"), "ERREUR"),
 (23, art, dict(reference_brute="Enders A., Hungenberg H., Denker H. P. & Mauch S. (2008), The long tail of social networking. Revenue models of social networking sites, European Management Journal, vol. 26, n° 3, p. 199-211.", titre="The long tail of social networking. Revenue models of social networking sites", annee="2008", revue="European Management Journal", volume="26", numero_fascicule="3", pages="199-211"), "CONFIRMÉE"),
 (29, art, dict(reference_brute="Goyane M. (2014), An empirical study of factors that influence the willingness to pay for online news. Journalism Practice, vol. 8, n° 6, p. 742-757.", titre="An empirical study of factors that influence the willingness to pay for online news", annee="2014", revue="Journalism Practice", volume="8", numero_fascicule="6", pages="742-757"), "ERREUR"),
 (30, art, dict(reference_brute="Hajli N. (2015), Social commerce constructs and consumer’s intention to buy, International Journal of Information Management, vol. 35, n° 2, p. 183-191.", titre="Social commerce constructs and consumer’s intention to buy", annee="2015", revue="International Journal of Information Management", volume="35", numero_fascicule="2", pages="183-191"), "CONFIRMÉE"),
 (35, art, dict(reference_brute="Jelassi K. & Ammi C. (2011), Les services Internet Mobile en France : une proposition de mesure de la continuité d’usage, Management & Avenir, n° 5, p. 238-256.", titre="Les services Internet Mobile en France : une proposition de mesure de la continuité d’usage", annee="2011", revue="Management & Avenir", numero_fascicule="5", pages="238-256"), "À COMPLÉTER"),
 (38, art, dict(reference_brute="Jones W. L. & Sonner B. S. (2001), Just say no to traditional student samples, Journal of Advertising Research, vol. 41, n° 5, p. 63-71.", titre="Just say no to traditional student samples", annee="2001", revue="Journal of Advertising Research", volume="41", numero_fascicule="5", pages="63-71"), "CONFIRMÉE"),
 (43, art, dict(reference_brute="Mangan A. (2017), Social networking websites : who survives ? Applied Economics, vol. 49, n° 48, p. 4885-4896.", titre="Social networking websites : who survives ?", annee="2017", revue="Applied Economics", volume="49", numero_fascicule="48", pages="4885-4896"), "ERREUR"),
 (45, art, dict(reference_brute="Pavlou P. A. (2003), Consumer acceptance of electronic commerce : Integrating trust and risk with the technology acceptance model. International journal of electronic commerce, vol. 7, n° 3, p. 101-134.", titre="Consumer acceptance of electronic commerce : Integrating trust and risk with the technology acceptance model", annee="2003", revue="International journal of electronic commerce", volume="7", numero_fascicule="3", pages="101-134"), "CONFIRMÉE"),
 (49, art, dict(reference_brute="Smith M. D. & Telang R. (2009), Competing with free : The impact of movie broadcasts on DVD sales and Internet piracy, Mis Quarterly, p. 321-338.", titre="Competing with free : The impact of movie broadcasts on DVD sales and Internet piracy", annee="2009", revue="Mis Quarterly", pages="321-338"), "À COMPLÉTER"),
 (42, ouv, dict(reference_brute="Lomax R. G. & Schumacker R. E. (2004), A beginner’s guide to structural equation modeling, Psychology press.", titre="A beginner’s guide to structural equation modeling", annee="2004", premier_auteur="Lomax", editeur="Psychology press"), "ERREUR"),
 (24, ouv, dict(reference_brute="Evrard Y., Pras B., Roux E. (2009), Market : fondements et méthodes des recherches en marketing, 4e édition, Dunod, Paris.", titre="Market : fondements et méthodes des recherches en marketing", annee="2009", premier_auteur="Evrard", editeur="Dunod"), "NON VÉRIFIABLE"),
 (28, ouv, dict(reference_brute="Fishbein M. & Ajzen I. (1975), Belief, Attitude, Intention and Behavior : An Introduction to Theory and Research, Addison-Wesley, Reading, MA.", titre="Belief, Attitude, Intention and Behavior : An Introduction to Theory and Research", annee="1975", premier_auteur="Fishbein", editeur="Addison-Wesley"), "CONFIRMÉE"),
 (58, ouv, dict(reference_brute="Vroom V.C. (1964), Work and motivation, New York : John Wiley Sons.", titre="Work and motivation", annee="1964", premier_auteur="Vroom", editeur="John Wiley Sons"), "ERREUR"),
 (59, ouv, dict(reference_brute="Walster E., Walster G. W. & Berscheid E. (1978), Equity : Theory and research.", titre="Equity : Theory and research", annee="1978", premier_auteur="Walster"), "À COMPLÉTER"),
]
# pour que la recherche simulée trouve Pavlou/Ashraf
CR["pavlou"]; 
ok = 0
for num, f, kw, attendu in cas:
    brute = kw["reference_brute"]
    if f is art and "Pavlou" in brute: A._crossref = (lambda b,d, _o=A._crossref: [CR["pavlou"]] if "Pavlou" in b else _o(b,d))
    r = f(num, tool_context=ctx, **kw)
    bon = r["verdict"] == attendu
    ok += bon
    print(("OK  " if bon else "XX  ") + f"{num:>2} {r['verdict']:<15} attendu {attendu:<15} | {r['ecarts']}")
print(f"\n{ok}/{len(cas)} conformes")
print(A.synthese(tool_context=ctx)["tableau"].splitlines()[-1])
