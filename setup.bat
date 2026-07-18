@echo off
REM Installation et lancement automatiques (Windows)

echo == 1/5 Creation de l'environnement virtuel ==
python -m venv venv
call venv\Scripts\activate.bat

echo == 2/5 Installation des dependances ==
pip install --upgrade pip
pip install -r requirements.txt

echo == 3/5 Application des migrations ==
python manage.py migrate

echo == 4/5 Creation des comptes de demonstration ==
python manage.py seed_demo

echo == 5/5 Lancement du serveur ==
echo.
echo Application disponible sur : http://127.0.0.1:8000/
echo Admin Django              : http://127.0.0.1:8000/admin/  (admin / admin1234)
echo Compte de demo            : demo / demo12345
echo.
python manage.py runserver
