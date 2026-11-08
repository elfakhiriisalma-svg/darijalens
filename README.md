# DarijaLens

Plateforme de compréhension, de normalisation et d'analyse de la darija écrite
(arabe, arabizi, code-switching) : détection de langue, sentiment, discours haineux,
traduction vers le français et l'anglais.

Projet de Traitement Automatique du Langage (TAL) réalisé par Salma Elfakhiri et Douae Zikki.

> **État** : étape 2 (structure du projet). L'API ne contient pour l'instant que des routes
> de surveillance. Les modules de TAL arrivent aux étapes suivantes.

## Structure

```
apps/api        API FastAPI (backend)
apps/web        Interface React (frontend, à venir)
packages/nlp    Bibliothèque de TAL, indépendante du web (à venir)
ml              Entraînement des modèles (Colab / Kaggle)
data            Données (non versionnées)
tests           Tests automatiques
docs            Documentation
```

## Prérequis

Git, Python 3.12, Node.js, Docker Desktop.

## Lancer le projet avec Docker

1. Copier la configuration :

   ```
   copy .env.example .env
   ```

2. Ouvrir `.env` et remplacer `change-me` par un mot de passe de votre choix.
3. Démarrer :

   ```
   docker compose up --build
   ```

4. Vérifier dans le navigateur :
   - http://localhost:8000/health : le serveur tourne ;
   - http://localhost:8000/ready : le serveur et la base de données répondent ;
   - http://localhost:8000/docs : documentation interactive de l'API.

5. Arrêter : `Ctrl+C`, puis `docker compose down`.

## Lancer les tests sans Docker

```
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r apps/api/requirements-dev.txt
ruff check .
pytest
```

## Licence

MIT.
