# Référence de traduction — Player

Guide de cohérence pour les chapitres non traduits. Cette fiche résume les
conventions observées sans reproduire les dialogues officiels.

## Texte et typographie

- Écrire **tout** le texte en **MAJUSCULES**, y compris les interjections,
  avec les accents (`É`, `È`, `À`, `Ç`, `Ù`, `Œ`).
- Utiliser les guillemets droits `"..."`, jamais `« ... »`.
- Les guillemets entourent uniquement le titre ou le terme cité :
  `"MAÎTRE ÉPÉISTE" ASAKYUN.`
- Utiliser l'apostrophe courbe `’` (`C’EST`, `JUSQU’AU`), jamais `'`.
- Points de suspension : trois points `...`, comme dans la source, sans espace
  avant.
- Conserver la ponctuation et les virgules de la source.
- Mettre une **espace insécable** avant `?`, `!`, `:` et `;`
  (`TU VEUX CHANGER LE PASSÉ ?`, `SÉRIEUX... !`) pour que le signe ne passe
  jamais seul à la ligne. Pas d'espace avant `.` ni `,`.
- Les nombres ordinaux s'écrivent `99E` en capitales (forme typographique
  exacte : `99ᵉ`).
- Centrer le texte horizontalement et verticalement dans chaque bulle.
- Équilibrer les retours à la ligne ; ne pas isoler inutilement un mot.

## Polices

Chaque police doit contenir tous les caractères français (`É È Ê À Â Ç Ù Û Î
Ï Ô Œ ’`) ; une police incomplète est refusée.

Le choix du style se fait **en regardant le lettrage anglais** de chaque bulle :
la version anglaise utilise elle-même plusieurs polices.

| Style | Quand l'utiliser (lettrage anglais) | Police (dossier `fonts/`) |
| --- | --- | --- |
| `dialogue` | Capitales droites, propres, régulières | Anime Ace 2.0 BB, contour 1 px |
| `italique` | Capitales penchées, fines (paroles tendues, chuchotées) | Anime Ace 2.0 BB Italic, contour 1 px |
| `pensee` | Pensées dans les bulles en dents de scie | Anime Ace 2.0 BB Italic, contour 1 px |
| `cri` | Pinceau épais, condensé, irrégulier (cris, exclamations fortes) | Mouse Memoirs, jusqu'à 130 px |
| `chuchotement` | Petits caractères | Anime Ace 2.0 BB, taille réduite |
| `systeme` | Titres de compétence ou fenêtres système, sans bulle | Anton, étiré verticalement |
| `titre` | Titres décoratifs gothiques ou fantasy (ex. `GUARDIAN FORM`) | Metal Mania |
| `cartouche` | Fiches sans bulle en capitales fines et condensées (ex. `EGO WEAPON`, ch. 225) | Oswald (graisse 300) |

Remarque : dans le chapitre 225, la plupart des bulles « en gros » ont un
lettrage **marqueur droit**, pas un pinceau : elles restent en `dialogue` avec
un `max_size` de 56 à 80. Le style `cri` est réservé au vrai pinceau épais.

**Anime Ace 2.0 BB** (Blambot) : gratuite pour un usage **personnel et non
commercial uniquement**, ne pas redistribuer (voir
`fonts/LICENSE-AnimeAce2-Blambot.txt`). Téléchargée depuis FontSpace
(`fontspace.com/get/family/pwjm`, avec l'en-tête Referer de la page de la
police ; dafont et Font Squirrel bloquent les téléchargements sans navigateur).
Elle n'a ni `Ç` ni `Œ` ni espace insécable : les fichiers `*-FR.ttf` sont des
copies complétées par `scripts/add_french_glyphs.py` (`Ç` = C + virgule, `Œ` =
O + E accolés). La première version « Anime Ace » (2001) n'a aucun accent :
ne pas l'utiliser.

Les autres polices sont libres (licence OFL), depuis `github.com/google/fonts`.
**Wild Words** (Comicraft) est payante : pas de version gratuite légale.

Un même style garde la même police sur tous les chapitres.

### Texte posé sur le dessin (sans bulle)

Pour un titre ou un nom de compétence écrit directement sur l'image, utiliser
`"box": [x0, y0, x1, y1]` au lieu de `"point"`. Le script efface les lettres
par inpainting (reconstruction du fond) puis redessine le texte français avec
le même dégradé de couleur, à la place des lettres d'origine.

| Champ | Rôle |
| --- | --- |
| `stretch` | Étirement vertical maximal (titres hauts et étroits : 1.5 à 4) |
| `target` | Zone exacte du nouveau texte, si celle détectée est faussée par le décor |
| `ink_red_max` | Lettres bleues sur fond bleu clair : seuil du canal rouge (ex. 120) |
| `grow` | Marge d'effacement autour des lettres (défaut 4, 9 pour un halo) |
| `outline` / `outline_width` | Liseré clair autour des lettres, comme l'original |
| `ink_max` | Seuil de l'encre (défaut 215 ; 120 pour ne prendre que le noir) |
| `solid` | Lettres blanches cernées de noir : bouche l'intérieur des lettres avant l'effacement (7 pour les titres de combat) |
| `fill` | Couleur de remplissage `[r, g, b]` à la place de l'inpainting (texte sur le blanc d'une bulle) |
| `angle` | Inclinaison du texte en degrés, sens antihoraire |
| `line` / `line_width` | Points `[x, y]` d'un contour de bulle à retracer en noir (texte qui chevauche le contour) |
| `style` | Tout style du tableau des polices (`systeme` par défaut, `cartouche`, `dialogue`...) |
| `light_min` | Seuil de clarté des lettres pour `light` (défaut 190) et `unsat` (défaut 170) |
| `unsat` | Lettres blanches sur dessin coloré : saturation maximale des pixels de lettre |
| `blur_fill` | Très grosses lettres sur fond lumineux : remplissage flou à bords fondus (ex. 25) au lieu de l'inpainting, qui fait des pavés |
| `colors` | Dégradé du nouveau texte `[[r, g, b] haut, [r, g, b] bas]` ; sans lui, couleurs relevées sur les lettres d'origine |
| `light` | Lettres claires sur fond sombre (seuil `light_min`) |
| `light_any` | Lettres claires mais colorées (légendes en dégradé) : seuil sur le canal le plus clair (ex. 200) |
| `outlined` | Lettres blanches cernées de sombre sur un fond clair (ciel) : blanc collé à un trait sombre, rayon en px (2 à 9) |
| `outlined_fill` | Avec `outlined` : lettres noires épaisses cernées de blanc sur un dessin sombre (ch. 231 p. 2). Prend toute la tache noire bordée de blanc, sauf celles qui touchent le bord de `box` (traits du dessin). Réglage type : `"outlined": 4, "outlined_fill": true, "ink_max": 90, "light_min": 200, "grow": 3` |
| `thick` | Onomatopées géantes au pinceau : ne garde que les traits plus épais que 2 × N px (efface les hachures) |
| `max_letter` | Ne garde que les taches d'encre de hauteur ≤ N px (exclut contours et décor ; ~50 pour une bulle coupée) |
| `vfill` | Fond à rayures verticales : recomposé colonne par colonne |
| `cv_inpaint` | Ancien inpainting `cv2.inpaint` au lieu de LaMa (repli, si LaMa invente un motif gênant) |

**Effacement par défaut (depuis le 9 octobre) : LaMa.** Sans `fill`, `vfill`, `blur_fill` ni
`cv_inpaint`, le mode `box` efface avec le modèle LaMa (`models/lama_fp32.onnx`,
[Carve/LaMa-ONNX](https://huggingface.co/Carve/LaMa-ONNX), lu par OpenCV, ~4 s par zone) : il
prolonge hachures, dégradés et traits là où `cv2.inpaint` laissait un pavé flou (ch. 227 p. 28,
228 p. 17, 28, 33). Texte translucide impossible à isoler (226 p. 11) : `"ink_max": 256, "grow": 0`
efface toute la boîte et LaMa reconstruit le fond.
| `line_spacing` | Interligne (défaut 0,95) |

**Toujours chercher ces textes sans bulle** à l'inventaire d'une page : ils ne
sont pas détectés automatiquement (erreur commise sur la page 006 du chapitre
259 : `FIGHT WITH ME!`, `DIVINE ENERGY RELEASE` et `GUARDIAN FORM` avaient été
oubliés).

## Catégories de texte

### Dialogues

- Conserver le tutoiement ou le vouvoiement selon la relation entre les
  personnages.
- Préserver le registre : familier, solennel, provocateur ou méprisant.
- Traduire naturellement plutôt que mot à mot.
- Garder les phrases courtes et énergiques lorsqu’elles correspondent au rythme
  de la scène.
- Les interjections doivent rester brèves : `HEIN ?`, `EUH ?`, selon le contexte.
- Suivre la table des personnages (tutoiement ou vouvoiement entre chaque
  paire) et la compléter dès qu'une nouvelle relation apparaît.

### Narration et pensées

- Garder les textes narratifs courts et lisibles.
- Distinguer les pensées ou apartés des dialogues avec le style `pensee`.
- Conserver les phrases volontairement incomplètes lorsque les points de
  suspension annoncent la suite.

### Interface et panneaux

- Conserver les MAJUSCULES et les accents français :
  `ARÈNE CÉLESTE TERRARIUM`.
- Utiliser les ordinaux français : `99E ÉTAGE`.
- Utiliser le style `systeme` pour les fenêtres et messages d'interface.
- Employer exactement le même terme pour un lieu, une arène, une compétence ou
  un titre lorsqu’il réapparaît.
- Adapter les noms de lieux et d’interface pour obtenir un français naturel,
  sans traduction mécanique.
- Centrer le texte et conserver l’espacement propre aux panneaux, différent
  d’une bulle ronde.

### Effets sonores et action

- Conserver les effets sonores stylisés lorsqu’ils font partie du dessin.
- Ne pas confondre une onomatopée avec une réplique.
- Ne pas remplacer une onomatopée étrangère sans équivalent français naturel.
- Les textes d’action et les cris utilisent le style `cri`.
- Les slogans et encouragements sont **traduits** en gardant leur rythme oral
  et leurs ellipses : `LET’S GO` → `ON Y VA !`, `LET’S WIN...` →
  `ON VA GAGNER...`. Seul un slogan dessiné dans l'illustration reste tel quel.

## Glossaire

Termes gardés en anglais (choix de l'utilisateur, 4 octobre) : **UNNAME, PLAYER(S), RANKER, UNRANKER**. Tous les autres termes de la série se traduisent (Ego Weapon → ARME D’EGO, Core, Contract, Vessel, Curtain, titres, noms de techniques) : voir le tableau. Un nouveau terme de jeu douteux : demander à l'utilisateur.

| Source | Français retenu | Règle |
| --- | --- | --- |
| Master Swordsman | MAÎTRE ÉPÉISTE | Titre ; guillemets seulement si présents dans la source |
| Contract | CONTRAT | Conserver les guillemets si le terme est cité |
| Mirage | MIRAGE | Nom propre ou titre selon le contexte |
| Do you want to change the past? | TU VEUX CHANGER LE PASSÉ ? | Tutoiement retenu |
| How disgraceful | QUELLE HONTE ! | Ton réprobateur naturel |
| That's intense! | C’EST INTENSE ! | Garder l’énergie de la réplique |
| Come back safely... | REVIENS SAIN ET SAUF... | Formule affective avec ellipse |
| HEO SEOL-JIN | SEOL-JIN HEO | Nom complet du personnage ; ne pas interpréter `HEO` comme une interjection |
| Let's fight to the end. | BATTONS-NOUS JUSQU’AU BOUT. | Chapitre 259 |
| Seriously | SÉRIEUX / FRANCHEMENT | `SÉRIEUX` en exclamation, `FRANCHEMENT` en début de phrase |
| KIM TAE-WON | TAE-WON KIM | Prénom puis nom, comme SEOL-JIN HEO (ch. 225) |
| Divine Realm | DOMAINE DIVIN | Entre guillemets quand la source les met |
| Ego Weapon | ARME D’EGO | Toujours avec « D’ » (consigne de l’utilisateur, 4 octobre) : `UNE ARME D’EGO`, `MAÎTRE D’ARME D’EGO` ; `EGO` sans accent ; fiches « ??? EGO WEAPON IN THE FORM OF... » → `ARME D’EGO EN FORME DE...` |
| Absolute God | DIEU ABSOLU | Arthur |
| God Candidate | CANDIDAT DIVIN | |
| Final Battle / First Round | BATAILLE FINALE / PREMIER ROUND | Titres d'écran, style `systeme` |
| Mother of Flames | MÈRE DES FLAMMES | Esprit-renard, mère du clan du feu |
| Reconstruction | RECONSTRUCTION | Pouvoir d'Arthur |
| Vessel | RÉCEPTACLE | Corps hôte, avec guillemets |
| Grey zone | ZONE GRISE | |
| Who cares? | ET ALORS ? | |
| Unnamed / Unname | UNNAME | **Ne pas traduire** (consigne du 4 octobre). Nom propre sans article : `D’UNNAME`, `UNNAME FUT...`. « Nameless » descriptif reste traduit : `L’ÊTRE SANS NOM`, `"SANS-NOM."` |
| Player / Players | PLAYER / PLAYERS | **Ne pas traduire**, même au sens courant : `LES PLAYERS`, `CONTRAT DE PLAYER`, `J’ARRIVE, "PLAYER" !` |
| Ranker / Unranker | RANKER / UNRANKER | **Ne pas traduire** (ch. 236 : `JE SUIS "UNRANKER".`) |
| Cartridge open | CARTOUCHE OUVERTE | Ch. 226-227 |
| Contract Review | LECTURE DU CONTRAT | Ch. 226 |
| Serpent of Eden | SERPENT D’ÉDEN | Ch. 226 |
| Contract of Absolute Fairness | CONTRAT D’ÉQUITÉ ABSOLUE | Ch. 227 |
| Witch of Western Lake | SORCIÈRE DU LAC DE L’OUEST | Ch. 227, Mirage la vouvoie |
| Soul Sword | L’ÉPÉE DE L’ÂME | Ch. 227 |
| ASARYUN | ASARYUN | Orthographe de l'image du ch. 227 |
| Explorer | EXPLORATEUR / EXPLORATRICE | Ch. 228 ; la Dame aux cheveux d'argent est une exploratrice |
| Lady of Serene Heights | DAME DES CIMES SEREINES | Ch. 228 |
| The Path to Utopia (Avalon) | LE CHEMIN VERS L’UTOPIE (AVALON) | Compétence, ch. 228 |
| Sword Release / Rending Sword | LIBÉRATION DE L’ÉPÉE / ÉPÉE DÉCHIRANTE | Techniques de Dean (V16), ch. 243-244 |
| Semifinal / Winner | DEMI-FINALE / VAINQUEUR | Écrans de tournoi, ch. 244 |
| Former Rank N - Class: X Contract | EX-RANG N - CLASSE : CONTRAT DE X | Ch. 226 : MAÎTRE DE L’ONDE (Wave Art Master), CORPS-À-CORPS (Infighter), DÉMONIDE (Demonkin), DANSEUR D’ÉPÉE |
| Threat Level | NIVEAU DE MENACE | Ch. 226 (validé) : CLAN DES GÉANTS, ROI DES FOURMIS, COLONIE DE HARPIES, HOMONCULE, CYCLOPE, CHEF DE LA TRIBU DES LOUPS CROC-DE-GIVRE, BÊTE À DÉFENSES DE GIGIN, SORCIÈRE DÉMONIAQUE, DÉMON DE L’ORACLE |
| 44th Red Gate / Hidden Stage | 44E PORTE ROUGE / NIVEAU CACHÉ | Ch. 226 |
| Lava Veil of Raspa Volcano, Keeper of the Eternal Flames | VOILE DE LAVE DU VOLCAN RASPA, GARDIEN DES FLAMMES ÉTERNELLES | Ch. 226 |
| Spatula / Axe / Whip / Hammer / Torch | SPATULE / HACHE / FOUET / MARTEAU / TORCHE | Armes d’ego d’Arthur (ch. 225, 235, 246). Jamais `SPATULA` |
| Bracer / Bracelet | BRASSARD (ch. 225) / BRACELET (ch. 235) | L’anglais varie ; à unifier si l’utilisateur le demande |
| Dragon Cloak / Dragon Suit | CAPE DU DRAGON (ch. 254) / ARMURE DU DRAGON (ch. 255) | L’anglais varie ; toujours provisoire |
| Ryujin / Wujin | RYUJIN | Deux personnages distincts : WUJIN est le chef de l’union des petites guildes (VF officielle) |
| Second Round | DEUXIÈME ROUND | Ch. 228 ; noms des combattants (DEAN, VAN ZICHMUND) et « VS » laissés tels quels |

## Personnages et registre

| Personnage A | Personnage B | Registre |
| --- | --- | --- |
| Seol-jin Heo | Arthur | Tutoiement |
| Arthur | Les candidats (en groupe) | Vouvoiement pluriel (`VOUS`) |
| Tae-won Kim | Mirage | Tutoiement (adversaires, ton méprisant) |
| Mère des Flammes | Lillet | Tutoiement (mère et fille) |
| Arme Ego (démone à corne) | Mirage | Tutoiement (menaces) |
| Lillet | Ses compagnons | Tutoiement |

Compléter cette table à chaque nouvelle relation.

## Règles de retouche des images

- Préserver les fichiers originaux dans `chapters_en/` ; ne jamais les modifier.
- Enregistrer les versions françaises dans `chapters_fr/chapter-N/` avec le
  **même nom de fichier** que l'original (pas de suffixe).
- Toujours repartir de l'image anglaise d'origine, jamais d'une version
  française déjà enregistrée, pour éviter de dégrader la qualité JPEG.
- La source de vérité est `translations/chN_fr.txt` : `build` en régénère les
  configs `inventaire/chN/config_PPP.json` (sauf ch. 225 et 259 : configs JSON écrites à la main,
  dans `translations/`).
- Reconstituer la zone intérieure de la bulle sans masquer son contour original.
- Adapter la taille du texte à la surface utile, sans remplir artificiellement
  une bulle qui doit rester aérée.
- Conserver l’espace vide lorsqu’une page contient peu de texte.

## Principes de retouche

Le déroulé d'un chapitre (inventaire OCR, txt, `build`, contrôle, viewer) est
dans `CLAUDE.md` ; les chapitres s'enchaînent sans validation page par page.
Le moteur applique ces principes, à vérifier sur les points signalés :

- **Bulle par bulle** : masque limité à l'intérieur de la bulle ; contour,
  queue, ombres et dessin intacts. Les bulles collées se séparent par un `cut`.
- **Fond reconstruit** avec la couleur et la texture autour des lettres, jamais
  un rectangle uniforme ; sur un fond non uniforme, mode `box` (inpainting,
  `blur_fill`, `vfill`).
- **Texte centré** sur le centre optique de la zone nettoyée, avec une marge
  visible avant le contour ; accents et ponctuation dans la zone utile.
- **Contrôle** : aucun reste de lettre, aucun halo ni différence de blanc,
  texte lisible sans être grossi artificiellement.

**Erreur à éviter :** dessiner un rectangle blanc de taille fixe autour d'une
coordonnée estimée. Cette méthode masque les contours, détruit la texture de
la page et décale facilement le texte hors du centre réel de la bulle.

## Outil : `translate_bubbles.py`

```
python scripts/translate_bubbles.py translations/ch259_*.json
```

Champs d'une bulle dans la config :

| Champ | Rôle |
| --- | --- |
| `point` | Point à l'intérieur de la bulle, près du texte |
| `text` | Texte français ; `\n` impose une coupure |
| `style` | `dialogue` (défaut), `italique`, `pensee`, `cri`, `chuchotement`, `systeme`, `titre` |
| `max_size` | Taille maximale imposée. Sans elle, la taille suit la hauteur des lettres anglaises mesurée dans la bulle (`lettering_size`) |
| `cut` | Ligne `[[x, y], ...]` qui sépare deux bulles collées ou referme un contour ouvert |
| `open` | Ligne qui détache un trait noir entrant dans la bulle (pour l'effacer) |
| `close` | Rayon (1 à 3) qui referme les petites brèches du contour |
| `color_bg` | `true` : traite les traits colorés comme du fond (seulement avec un `cut`) |
| `erase_color` | `true` : efface aussi le texte coloré (préservé par défaut pour ne pas abîmer le dessin) |
| `box` | Texte posé sur le dessin, à la place de `point` : voir « Texte posé sur le dessin » |

Styles : voir le tableau des polices (`cartouche` en plus de ceux listés ci-dessus).

Une bulle en `ÉCHEC` est laissée en anglais et signalée ; la page est quand
même enregistrée. Toujours relire le journal du script.

## Méthode de correction (relectures du 9-10 octobre, ch. 228-233)

Règle : un défaut qui revient se corrige **dans le moteur**, puis on refait le rendu de tous les
chapitres. Le réglage bulle par bulle dans le txt est réservé aux cas vraiment particuliers.
Sinon le même défaut reste partout ailleurs (constat de l'utilisateur au ch. 233).

**Repérage, sur tous les chapitres après chaque changement du moteur :**

1. `build N` : `ÉCHEC`, texte non retrouvé.
2. `python scripts/find_missed.py N` : texte anglais jamais traité (planche `oublis.png`).
3. `python scripts/audit_render.py N` : texte français nettement plus petit que l'anglais
   (planche `tailles.png`).

**Recettes, par défaut constaté :**

| Défaut | Correction |
| --- | --- |
| Texte trop petit dans une bulle | Le moteur coupe seul les lignes (taille proche de l'anglais). Si ça ne suffit pas : traduction plus courte (« CE RÉGIME... », « JE L’AI~ ») |
| Texte trop petit dans un cadre ou une légende (`box`) | Le moteur recoupe seul si les `\n` imposés rapetissent le texte ; sinon `target` sur toute la zone utile du cadre (pas seulement les lettres anglaises) et plus de lignes courtes |
| Texte décentré : bulle coupée par une onomatopée, une queue, le bord de page | `box` + `fill` limité aux lettres anglaises (`max_letter`), `target` centré sur la partie visible de la bulle |
| Contour de bulle rogné par un `fill` | Deux entrées : `(effacer)` en `fill` serré sur les lettres, puis le texte en `"ink_max": 0` + `target` (rien n'est effacé) |
| Bonhomme de neige (texte coupé, une bulle vide) | Corrigé dans le moteur le 10 octobre (recadrage élargi aux bulles voisines, ch. 236 p. 16) ; le journal signale `ÉCHEC : recouvre une bulle voisine`. Si ça reste : `point` dans chaque bulle + le même `cut` au cou, prolongé dans le trait noir |
| Logo, nom ou petite bulle effacés avec la bulle voisine | `box` limité aux lettres (`max_letter` sous la hauteur du logo) ; petites bulles posées sur un titre : laissées d'origine si identiques |
| Titre ou légende sur le dessin | `box` : LaMa par défaut ; lettres noires cernées de blanc → `outlined` + `outlined_fill` ; texte translucide → `"ink_max": 256, "grow": 0` |
| Texte gravé ou incliné sur le dessin (plaque « HOPE ») | `box` serré + `target` + `angle` mesuré sur l'original, style `systeme` (gras) |
| Scène de fin de chapitre répétée au début du suivant, anglais différent (234 p. 16 / 235 p. 12 « QUI DIABLE... ES-TU ? » ; 236 p. 27 / 237 p. 3) | Même texte français des deux côtés, celui du premier passage ; commentaire dans le txt |
| Bulle identique dans les deux langues (« LAY! », « DEAN. ») décentrée ou dessin voisin abîmé (237 p. 2) | Moteur (10 octobre) : texte identique à l'anglais lu par l'OCR, sans réglage JSON → l'original est gardé tel quel (49 bulles) |
| Halo coloré des lettres anglaises resté par-dessus le français (237 p. 9) | Moteur (10 octobre) : la couleur enfermée dans la bulle est du texte et s'efface ; seule la couleur qui touche le contour (onomatopée) est préservée. `erase_color` n'est plus nécessaire pour les lettres colorées |
| Bulle entière jamais traduite, lettrage au feutre condensé (238 p. 2, 6, 13 : « OY! TAKE IT! », « NO... », « HOW DARE YOU INSULT ME?! ») | L'OCR ne lit rien, pas même un bloc « non lu ». `find_missed.py` (10 octobre) signale maintenant les zones illisibles en forme de ligne de texte sur fond clair : `(illisible, bulle)`. Il ignore aussi les bulles gardées d'origine (texte identique). Ajouter une entrée id 100+ avec `point` |
| Accents des capitales collés à la ligne du dessus en mode `box` (« ÉTAIJ », 240 p. 11) | Moteur (10 octobre) : interligne agrandi quand une ligne après la première porte une capitale accentuée. Lettres noires cernées de blanc : recette `outlined` + `outlined_fill`, pas `ink_max` seul |
| `build` interrompu, pages de 0 octet (`BrokenProcessPool`, plusieurs rendus en parallèle) | Moteur (10 octobre) : les pages d'un processus tué sont refaites une à une. Éviter de lancer deux `build` en même temps |
| Onomatopées « CRACK » (247 p. 16, 19) et « HA... » (247 p. 21) | Gardées d'origine, ni effacées ni traduites (choix de l'utilisateur, 10 octobre) : entrées commentées dans le txt |
| Bulle coupée par un trait de case (248 p. 25 « VERY WELL THEN... ») : le `point` laisse la ligne du bas | Recette « contour rogné » : `(effacer)` en `box` avec `max_letter` au-dessus de la hauteur des lettres, puis texte en `"ink_max": 0` + `target` |
| Bulle coupée entre deux pages : une moitié deux fois plus grosse que l'autre (249 p. 1-2, 20-21 ; 250 p. 15-16) | Moteur (10 octobre) : en mode `box` avec `fill`, la taille est plafonnée par `max_size`, sinon par celle du style de bulle. Depuis le 10 octobre au soir, c'est automatique (`link_split_bubbles` dans `auto_translate.py`) : deux entrées `box` + `fill` qui touchent le bas d'une page et le haut de la suivante reçoivent la même colonne, le meilleur découpage de chaque moitié, la même taille (celle de la moitié la plus serrée) et un texte collé à la coupure (`seam`). Il suffit de mettre chaque moitié en `box` avec `fill` |
| Entrée `(effacer)` avec un id d'inventaire (< 100) : le mot « (EFFACER) » s'écrit dans la bulle (253 p. 11) | Toujours un id 100+ pour `(effacer)` ; l'entrée d'inventaire passe à `-` |
| Tiret long « — » : carré vide en mode `box` (254 p. 24) | Remplacer par « ... » |
| Grand titre blanc cerné de noir sur un dessin clair : fantômes des lettres anglaises (261 p. 28-29, 262 p. 5) | Une entrée `(effacer)` par ligne en `"ink_max": 256, "grow": 0` (LaMa reconstruit le rectangle), puis le titre en `"ink_max": 0` + `target` |
| « 100 % » coupé sur deux lignes (264 p. 21) | Moteur (10 octobre) : espace insécable avant « % » comme avant `? ! : ;` |
| « SEOL- / JIN » coupé au trait d'union (264 p. 18) | Moteur (10 octobre) : `NAMES_NO_BREAK` (SEOL-JIN, TAE-WON...) jamais coupés |
| Cédille du Ç posée sur la ligne suivante, accents collés après redécoupage (264 p. 20) | Moteur (10 octobre) : en mode `box`, l'interligne se calcule sur les lignes finales (accents, cédille) |
| Mot de l'univers traduit à un endroit | Le traduire partout, dessin compris (« PROJECT: HOPE » → `PROJET : ESPOIR`, ch. 230, 231, 232, 237) |

**Limite acceptée (décision de l'utilisateur, 10 octobre) :** Anime Ace est plus large que le
lettrage anglais ; un mot long seul (« DÉPLOIEMENT. ») ou une longue ligne reste plus petit que
l'anglais. Pas de lettres resserrées : `audit_render.py` sert à repérer les vrais défauts (bulle mal
détectée, traduction raccourcissable), pas à tout ramener à la taille anglaise.

**Moteur (10 octobre) :** les `\n` imposés sont abandonnés si un découpage automatique donne un
texte au moins 25 % plus grand (`REWRAP_GAIN`) ; en bulle, chaque pixel sous 80 % de la taille
anglaise compte double dans le choix du découpage (avant : 65 %).

## Erreurs rencontrées et solutions

### Chapitre 259

| Symptôme | Cause | Solution |
| --- | --- | --- |
| Rien d'effacé, texte « trop long » | Le point tombe dans le creux d'une lettre (O, A...) | Corrigé dans le script (zone minimale de 90 px) ; sinon déplacer `point` |
| `ÉCHEC : la bulle fuit vers le fond` | Contour ouvert : un trait, un éclair ou une onomatopée traverse le bord | Essayer d'abord `close: 1` ; si la brèche est large, tracer un `cut` **sur le vrai contour**, relevé pixel par pixel, pas sur un cercle estimé |
| Onomatopée coréenne colorée effacée ou coupée | Le nettoyage recouvrait les traits colorés | Corrigé : les pixels colorés sont toujours préservés et repassés par-dessus |
| Morceau d'ancien texte qui reste (ex. « UT ») | Une onomatopée colorée coupe le contour de la bulle | `cut` le long du contour + `color_bg: true` |
| Bulle minuscule au texte en 24 px | Un trait noir (queue d'une autre bulle) entre dans la bulle et la coupe | `open` le long de l'intérieur du contour |
| Deux bulles collées traitées comme une seule | Les contours se touchent | `cut` entre les deux, sur chacune des deux bulles |
| Texte qui touche des traits décoratifs | Taille maximale trop grande (cris en 80 px) | Baisser `max_size` et imposer les coupures avec `\n` |
| Mot isolé (`BOUT.`) ou `?` seul à la ligne | Coupure automatique | `\n` dans le texte ; l'espace insécable avant `? ! : ;` est automatique |
| `color_bg` activé partout | Ouvrait des brèches dans des bulles saines | Le laisser désactivé par défaut |
| Erreur de syntaxe après une modification du script | `\n` ou `\xff` écrits par un script Python intermédiaire | Modifier le script directement, puis relancer une page test |

### Ajouts du chapitre 225

| Symptôme | Cause | Solution |
| --- | --- | --- |
| Une bulle collée à une autre perd son texte (texte écrit puis effacé), sans « ÉCHEC » | Bulles en bonhomme de neige reliées par un col blanc : la seconde bulle recouvre la première | `cut` au col sur **les deux** bulles. Détection : comparer les masques de toutes les bulles d'une page (aucun pixel commun ne doit exister) |
| `cut` sans effet, la fuite continue | Coordonnées relevées dans un recadrage et pas reportées en coordonnées de page, ou `cut` qui s'arrête pile sur les pointes du col | Toujours convertir en coordonnées de page ; prolonger le `cut` d'une dizaine de pixels dans le trait noir des deux côtés |
| Queue de bulle large qui fuit | Le `cut` ne fermait qu'une moitié de la queue | Relever le contour colonne par colonne et tracer le `cut` sur toute la largeur de l'ouverture |
| Bulle oubliée à l'inventaire (`AH...`, p. 14) | Petite bulle collée à une grande, lue comme une seule | Relire la page française entière après le rendu : une bulle vide trahit l'oubli |
| Fantômes de lettres sous un titre blanc cerné de noir | L'encre détectée n'est que le cerne ; l'intérieur des lettres n'est pas effacé | `solid: 7` et un `box` plus large que les lettres, avec `target` pour la zone du texte |
| Contour de bulle effacé par une note manuscrite qui le chevauche | L'effacement du `box` prend aussi le contour | `fill` (blanc) + `line` : points du contour retrouvés en ajustant une ellipse sur le reste du contour (`cv2.fitEllipse`) |
| Page en `.webp` | Les chapitres 225 et suivants sont en WebP | Rien à faire : même nom, même extension ; le script enregistre en WebP qualité 95 |
| Faux « ÉCHEC » dans le journal | Le texte traduit contient le mot (`ÉCHEC ET MAT !`) | Chercher `ÉCHEC,` ou `ÉCHEC :` plutôt que `ÉCHEC` seul |

### Ajouts du 4 octobre (retours sur le ch. 239, ch. 244)

| Symptôme | Cause | Solution |
| --- | --- | --- |
| Texte français deux fois plus petit que l'anglais dans les grandes bulles | Plafond fixe de 48 px en dialogue ; les bulles non lues par l'OCR n'avaient aucune mesure | Corrigé : `lettering_size` mesure la hauteur des lettres d'origine (composantes connexes, 3e quartile) ; `auto_translate` ne fixe plus `max_size` |
| Petites bulles un peu trop grosses en français | Une mesure par lignes fusionnait deux lignes serrées | Mesure lettre par lettre, sans marge supplémentaire |
| `...` seuls minuscules | Anime Ace n'a que de petits points carrés | Corrigé : `draw_dots` dessine trois disques à la taille et à la place des points d'origine |
| Bulle du haut d'un bonhomme de neige vide, texte posé au col | L'OCR n'avait pas vu le `...` du haut : le masque couvrait les deux bulles | Ajouter la bulle manquante dans le txt (id 100+, réglage `{"point": [x, y]}`) : les deux points séparent les bulles |
| Texte trop bas dans une bulle coupée par le haut de la page | Seule la moitié visible de la bulle comptait pour le centrage | Corrigé : le texte est centré sur la hauteur du texte anglais (repli sur le centre de la bulle s'il y rapetisse de plus de 10 %). Depuis le 10 octobre (239 p. 19), une bulle qui touche le haut ou le bas de la page accepte jusqu'à 25 % de rapetissement (`INK_CENTRE_KEEP_EDGE`) avant ce repli |
| Reste d'une ligne anglaise sur la page voisine, bulle coupée par la page (239 p. 34-35 « HANDS. ») | `find_missed` la repère. Page du bas : `(effacer)` sur la ligne. Page du haut : si le texte français touche la zone, recette « contour rogné » (ids 100 et 101, effacement d'abord, puis texte en `"ink_max": 0`). Un `(effacer)` placé après le texte efface les lettres françaises |
| Page entière non traduite (ch. 239 p. 38, ch. 228 p. 16) | L'OCR ne lit rien sur de grosses légendes blanches sur fond coloré | Après `inv`, lister les pages sans aucune entrée traduite et les regarder |
| Pavés flous sous une grande légende effacée | Le texte français, plus étroit, ne recouvrait pas la zone effacée | `blur_fill`, `stretch` et des `\n` pour reprendre la forme du bloc anglais (même nombre de lignes) |
| Lettres-fantômes roses restées autour d'un titre | Seuil `light_min` trop haut, ou `max_letter` trop bas (lettre et fantôme ne forment qu'une tache) | Baisser `light_min` sans prendre le fond, monter `max_letter` |
| Pavé blanc derrière « WINNER » | `box` qui déborde sur le décor sombre : tout est pris pour de l'encre | Resserrer le `box` et baisser `max_letter` sous la hauteur du `box` ; une ligne sur fond sombre → `light` + `solid` dans un `box` séparé |
| « MOI... » au lieu de « JE... » | Fragment traduit sans regarder la bulle suivante (« JE ME SOUVIENS... ») | Traduire une phrase coupée en connaissant sa suite |
| Mots traduits à tort (INNOMMÉ, JOUEUR) | Termes de la série | Voir le glossaire : UNNAME et PLAYER ne se traduisent pas |
| Plantage `IndexError` dans `draw_text` (ch. 239) | Centrage sur le texte anglais : une ligne hors du recadrage passait le contrôle de place (ramenée au bord) | Corrigé dans `fits` : une ligne hors recadrage est refusée, le centre de la bulle est repris |

### Ajouts des ch. 245-249

| Symptôme | Cause | Solution |
| --- | --- | --- |
| Onomatopée géante au pinceau dans une bulle en dents de scie : `ÉCHEC`, fuite | Les lettres touchent le contour | Mode `box` avec `ink_max: 70` et `thick: 5` (ouverture morphologique : seuls les traits épais sont effacés, le contour fin reste), `fill` blanc |
| Lettres fantômes plus blanches que le fond après un `fill` | Fond à 253, remplissage à 255 | Relever la couleur du fond et la mettre dans `fill` (ex. `[253,253,253]`) |
| Bulle coupée entre deux pages | Chaque page ne voit qu'une moitié de bulle | Une moitié du texte par page, en mode `box` avec `max_letter` ~50 (le contour est exclu) et `fill` ; sinon les lignes coupées restent |
| Texte bleu foncé non effacé (ch. 245 p. 13) | Pixels colorés préservés par défaut | `erase_color: true` ; les cheveux colorés dans la bulle se nettoient avec un `(effacer)` en `box` |
| Texte français trop bas dans un `box` | L'emprise de l'encre inclut le décor | `target` sur les seules lettres d'origine, `box` resserré |
| Légende en dégradé orangé non détectée par `light` (ch. 252 p. 7) | `light` exige les trois canaux clairs | `light_any: 110` (canal le plus fort au-dessus du seuil) |
| Bonhomme de neige : le texte du haut glisse au col (ch. 253 p. 31) | Masque commun aux deux bulles | `cut` au col, prolongé dans le trait noir |
| Narration de la Mère des Flammes en cartouches rectangulaires (ch. 252-253) | Lettrage fin condensé | Style `cartouche` |
| Carré vide à la place de « — » (ch. 254 p. 24) | Le mode `box` n'a pas de police de repli | En `box`, remplacer « — » par « ... » |
| « DRAGON CLOAK » (ch. 254) | Surnom de Libur | `CAPE DU DRAGON` (choix provisoire, à confirmer) |
| « ELCALIBUR » (ch. 254, forme achevée de Libur) | `EXCALIBUR` (choix de l'utilisateur, 10 octobre) ; la note de la team de scan qui l'explique est effacée, pas traduite |
| « ARTHUR-NIM » (ch. 246, 256) | `ARTHUR` seul, sans le suffixe coréen (choix de l'utilisateur, 10 octobre) |
| « ROOKIE » (ch. 254 p. 6) | `LA "NOVICE"` (avant : `"BLEUE"`, refusé par l'utilisateur) |
| Lettres blanches cernées de sombre sur un ciel nuageux clair (ch. 257 p. 1) | `light` prend aussi les nuages | `outlined: 2` (blanc collé à un trait sombre), `ink_max: 130`, `light_min: 200`, `max_letter: 70` |
| Pavés noirs sous un grand titre effacé avec `blur_fill` | Zone effacée plus large que le flou | Monter `blur_fill` (40) |
| Grand titre blanc cerné de noir sur un décor chargé : restes de lettres autour du texte français (ch. 261 p. 28-29) | Le français, plus court, ne recouvre pas l’original | `outlined: 9` + `target` sur l’emprise des lettres d’origine + `stretch: 3` (même nombre de lignes) |
| « TRANSMOGRIFICATION » (ch. 261) | Changement de forme des armes d’ego | `MÉTAMORPHOSE` |
| Texte « (effacer) » dessiné tel quel dans la bulle (ch. 264 p. 19) | `(effacer)` ne marche que sur un id ajouté (100+), pas sur un id de l’inventaire | Mettre l’id d’inventaire à `-` et créer un id 100+ pour l’effacement |
| `
` transformé en vrai retour à la ligne (ch. 258) | Remplacement via un script Python | Rappel : écrire les `
` avec Edit uniquement |
| « WORLD BALANCER » (ch. 257) | Trésor qui fait circuler le karma | `RÉGULATEUR DU MONDE` |
| « SPEAR OF THE END » / « HIDDEN PHASE UNLOCKED » (ch. 257) | Technique de Lucia / écran système | `LANCE DE LA FIN` / `PHASE CACHÉE DÉBLOQUÉE` |
| « SWORD OF RUPTURE » (Vortex Scans, ch. 249) | Autre traduction de la technique de Dean | `ÉPÉE DÉCHIRANTE`, comme au ch. 244 |

**Méthode de diagnostic d'une fuite :** afficher le masque noir et blanc
autour de la bulle et chercher le chemin du remplissage jusqu'au bord de
l'image. Corriger le point précis de sortie, pas toute la bulle.

### Ajouts du 4 octobre (retours sur le ch. 231)

| Problème | Cause | Solution |
| --- | --- | --- |
| Bulle grise translucide : anglais à moitié effacé, français minuscule par-dessus (231 p. 4, 241 p. 1) | Fond sous le seuil de blanc (200) : le masque ne prend qu'un morceau de la bulle, sans ÉCHEC | Mode `box` avec inpainting : `"ink_max": 90, "max_letter": 90, "grow": 7`, `outline` blanc si les lettres anglaises en ont un ; `\n` pour couper les lignes |
| Texte `box` coupé en haut ou en bas, accents perdus | `target` qui dépasse `box` : le rendu est découpé à `box` | Toujours `target` à l'intérieur de `box` |
| Logo dans une case (« DEAN », 231 p. 13) effacé | Le mode `point` vide toute la case | `box` + `fill` limité au texte anglais |
| Fantôme rectangulaire des lettres anglaises après `fill` | Blanc du fond à 253, rempli en 255 | Corrigé dans le moteur : `fill` prend la couleur relevée autour des lettres si elle en est proche |
| « PAS POSSIBLE !!! » sur une ligne en 29 px pour un « NO WAY!!! » de 66 px | Le score préférait une ligne à un mot court isolé | Corrigé dans `score` : sous 65 % de la taille anglaise, chaque pixel perdu compte double |
| Pinceau rendu en `dialogue` (243 p. 15) | Style mal choisi | `cri` |
| Bonhomme de neige : une bulle vidée ou texte posé dans le cou (231 p. 1, 229, 233, 234, 236, 240, 260) | Une seule bulle repérée par l'OCR, son masque couvre les deux | Une entrée par bulle (id 100+ avec `point` pour celle ratée) et le même `cut` horizontal au point le plus étroit du cou sur les deux. Le mode `box` marche aussi mais donne un texte bien plus petit |
| Bulle entière restée en anglais, sans alerte (228 p. 28, 232 p. 6, 233 p. 7, 241 p. 8) | L'OCR de l'inventaire l'avait ratée | Le contrôle signale maintenant `texte non traité` : texte lu sur la page française loin de toute entrée |
| Légende noire cernée de blanc sur fond rouge (228 p. 28) | `light` ne prend que le blanc, l'inpainting bave du noir | `ink_max: 200`, `grow: 8` ; depuis LaMa, plus de `fill` (il laissait un rectangle uni sur le dégradé) |
| Bulle en `box` + `fill` au texte minuscule (229 p. 4, 9) | Lignes françaises plus longues que la boîte de l'anglais | Plus de lignes courtes (`\n`), `target` sur l'intérieur de la bulle et `max_letter` (~45) pour ne pas effacer le contour ; ou `point` + `close: 3` |
| Bulle coupée entre deux pages, texte rogné en bas (229 p. 11-12) | Deux lignes dans une demi-bulle | Une seule ligne par moitié (`C’EST TOUT` / `TOI !`) |
| `build` figé sans fin, processus à 0 % de CPU (ch. 230, 240) | `multiprocessing.Pool` qui reste bloqué sous Windows (12 processus LaMa) | Corrigé : `ProcessPoolExecutor`, 4 processus pour le rendu, 12 pour le contrôle. Si ça recommence : tuer les `python`, rendre les pages une par une pour trouver la fautive |
| `RuntimeError: Set changed size during iteration` dans `floodfill` (ch. 264) | Erreur interne ponctuelle de PIL | Relancer le chapitre |
| Petites bulles posées sur un grand titre (230 p. 15, « HE- », « HEHE ») vidées ou effacées | En `point`, le contour blanc des lettres du titre relie les bulles : le remplissage de l'une écrase l'autre | Titre effacé par rectangles qui évitent les bulles (`"ink_max": 256` + `(effacer)`), texte posé avec `"ink_max": 0` + `target`, puis bulles en `box` + `fill` avec `max_letter` à la hauteur des lettres |

## Chemin rapide : `auto_translate.py` (depuis le ch. 226)

```
python scripts/auto_translate.py inv 226     # OCR -> translations/ch226_fr.txt (anglais en commentaire)
# remplir la 3e colonne : PAGE.ID | style [json] | TEXTE   ('-' = ignorer, \n = coupure)
python scripts/auto_translate.py build 226   # configs JSON + rendu + contrôle OCR de la page française
python scripts/auto_translate.py build 226 009 010   # seulement certaines pages
python scripts/auto_translate.py check 226   # contrôle seul
```

- Le contrôle relit chaque page française par OCR et ne signale que les bulles où le texte
  français n'est pas retrouvé (bulle vidée par une voisine) et l'anglais resté visible ; seuls ces
  points sont recadrés dans `inventaire/chN/controle_PPP.png`. « lu : '' » sur un texte court en
  gros caractères est souvent un faux positif.
- Après `inv`, lister les pages sans aucune ligne traduite et les regarder : l'OCR peut rater une page entière.
- Ne regarder les images que pour : les blocs « non lu par l'OCR » ou illisibles, le choix
  italique/cri, les points signalés, et les titres en mode `box` (l'OCR ne juge pas leur rendu).
- Réglages JSON utiles en mode `box` : `light` (lettres claires), `max_letter` (ne garde que les
  taches de hauteur ≤ N px), `vfill` (fond à rayures verticales : recomposé colonne par colonne).
- Fiches de contrat (lettres blanches cernées sur bande magenta rayée, ch. 226) :
  `{"box": ..., "vfill": true, "light": true, "grow": 6, "colors": [[255,255,255],[255,255,255]],
  "outline": [0,0,0], "outline_width": 3}` ; garder le `box` dans la bande, sinon un pavé rayé
  apparaît sur le dessin blanc.

## Relecture : `viewer.html`

Après chaque rendu : `python scripts/make_viewer.py`, puis ouvrir `viewer.html`
(double-clic). Le chapitre anglais s'affiche à gauche, le français à droite ;
les deux colonnes défilent ensemble.

Un rendu sans `ÉCHEC` peut quand même déborder ou laisser un reste de texte :
vérifier en petites planches les points signalés par le contrôle, les `box` et
les bulles ajoutées à la main (pas chaque bulle, trop coûteux). L'utilisateur
relit ensuite dans le viewer et signale le reste par capture d'écran.

## Vérification d'un chapitre

1. Le sens et le ton sont-ils naturels en français ?
2. Le registre correspond-il au personnage et à la scène ?
3. Les noms propres, titres et termes récurrents sont-ils cohérents ?
4. Les guillemets entourent-ils uniquement le terme concerné ?
5. Les majuscules, accents, apostrophes `’`, ellipses et espaces insécables
   sont-ils corrects ?
6. Le style de police correspond-il au type de texte (dialogue, pensée, cri,
   système) ?
7. Le texte est-il lisible, centré et adapté à la bulle ou au panneau ?
8. Le contour, la queue et le fond de chaque bulle ont-ils été préservés ?
9. Les pages sans aucune entrée traduite ont-elles été regardées (texte raté par l'OCR) ?

La version officielle Webtoon étant protégée par le droit d’auteur, les
comparaisons restent limitées à de courts extraits et à des observations de
style.

### Version française officielle (audit du 9 octobre)

webtoons.com/fr, « Player » (title_no=2985), est marquée **Terminé à l’Ep. 224**
(juillet 2025). Notre ch. 225 enchaîne juste après : aucun chapitre en commun.
Il n’existe pas de version anglaise officielle (originaux : Vortex Scans).

Termes relevés dans les Ep. 150-224 officiels, comparés à nos choix :

| VF officielle | Nous | Décision |
| --- | --- | --- |
| PLAYER(S), RANKER, ARÈNE CÉLESTE, RÉCEPTACLE, ÉPÉISTE, MOGLAY | identique | — |
| KIM TAEWON, HEO SEOLJIN (nom d’abord, sans trait d’union) | TAE-WON KIM, SEOL-JIN HEO | On garde nos choix (glossaire) |
| ARME D’ÉGO (accent) | ARME D’EGO | On garde nos choix (glossaire) |
| MÈRE DU FEU | MÈRE DES FLAMMES | On garde nos choix (glossaire) |

### Ajouts de l’audit du 9 octobre

Relecture complète EN↔FR des 40 chapitres. Corrigé et re-rendu :

| Page | Erreur | Correction |
| --- | --- | --- |
| 226 p. 5 | « RENTRÉ LEUR RÔLE », « unused » perdu | `LES CONTRATS "INUTILISÉS" QUI AVAIENT REMPLI LEUR RÔLE` |
| 226 p. 14 | `IN... NOMMÉ` (UNNAME traduit) | `UN... NAME... !` |
| 232 p. 8 | `SI JE ARRÊTE` | `SI J’ARRÊTE` |
| 240 p. 13 | Titre `ARME EGO` | `ARME D’EGO` |
| 243 p. 15 | `ÉPÉE FENDEUSE` | `ÉPÉE DÉCHIRANTE` |
| 246 p. 12 | `SPATULA` laissé en anglais | `SPATULE` |
| 254 p. 32 | Phrase incomplète (`EN ÉTAIENT EXACTEMENT`) | `EN ÉTAIENT L’EXEMPLE MÊME` |
| 260 p. 28 | `QUE TU AS EU` | `QUE TU AS EUE` (accord avec « moitié ») |
| 264 p. 14 | Note manuscrite « Out of nowhere... » oubliée | `TOUT À COUP...` en `box` |
| 225 p. 11 | `"MIRACLE"` : coquille du scan anglais pour le nom MIRAGE (signalé par l’utilisateur) | `CE TYPE, C’EST "MIRAGE"... ?` ; le « TRULY A MIRACLE » de la p. 12 reste une expression |

Leçons : l’OCR de l’inventaire déforme l’anglais (ex. `VOICE`, `WUJIN`, `5070`) ;
avant de juger une traduction sur l’OCR, regarder la bulle. Les petites notes
manuscrites en minuscules passent facilement pour du décor. Le scan anglais
lui-même contient des coquilles (`MIRACLE` pour MIRAGE, `VOICE` pour CHOICE) :
un nom propre entre guillemets qui ne colle pas au personnage est à rapprocher
des noms connus plutôt qu’à traduire tel quel.

229 p. 4-5 : « FOR THE SAKE... OF THE VOICE YOU’VE MADE! » (coquille du scan pour
CHOICE) → `AU NOM...` / `DU CHOIX QUE TU AS FAIT !` (validé par l’utilisateur).

Mineurs corrigés ensuite : 226 p. 2 `SE SONT MIS` → `SE MIRENT` (récit au passé
simple) ; 238 p. 7 `CUISTOTE` → `LA CUISINIÈRE MAUDITE` ; 241 p. 6 pancarte « ON DUTY »
→ `DE GARDE` en `box` (`light`, `light_min: 180`, style `cartouche` pour le trait fin
à la craie : `systeme` était trop gras).
