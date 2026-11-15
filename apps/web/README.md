# Interface web DarijaLens

Interface React (Vite + TypeScript) de l'API DarijaLens : sentiment, langage offensant, mots qui ont pesé dans la décision, traduction.

## Lancer en local

1. Démarrer l'API (depuis la racine du dépôt) :

   ```
   $env:PYTHONPATH = "packages\nlp"
   uvicorn app.main:app --app-dir apps\api --reload
   ```

2. Démarrer l'interface :

   ```
   cd apps\web
   npm install
   npm run dev
   ```

3. Ouvrir http://localhost:5173

L'adresse de l'API se règle avec `VITE_API_URL` (voir `.env.example`). L'API n'accepte que les adresses listées dans son réglage `CORS_ORIGINS` (par défaut `http://localhost:5173`).

## Commandes

| Commande | Rôle |
|---|---|
| `npm run dev` | serveur de développement |
| `npm test` | tests de la logique (surlignage des mots) |
| `npm run build` | vérification des types et construction dans `dist/` |
