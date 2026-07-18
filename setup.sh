#!/usr/bin/env bash
# Installation et lancement automatiques (Linux / macOS)
set -e

echo "== 1/5 Création de l'environnement virtuel =="
python3 -m venv venv
source venv/bin/activate

echo "== 2/5 Installation des dépendances =="
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "== 3/5 Application des migrations (création de la base de données) =="
python manage.py migrate

echo "== 4/5 Création des comptes de démonstration (admin / demo) =="
python manage.py seed_demo

echo "== 5/5 Lancement du serveur =="
echo ""
echo "Application disponible sur : http://127.0.0.1:8000/"
echo "Admin Django              : http://127.0.0.1:8000/admin/  (admin / admin1234)"
echo "Compte de démo            : demo / demo12345"
echo ""
python manage.py runserver
