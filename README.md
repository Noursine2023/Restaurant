# NYC Restaurants — Interface Web Flask

Interface web pour explorer et gérer la base de données MongoDB des restaurants de New York.

## Lancement rapide

```bash
# 1. Installer les dépendances
pip install flask pymongo

# 2. S'assurer que le container MongoDB tourne
docker start mongo-resto

# 3. Lancer l'application
python app.py
```

Ouvrir ensuite : http://localhost:5000

## Fonctionnalités

- **Dashboard** — statistiques globales avec 3 graphiques (Chart.js)
  - Restaurants par borough (bar chart)
  - Top 8 cuisines (donut chart)
  - Score moyen d'inspection par borough (horizontal bar)

- **Liste des restaurants** — recherche full-text, filtres borough/cuisine, pagination

- **Détail** — fiche complète avec historique des inspections et score moyen

- **CRUD complet** — Ajouter, modifier, supprimer un restaurant

## Structure du projet

```
resto_app/
├── app.py              # Application Flask + routes
├── requirements.txt    # Dépendances
└── templates/
    ├── base.html       # Layout commun (nav, styles)
    ├── index.html      # Dashboard
    ├── restaurants.html # Liste + filtres
    ├── detail.html     # Fiche restaurant
    ├── add.html        # Formulaire ajout
    └── edit.html       # Formulaire modification
```

## Configuration

Par défaut, l'app se connecte à `mongodb://localhost:27017/` sur la base `restaurantDB`.
Pour modifier, éditer la ligne dans `app.py` :
```python
client = MongoClient("mongodb://localhost:27017/")
```
