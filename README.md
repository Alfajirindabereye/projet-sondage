# Scrutin — Système de sondage (Django)

Application web permettant de créer des sondages personnalisés, de les
diffuser via un lien unique, de collecter les réponses (avec logique
conditionnelle) et de visualiser les résultats sous forme de statistiques
(tableaux + graphiques Chart.js), avec export CSV.

## Stack technique

- **Backend** : Django 6 (Python)
- **Base de données** : SQLite (fichier local, créé automatiquement)
- **Frontend** : HTML/CSS "maison" (design personnalisé, sans framework CSS externe) + JavaScript vanilla pour le constructeur de sondage dynamique et l'affichage conditionnel
- **Visualisation** : Chart.js (chargé depuis un CDN)
- **Authentification** : système d'auth Django, renforcé (connexion par identifiant ou e-mail, verrouillage anti force-brute, indicateur de force du mot de passe, "se souvenir de moi")

---

## 🚀 Démarrage rapide (ouvrir le projet dans VS Code)

### Prérequis
- **Python 3.10 ou plus récent** installé sur votre machine (vérifiez avec `python3 --version` ou `python --version`)
- **VS Code** avec l'extension **Python** (Microsoft) installée

### Étape 1 — Ouvrir le dossier dans VS Code
Décompressez l'archive, puis dans VS Code : `Fichier` → `Ouvrir un dossier...` → sélectionnez le dossier `sondage`.

### Étape 2 — Lancer l'installation automatique

Ouvrez un terminal dans VS Code (`Terminal` → `Nouveau terminal`), puis :

**Sur macOS / Linux :**
```bash
bash setup.sh
```

**Sur Windows (invite de commandes ou PowerShell) :**
```bat
setup.bat
```

Ce script fait tout automatiquement :
1. Crée un environnement virtuel Python (`venv`)
2. Installe Django et les dépendances
3. Crée la base de données SQLite (migrations)
4. Crée un compte administrateur et un compte de démonstration avec un sondage d'exemple
5. Démarre le serveur

### Étape 3 — Ouvrir l'application dans le navigateur

Une fois le terminal affichant :
```
Starting development server at http://127.0.0.1:8000/
```

Ouvrez votre navigateur à l'adresse : **http://127.0.0.1:8000/**

### Comptes disponibles immédiatement

| Rôle | Identifiant | Mot de passe | Accès |
|---|---|---|---|
| Compte de démo (avec un sondage déjà créé) | `demo` | `demo12345` | http://127.0.0.1:8000/ |
| Administrateur Django | `admin` | `admin1234` | http://127.0.0.1:8000/admin/ |

Pour arrêter le serveur : `Ctrl + C` dans le terminal.

Pour le relancer plus tard (sans tout réinstaller) :
```bash
source venv/bin/activate   # Windows : venv\Scripts\activate
python manage.py runserver
```

---

## Installation manuelle (si vous préférez ne pas utiliser setup.sh/setup.bat)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo          # crée admin/demo (optionnel)
# ou : python manage.py createsuperuser   # pour créer votre propre compte admin

python manage.py runserver
```

Puis ouvrez http://127.0.0.1:8000/

## Lancer les tests automatisés

```bash
python manage.py test
```
12 tests couvrent : inscription, connexion (identifiant/e-mail), verrouillage anti force-brute, création de sondage avec logique conditionnelle, remplissage anonyme, validation des champs obligatoires, contrôle d'accès aux résultats, sondage clos/expiré.

## Déboguer dans VS Code

Une configuration de lancement est fournie (`.vscode/launch.json`) : appuyez sur **F5**, VS Code démarre le serveur Django en mode debug (points d'arrêt disponibles).

## Structure du projet

```
sondage/
├── config/          # réglages du projet Django (settings, urls)
├── accounts/        # inscription, connexion, backend d'authentification, tests
├── surveys/         # sondages, questions, réponses, résultats, export CSV, tests
│   └── management/commands/seed_demo.py   # crée admin + compte démo + sondage exemple
├── templates/        # template de base (navbar, footer)
├── static/           # CSS et JS (design + constructeur de sondage)
├── setup.sh / setup.bat   # installation + lancement en une commande
├── .vscode/           # configuration de débogage VS Code
└── manage.py
```

## Fonctionnalités couvertes

- Inscription / connexion (identifiant ou e-mail), verrouillage après 5 tentatives échouées, mot de passe avec règles de robustesse
- Création d'un sondage : choix unique, choix multiple, texte libre
- Questions conditionnelles ("Afficher Q5 seulement si réponse à Q3 = Oui")
- Génération automatique d'un lien de partage unique (UUID)
- Remplissage avec ou sans compte (paramétrable par sondage)
- Résultats : tableaux + graphiques (camembert / histogramme) + réponses libres
- Liste "Mes sondages" avec statut (actif / clos), clôture manuelle
- Expiration automatique à une date donnée
- Export des résultats en CSV (compatible Excel, accents inclus)
- Tests automatisés (12 tests, couverture des cas critiques)

## Notes de sécurité

- CSRF activé sur tous les formulaires
- Mots de passe hashés via le système Django standard (PBKDF2)
- Connexion protégée par verrouillage temporaire après tentatives répétées
- Seul le propriétaire d'un sondage peut le modifier, le clôturer, le supprimer, voir ses résultats ou exporter ses réponses

⚠️ **Avant une mise en production réelle** : changez `SECRET_KEY`, désactivez `DEBUG`, configurez `ALLOWED_HOSTS`, changez les mots de passe `admin`/`demo`, et utilisez un serveur WSGI de production (Gunicorn, etc.) derrière un serveur web (Nginx).
