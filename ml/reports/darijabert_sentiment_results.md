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
