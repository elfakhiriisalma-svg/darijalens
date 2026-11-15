# Fine-tuning de DarijaBERT pour le sentiment (corpus MYC)

Résultats copiés depuis le notebook Kaggle (GPU Tesla T4) le 2026-11-13, avec `ml/finetune_darijabert.py`.
Mêmes données, même découpage (graine 42) et même nettoyage que le modèle simple (`train_sentiment.py`).
Mesure principale : **test sans emojis** (le corpus MYC a un biais d'emojis, voir `emoji_bias`).

Réglages : 3 epochs, taux d'apprentissage 2e-5, batch 32, longueur max 128, fp16,
meilleur checkpoint choisi sur le F1 macro de validation (sans emojis).

| Écriture | Exemples de test | Modèle simple (TF-IDF) | DarijaBERT | Gain |
|---|---|---|---|---|
| Arabe (modèle `SI2M-Lab/DarijaBERT`) | 1731 | 0,845 | **0,863** | +0,018 |
| Arabizi (modèle `SI2M-Lab/DarijaBERT-arabizi`) | 662 | 0,719 | **0,811** | +0,092 |
| Mixte (modèle arabe) | 64 | 0,614 | 0,671 | +0,057 (échantillon trop petit) |

Validation (F1 macro par epoch) :
- arabe : 0,856 / 0,860 / 0,855
- arabizi : 0,794 / 0,812 / 0,805

## Limites
- La perte de validation augmente après l'epoch 1 : surapprentissage léger. Le F1 reste stable.
- Les fichiers de métriques JSON et le modèle arabe ont été effacés par un redémarrage de Kaggle :
  les chiffres arabes ci-dessus viennent de la sortie du notebook, pas d'un fichier.
- Le corpus MYC reste un corpus de commentaires à 2 classes. L'évaluation finale doit se faire
  sur notre propre corpus annoté.

## Essai : ajouter des phrases de négation à l'entraînement

Problème observé : `ماشي مزيان هاد الشي` (« ce n'est pas bien ») et `ما كاينش مشكل، كلشي مزيان`
(« pas de problème, tout est bien ») sont mal classées. Le modèle simple rate aussi `ماعجبنيش`.

Données : `ml/data/negation_phrases.csv`, 69 phrases écrites à la main pour l'expérience
(négations positives et négatives, plus des phrases sans négation), relues et validées par Salma.
Une ligne sur quatre (18 phrases) est gardée de côté et ne sert jamais à l'entraînement.

| Modèle (DarijaBERT arabe) | Négation jamais vue (18 phrases) | F1 macro arabe, test sans emojis |
|---|---|---|
| Sans phrases de négation | 9/18 = 0,50 | 0,859 |
| + 51 phrases répétées 3 fois | 10/18 = 0,56 | 0,867 |
| + 51 phrases répétées 15 fois | 7/18 = 0,39 | 0,870 |

Conclusion : **cette approche ne règle pas le problème.** Avec 18 phrases, une phrase pèse 5,6 points,
donc ces écarts sont du bruit. Le F1 arabe varie de 0,859 à 0,870 d'une exécution à l'autre,
ce qui donne l'ordre de grandeur de la variabilité du fine-tuning sur GPU.
Prochaine piste : de vrais commentaires avec négation dans notre propre corpus annoté.
Mesure de repli en place : l'API répond `uncertain` quand le score est entre 0,40 et 0,60.

## Test complémentaire de la négation (12 phrases nouvelles, DarijaBERT sans entraînement de négation)

11 phrases sur 12 correctes. Les négations avec verbe (`ما عجبنيش`, `ما كيستاهلش`, `ما جاوبونيش`)
sont bien classées. L'erreur restante est `ماشي خايبة هاد الخدمة` (« ce service n'est pas mauvais »,
score 0,49) : la faiblesse se concentre sur **`ماشي` + adjectif** (voir aussi `ماشي مزيان`, `ماشي زوين`).
Les phrases à 0,54 et 0,49 tombent dans la zone `uncertain` (0,40 à 0,60).
Limite : 12 phrases écrites par l'équipe de développement, donc un signe encourageant et non une preuve.
