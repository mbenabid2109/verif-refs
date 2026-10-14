# Concevoir et évaluer un agent de vérification bibliographique

**Note méthodologique — conception, test de développement, test de validation et test de stabilité de l'agent « verif_refs » (Google ADK)**

*Document de travail, 26 septembre 2026 — version 2 (ajout du test de stabilité, versions 5 et 5.1)*

---

## 1. Introduction

La vérification des références bibliographiques est une tâche fastidieuse, rarement faite de manière exhaustive, et dont les défaillances se propagent : une référence erronée, une fois publiée, est reprise d'article en article. Les modèles de langage semblent pouvoir l'automatiser, mais ils sont eux-mêmes connus pour produire des références plausibles et fausses. La question posée ici est donc double : peut-on construire un agent qui vérifie des références de manière **fiable**, et comment établir cette fiabilité sans se contenter d'une démonstration réussie ?

La note documente une démarche en trois temps. Un premier test, dit de développement, a servi à concevoir l'agent par itérations successives sur une bibliographie de 60 références. Un deuxième test, dit de validation, a évalué la version figée sur une bibliographie nouvelle de 43 références, selon un protocole fixé à l'avance : version gelée, corrigé et prédictions établis avant l'exécution, indicateurs définis a priori. Un troisième test a porté sur la bibliographie d'un manuscrit de l'auteur (40 références), avec deux exécutions par version afin de mesurer la **stabilité** des verdicts.

Quatre résultats ressortent. D'abord, l'architecture efficace n'est pas celle qui confie le plus au modèle de langage, mais celle qui lui retire toute tâche de comparaison exacte. Ensuite, une seconde source n'apporte pas un second avis lorsqu'elle s'alimente à la première. Puis, l'agent validé détecte 95 % des erreurs majeures qu'il peut vérifier, avec une précision de 95 %, mais il peut certifier à tort une référence erronée lorsque la source consultée est incomplète. Enfin, la variabilité d'une exécution à l'autre se loge exclusivement dans les décisions laissées au modèle ; lorsque le code les reprend, la stabilité passe de 87 % à 100 %, et le modèle cesse d'inventer des DOI.

## 2. Dispositif technique

### 2.1 Cadre

L'agent repose sur l'Agent Development Kit de Google (ADK, version 2.10.0 pour Python) et sur le modèle `gemini-flash-lite-latest`, avec relances automatiques en cas de surcharge du service (erreurs 429 et 503). Il s'exécute localement sous Windows et s'utilise via l'interface de développement `adk web`.

Son principe relève du paradigme ReAct (Yao et al., 2023) : le modèle raisonne, décide d'appeler un outil, observe le résultat, puis conclut. L'interface d'ADK rend ce cycle observable, appel par appel, ce qui a été essentiel pour diagnostiquer les défaillances.

### 2.2 Sources

Trois sources ouvertes sont interrogées :

- **Crossref**, registre des DOI et de leurs métadonnées déposées par les éditeurs (Hendricks et al., 2020), pour les articles et les actes de conférence ;
- **DataCite** (à partir de la v5), pour les DOI non enregistrés chez Crossref : prépublications arXiv, rapports d'institutions ;
- **OpenAlex**, index bibliographique ouvert (Priem et al., 2022), comme second avis sur le volume, le numéro, les pages et l'année ;
- **Open Library**, pour les ouvrages (auteurs, années des éditions, éditeurs).

### 2.3 Évolution de l'architecture

| Version | Principe | Issue |
|---|---|---|
| v1 | Le modèle interroge Crossref et compare titre, auteurs, année et revue | L'outil ne transmettait ni volume, ni numéro, ni pages : des « correspondances parfaites » affirmées sur des champs jamais vus |
| v2 | Champs complets transmis ; règles de comparaison dans les instructions | 54/60 verdicts justes ; confusion entre information absente et information fausse |
| v3 | Deux sources ajoutées, quatre verdicts, règles de normalisation détaillées confiées au modèle | Régression (23/30 sur trois lots) ; test interrompu |
| v4 → v4.2 | **Partage des rôles** : le modèle classe et extrait ; le code Python compare, décide et compte | 57/60 en développement ; version figée pour la validation |
| v5 | Chaîne de trois agents (chargement d'un fichier, boucle de vérification par lots avec condition d'arrêt explicite, rapport exporté) ; correctifs issus de la validation | Stabilité de 87 % ; DOI inventés par le modèle |
| v5.1 | Le code reprend les deux dernières décisions instables : lecture du DOI et aiguillage | Stabilité de 100 % ; aucun DOI inventé |

Le passage de la v3 à la v4 constitue le principal enseignement de conception (voir section 7.1). Dans la v4, le modèle ne fait plus que trois choses : déterminer le type de document, recopier les champs, appeler l'outil adapté. Tout le reste est déterministe : recherche de la notice, contrôle d'identité du document, normalisation (casse, apostrophes, tirets, entités HTML, appels de note), comparaison champ par champ, recoupement, verdict, tableau et décompte final. Le code relit en outre lui-même, dans le texte brut, l'année, le volume, le numéro, les pages et les noms d'auteurs, de sorte qu'une erreur de recopie du modèle ne puisse pas devenir une fausse erreur de la référence.

Quatre verdicts sont possibles jusqu'à la v4.2 : **CONFIRMÉE** (aucun écart sur les champs vérifiés), **ERREUR** (la référence contredit la source), **À COMPLÉTER** (un champ présent dans la source manque dans la référence), **NON VÉRIFIABLE** (aucune source ne contient le document). La v5 en ajoute un cinquième, **À VÉRIFIER**, pour un écart que la source consultée ne permet pas de trancher (par exemple, un auteur de la référence absent d'une notice incomplète) : l'agent ne confirme plus ce qu'il ne peut pas établir.

À partir de la v5, l'agent devient une chaîne de trois agents ADK (`SequentialAgent`). Un **chargeur** lit un fichier (.docx, .txt, .bib, .ris) ou un texte collé et découpe la bibliographie ; une **boucle** (`LoopAgent`) vérifie un lot de dix références à chaque tour et s'arrête d'elle-même lorsque l'outil qui distribue les lots signale l'épuisement de la liste ; un **rapporteur** produit le tableau et l'enregistre en .md et .csv.

## 3. Protocole

### 3.1 Corpus

**Corpus de développement.** 60 références extraites d'un article francophone de sciences de gestion, au format « vol., n°, p. ». Il mêle articles internationaux, articles francophones diffusés par Cairn, ouvrages, thèse, rapports, communications et presse professionnelle. Il a été découpé en six lots de dix.

**Corpus de validation.** 43 références extraites d'un article publié dans *Political Communication*, au format APA avec DOI. Il diffère du premier par le domaine (communication politique et audit algorithmique), par le format, et par la forte présence d'actes de conférences en informatique, de rapports et d'articles de presse. Les références, coupées par la mise en page, ont été reconstituées par script ; les 31 DOI ont été contrôlés. Il a été découpé en cinq lots.

**Corpus de stabilité.** 40 références extraites d'un manuscrit de l'auteur sur la fiabilité de l'annotation assistée par LLM, au format APA. La bibliographie mêle articles de revues de méthodes, actes de conférences en traitement automatique des langues, prépublications et ouvrages. Chaque version (v5 puis v5.1) y a été exécutée deux fois, dans deux sessions distinctes, sur le même fichier.

### 3.2 Règles

1. **Gel de version.** Aucune modification de l'agent pendant un passage complet ; les défauts sont consignés et corrigés ensuite.
2. **Corrigé préalable.** Pour la validation, le corrigé a été établi et archivé avant toute exécution. Six références douteuses ont été vérifiées en ligne (pages d'éditeur, DBLP, CV d'auteurs) ; les autres reposent sur la connaissance du correcteur et sont marquées comme telles.
3. **Prédictions enregistrées.** Pour chaque référence, le verdict que l'agent *devrait* rendre compte tenu de sa conception a été consigné à l'avance, limites comprises.
4. **Indicateurs fixés a priori** : conformité aux prédictions, précision des signalements, taux de détection, justesse de la catégorie, couverture.
5. **Transparence des amendements.** Lorsque l'agent a relevé une erreur absente du corrigé, le corrigé n'a pas été modifié silencieusement ; l'amendement a été consigné.
6. **Double exécution** (troisième test). Chaque version est exécutée deux fois sur le même corpus ; la stabilité est la part de lignes strictement identiques d'une exécution à l'autre.

Une nuance s'impose pour le corpus de développement. Ses règles ayant été ajustées au vu de ses propres résultats, et le lot 1 ayant été rejoué après correction de la v4.0, les performances qui y sont mesurées sont optimistes par construction. Seul le test de validation mesure la capacité de l'agent à se généraliser. La même réserve vaut pour la v5.1 sur le troisième corpus, construite à partir des défauts observés sur ce corpus : son exactitude y est optimiste, sa stabilité en revanche est une mesure pleinement valide.

## 4. Test de développement (60 références)

### 4.1 Résultats par version

| Indicateur | v2 | v3 (lots 1-3) | v4.1 |
|---|---|---|---|
| Verdicts justes | 54/60 | 23/30 | **57/60** |
| Fausses alertes | 4 | 6 | 3 (dont 2 erreurs de catégorie) |
| Précision des signalements | ≈ 70 % | — | **85 %** |
| Problèmes réels détectés | 13 | — | **17** |
| Références non vérifiables | 13 (22 %) | — | **9 (15 %)** |
| Points de contrôle détectés | 4/5 | — | **5/5** |

Les points de contrôle étaient quatre erreurs repérées par le correcteur avant le test (mauvaise revue, pagination erronée, nom d'auteur tronqué, initiales fausses), auxquelles s'est ajoutée une pagination incomplète. L'agent a par ailleurs relevé deux erreurs réelles que le correcteur avait manquées : un nom d'auteur tronqué et un ordre d'auteurs inversé.

### 4.2 Défauts découverts sur données réelles

Chaque passage réel a révélé des défauts que des tests sur notices simulées ne pouvaient pas faire apparaître :

| Code | Défaut | Cas révélateur |
|---|---|---|
| — | Entités HTML de Crossref (`&amp;`) empêchant l'égalité de deux noms de revue identiques | article de *Media, Culture & Society* |
| — | Erreur de recopie des pages par le modèle, transformée en fausse erreur de la référence | pages d'une autre référence recopiées |
| D1 | Date de mise en ligne ou de redépôt (Cairn) prise pour une erreur d'année | notice datée de 2026 pour un article de 2009 |
| D2 | Appel de note `<sup>1</sup>` intégré au titre Crossref | article de 1992 |
| D3 | Numéro cumulé rangé par Crossref dans le champ *volume* | revue francophone numérotée en continu |
| D4 | OpenAlex reproduisant l'erreur de pagination de Crossref | pagination attestée par le DOI lui-même |
| D5 | Absence de nouvelle tentative et message d'erreur vide en cas de délai dépassé | panne ponctuelle d'Open Library |

Ces défauts ont été corrigés dans la v4.2, chacun vérifié sur le cas réel qui l'avait révélé, avant le gel.

## 5. Test de validation (43 références)

### 5.1 Composition du corpus

Le corrigé établit 14 références correctes et **29 erronées**, dont 25 gravement. L'anomalie dominante est remarquablement régulière : un auteur disparaît et le nom suivant est dédoublé, avec des initiales agglutinées (par exemple, trois auteurs réduits à « Bakshy, E., Adamic, S. M. L. A., & Adamic, L. A. »). S'y ajoutent une référence aux auteurs méconnaissables, un volume et des pages fantômes attribués à une communication de colloque, et quatre cas d'initiales en excès.

### 5.2 Résultats

| Indicateur | Résultat |
|---|---|
| Conformité aux prédictions | **41/43 (95 %)** |
| Précision des signalements | **19/20 (95 %)** |
| Détection, toutes références erronées | 19/29 (66 %) |
| Détection, références que l'agent pouvait vérifier | **19/24 (79 %)** |
| Détection des erreurs majeures vérifiables | **19/20 (95 %)** |
| Justesse de la catégorie | 14/19 (74 %) |
| Couverture (références non vérifiables) | 11/43 (26 %) |
| Fausses confirmations | 5 (1 imprévue, 4 prévues) |

Pour chaque auteur omis, l'agent **nomme l'auteur disparu** à partir de la notice de référence. Les cinq détections classées À COMPLÉTER au lieu d'ERREUR découlent d'une règle figée qui traitait l'auteur manquant comme une lacune ; elles étaient prévues.

### 5.3 Analyse des écarts

**La fausse alerte.** Un rapport doté d'un DOI enregistré chez DataCite, et non chez Crossref, a déclenché une recherche de repli, qui a trouvé un chapitre d'ouvrage au titre voisin. Le code l'a pris pour le même document. Or une notice portant un DOI différent de celui de la référence ne peut pas désigner le même document (défaut V1).

**La fausse confirmation imprévue.** Pour un ouvrage de 1968 à trois auteurs cité avec un auteur omis, la notice d'Open Library ne mentionnait vraisemblablement que le premier auteur. Le code vérifiant que chaque auteur de la *source* figure dans la référence, mais non l'inverse, tout a paru conforme (défaut V3).

**Les fausses confirmations prévues.** Quatre références comportaient des initiales en excès (« M. A. Z. » pour un auteur prénommé Mark). Le code ne compare que les initiales fournies par la source ; il ne voit donc pas celles qui s'y ajoutent (défaut V5). Cette limite avait été déclarée avant le test.

**Le bruit.** Pour un article à 29 auteurs cité selon la règle APA (19 premiers auteurs, points de suspension, dernier auteur), l'agent a listé neuf auteurs « manquants », dont huit omis légitimement ; seul le dernier manquait réellement (défaut V2). Pour un acte de conférence, une variante d'intitulé a produit un écart parasite (défaut V4).

**L'amendement.** L'agent a relevé un nom composé tronqué (« Kakhki, A. M. » pour Molavi Kakhki) que le corrigé avait manqué. La référence étant déjà classée erronée, les mesures ne changent pas.

## 6. Test de stabilité (40 références, deux exécutions par version)

### 6.1 Corrigé

Le corrigé, établi avant l'exécution, compte une erreur certaine (une communication de 2018 datée de 2019), une référence à compléter (un article cité comme « en ligne » depuis paru en numéro), trois points incertains et une dizaine de DOI existants non cités. L'agent y a ajouté une erreur que le correcteur avait manquée : un titre précédé de la mention « Survey article: », qui est en réalité la rubrique de la revue. C'est le troisième amendement de cette nature au cours des tests.

### 6.2 Résultats

| Indicateur | v5 (2 exécutions) | v5.1 (2 exécutions) |
|---|---|---|
| Références correctement découpées | 38/40 | **40/40** |
| Stabilité (lignes identiques) | 33/38 (87 %) | **40/40 (100 %)** |
| DOI inventés par le modèle | 3 (dont 1 faux) | **0** |
| Références avec DOI laissées sans vérification | 1 à 4 selon l'exécution | **0** |
| Fausses ERREUR | 1 à 2 | **0** |
| Prédictions enregistrées confirmées | — | **toutes** |

### 6.3 Ce que la v5 a révélé

Les cinq lignes instables de la v5 relèvent toutes d'une décision du modèle. Quatre références munies d'un DOI ont été tantôt vérifiées, tantôt classées « communication » ou « prépublication », malgré une instruction explicite. Surtout, pour une référence qui ne comportait **aucun** DOI, le modèle en a fourni un lors de chaque exécution : la première fois, un DOI qui existe mais désigne un tout autre article (il diffère du bon d'un seul caractère), ce qui a produit une fausse ERREUR ; la seconde fois, le DOI exact. Le code acceptait alors un DOI proposé par le modèle en l'absence de DOI dans le texte. L'outil conçu pour détecter les références inventées reproduisait donc, à son propre niveau, le défaut qu'il devait combattre.

Deux défauts déterministes sont également apparus : trois références commençant par une particule (« van Atteveldt », « van der Velden ») ont été fusionnées au découpage, et un rapprochement approximatif a confondu deux noms voisins dans une longue liste d'auteurs.

### 6.4 Correctifs de la v5.1

| Code | Défaut | Correctif |
|---|---|---|
| V5-1 | Rapprochement de noms voisins (Ziegler/Sigler) | un nom appartenant à un autre auteur de la source est exclu du rapprochement |
| V5-2 | Références commençant par une particule fusionnées | particules reconnues en début de référence |
| V5-3 | DOI inventés par le modèle | le modèle ne peut plus transmettre de DOI ; seul le DOI écrit dans la référence est lu |
| V5-4 | Règle d'aiguillage appliquée irrégulièrement | toute référence contenant un DOI est vérifiée par ce DOI, quel que soit le classement du modèle |
| V5-5 | Initiales « en excès » signalées sur des références correctes | recoupement avec les noms complets d'OpenAlex avant signalement |
| — | DOI manquants | note « DOI disponible, absent de la référence » |

## 7. Discussion

### 7.1 Ce qu'il faut confier au modèle, et ce qu'il faut lui retirer

L'échec de la v3 est instructif. Plus les règles de normalisation confiées au modèle étaient nombreuses et précises, moins elles étaient appliquées de manière uniforme : casse, apostrophes et sous-titres absents ont produit des fausses alertes que les instructions interdisaient explicitement. Le même modèle, au même moment, comptait mal les verdicts de son propre tableau. La v4 retient la leçon : le modèle fait ce qu'il fait bien (reconnaître un type de document, repérer des champs dans un texte hétérogène), et le code fait ce qu'il fait bien (appliquer la même règle sans exception). On retrouve le schéma producteur-vérificateur des agents à boucle de validation, avec un vérificateur programmé plutôt qu'un second modèle : plus fiable, gratuit et reproductible.

### 7.2 La circularité des sources

OpenAlex a été introduit comme second avis. Il a reproduit l'erreur de pagination de Crossref, puis sa date de redépôt, parce qu'il reprend une large part de ses métadonnées. Deux bases alimentées à la même source ne font pas deux témoignages. Le mécanisme est celui que les travaux sur la désinformation désignent comme *circular reporting*. La seule confirmation indépendante trouvée est structurelle : lorsque le DOI encode la pagination, il atteste des pages indépendamment des métadonnées déposées.

### 7.3 L'asymétrie des erreurs

Une fausse alerte coûte une vérification inutile. Un verdict NON VÉRIFIABLE laisse le travail à l'humain. Une fausse confirmation, en revanche, certifie une référence erronée, qui ne sera plus contrôlée. L'évaluation d'un tel outil ne peut donc pas se résumer à un taux global de verdicts justes ; elle doit isoler les fausses confirmations. D'où une règle d'usage de la v4.2 : **un verdict CONFIRMÉE ne vaut que pour les champs effectivement vérifiés**, et non pour la référence entière.

### 7.4 La prévisibilité comme critère de confiance

La conformité de 95 % aux prédictions est peut-être le résultat le plus utile. Les échecs de l'agent étaient connus avant l'exécution, à deux exceptions près. Un outil dont les limites sont connues à l'avance peut être employé avec discernement : on sait quels verdicts croire et lesquels contrôler.

### 7.5 La variabilité se loge dans les décisions du modèle

Le troisième test isole avec netteté l'origine de l'instabilité. Tout ce que fait le code est reproduit à l'identique d'une exécution à l'autre, y compris ses erreurs : la fusion fautive de trois références est apparue deux fois, exactement. Tout ce qui varie procède d'une décision du modèle : le choix de l'outil, et la fourniture d'une information absente du texte. En retirant au modèle ces deux décisions, la v5.1 atteint une stabilité complète sans rien changer d'autre. Le constat rejoint la littérature sur la fiabilité des annotations produites par des modèles de langage, qui souligne la variabilité des sorties d'une exécution à l'autre (Reiss, 2023) : la réponse proposée ici n'est pas de fixer davantage le modèle, mais de restreindre le périmètre de ses décisions à celles qui ne peuvent pas modifier un verdict.

La fourniture d'un DOI inventé mérite une attention particulière. Le modèle ne l'a pas produit en réponse à une demande : il l'a ajouté spontanément dans un champ facultatif. Une consigne interdisant d'« ajouter une information absente » n'aurait pas suffi à garantir le comportement ; seule la suppression du champ le garantit.

### 7.6 Un constat sur le corpus de validation

Vingt-neuf références erronées sur quarante-trois, dans une revue de premier rang, avec une signature caractéristique d'un logiciel de gestion bibliographique, illustrent la fragilité des métadonnées scientifiques face aux outils automatiques et à l'absence de contrôle en aval. Un seul article ne constitue pas un échantillon ; le constat justifie toutefois un audit systématique.

## 8. Limites

- **Le corrigé est l'œuvre d'un évaluateur unique**, établi en partie de mémoire ; il n'a pas été contre-vérifié par une seconde personne. Deux erreurs réelles lui ont échappé au cours des tests.
- **La stabilité n'a été mesurée que sur le troisième corpus**, à raison de deux exécutions par version. Deux exécutions suffisent à révéler une instabilité, pas à établir sa fréquence.
- **Deux corpus, deux articles.** Les effectifs (60 et 43) restent modestes et chaque corpus reflète les habitudes d'un seul article.
- **Un seul modèle** (Gemini flash-lite) : les résultats ne se transposent pas directement à d'autres modèles.
- **Dépendance aux sources ouvertes**, à leur couverture (faible pour les ouvrages francophones, nulle pour la presse) et à leur disponibilité.
- **Les corpus de validation et de stabilité ont désormais servi à identifier des défauts** : ils ne peuvent plus valider une version ultérieure. La v5.1 n'a pas encore été évaluée sur un corpus indépendant.
- **Le contrôle du corrigé par l'auteur**, prévu pour le troisième test, portait sur trois points précis ; il reste à consigner.

## 9. Suite des travaux

**Cahier des charges de la version 5**, établi avant tout codage (réalisé ; voir section 6) :

| Code | Correctif | Justification |
|---|---|---|
| V1 | Une notice dont le DOI diffère de celui de la référence est un autre document | fausse alerte (rapport DataCite) |
| V2 | Reconnaître les points de suspension APA ; ne vérifier alors que le dernier auteur | bruit (article à 29 auteurs) |
| V3 | Contrôle inverse : des auteurs de la référence absents de la source interdisent la confirmation | fausse confirmation (ouvrage de 1968) |
| V4 | Tolérer les variantes d'intitulé des actes de conférence | écart parasite |
| V5 | Signaler les initiales en excès | quatre fausses confirmations prévues |
| Règle | Un auteur omis relève de l'ERREUR, non de la lacune | justesse de catégorie à 74 % |

Deux extensions de couverture sont envisageables : DataCite pour les DOI non enregistrés chez Crossref, et une source spécialisée pour les actes de conférence sans DOI.

**Validation de la v5.1.** Elle devra être évaluée sur une bibliographie encore jamais utilisée, selon le même protocole, avec un corrigé contre-vérifié par une seconde personne et au moins trois exécutions pour estimer la fréquence d'éventuelles instabilités.

**Limites restant à traiter.** Les communications de conférence sans DOI (environ une référence sur huit dans le troisième corpus) restent hors de portée ; une source spécialisée (ACL Anthology, DBLP) permettrait de les couvrir. Les notices incomplètes d'Open Library produisent des « À VÉRIFIER » sur des ouvrages corrects ; une seconde source d'ouvrages réduirait ce bruit.

**Recherche.** Un audit de la qualité des bibliographies sur un échantillon raisonné d'articles récents de revues de communication est désormais réalisable avec cet outil.

## 10. Conclusion

L'agent validé n'est pas un vérificateur universel. Il est un détecteur précis des erreurs d'articles indexés, et en particulier des auteurs omis, dont il donne un diagnostic directement exploitable. Hors de ce périmètre, il se tait (NON VÉRIFIABLE) ou, plus rarement et plus dangereusement, confirme à tort. Sa valeur tient moins à ses taux qu'à la connaissance précise de ses limites, acquise par un protocole qui interdisait de les découvrir après coup. Quatre leçons dépassent le cas étudié : retirer au modèle de langage toute tâche de comparaison exacte ; ne pas prendre pour un second avis une source qui reprend la première ; mesurer séparément les fausses confirmations, parce qu'elles sont les seules erreurs qui échappent ensuite à tout contrôle ; enfin, mesurer la stabilité par des exécutions répétées, parce que c'est elle qui révèle les décisions encore laissées au modèle, et qu'une décision qui peut varier sans changer le texte d'entrée ne devrait jamais pouvoir changer un verdict.

---

## Références

Gilardi, F., Alizadeh, M., & Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. *Proceedings of the National Academy of Sciences, 120*(30), e2305016120. https://doi.org/10.1073/pnas.2305016120

Hendricks, G., Tkaczyk, D., Lin, J., & Feeney, P. (2020). Crossref: The sustainable source of community-owned scholarly metadata. *Quantitative Science Studies, 1*(1), 414–427. https://doi.org/10.1162/qss_a_00022

Krippendorff, K. (2019). *Content analysis: An introduction to its methodology* (4e éd.). SAGE.

Pangakis, N., Wolken, S., & Fasching, N. (2023). *Automated annotation with generative AI requires validation* (arXiv:2306.00176). arXiv. https://doi.org/10.48550/arXiv.2306.00176

Priem, J., Piwowar, H., & Orr, R. (2022). *OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts* (arXiv:2205.01833). arXiv. https://doi.org/10.48550/arXiv.2205.01833

Reiss, M. V. (2023). *Testing the reliability of ChatGPT for text annotation and classification: A cautionary remark* (arXiv:2304.11085). arXiv. https://doi.org/10.48550/arXiv.2304.11085

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *International Conference on Learning Representations (ICLR 2023)*.

---

## Annexes (fichiers du dépôt)

- `verif_refs/core.py`, `verif_refs/agent.py`, `verif_refs/cli.py` : version 5.2 (voir l'addendum ci-dessous)
- `data/corpus1_developpement_60refs.md` : corpus de développement (60 références, 6 lots)
- `data/corpus2_validation_43refs.txt` et `data/corpus2_corrige_et_predictions.md` : corpus de validation, corrigé et prédictions établis avant l'exécution
- `tests/` : batterie de non-régression (79 cas, notices simulées, sans accès au réseau)
- Le corpus de stabilité (bibliographie d'un manuscrit non publié) n'est pas distribué.

---

## Addendum — version 5.2 (octobre 2026)

Deux usages réels sur des bibliographies nouvelles ont révélé des fausses alertes que les corpus précédents ne contenaient pas.

- **Bibliographie d'un chapitre d'ouvrage collectif en sciences de gestion (22 références).** La seule erreur réelle (un numéro de revue erroné, « 158 » au lieu de 148) a été détectée, mais cinq des six verdicts ERREUR étaient de fausses alertes, toutes dues à la normalisation des métadonnées de Persée et de Cairn : numéros doubles (« 106–107 », « 3–4 »), préfixe « Vol. », supplément écrit « Suppl_1 », titre enregistré sans accents.
- **Bibliographie sur l'opinion publique (39 références).** Une vraie erreur de pagination a été détectée (Weaver, 1980 : 361–373 et non 361–376, confirmé sur le site de l'éditeur). Les fausses alertes portaient toutes sur les notices d'ouvrages d'Open Library : coauteur fusionné d'une autre œuvre (Tocqueville « et Beaumont »), seconds prénoms absents, notices réduites au premier auteur.

Correctifs de la v5.2 : comparaison des volumes et numéros par leur valeur ; reconnaissance des numéros doubles ; titres comparés sans accents ; notices d'ouvrages traitées comme une source peu fiable (les absences et les initiales supplémentaires deviennent des notes, les contradictions restent signalées) ; noms de famille composés mal découpés par la source signalés en À VÉRIFIER plutôt qu'en « auteur omis ». Une seule prudence est maintenue délibérément : lorsqu'une notice d'ouvrage ne cite que le premier auteur, l'agent rend À VÉRIFIER, car c'est la situation exacte d'une fausse confirmation.

La v5.2 passe les 79 cas de non-régression, mais **n'a pas été validée sur un corpus indépendant**. Comme pour les versions précédentes, ses performances sur les cas qui l'ont inspirée sont optimistes par construction.
