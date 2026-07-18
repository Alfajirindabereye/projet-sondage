"""
Commande utilitaire : crée un compte administrateur et un compte de
démonstration avec un sondage d'exemple, pour tester rapidement l'application.

Usage :
    python manage.py seed_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from surveys.models import Choice, Question, Survey

User = get_user_model()


class Command(BaseCommand):
    help = "Crée un superutilisateur admin/admin1234 et un sondage de démonstration."

    def handle(self, *args, **options):
        # --- Superutilisateur pour /admin/ ---
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password="admin1234"
            )
            self.stdout.write(self.style.SUCCESS(
                "Superutilisateur créé -> identifiant: admin / mot de passe: admin1234"
            ))
        else:
            self.stdout.write("Le superutilisateur 'admin' existe déjà.")

        # --- Utilisateur de démo + sondage d'exemple ---
        demo_user, created = User.objects.get_or_create(
            username="demo", defaults={"email": "demo@example.com"}
        )
        if created:
            demo_user.set_password("demo12345")
            demo_user.save()
            self.stdout.write(self.style.SUCCESS(
                "Utilisateur de démo créé -> identifiant: demo / mot de passe: demo12345"
            ))

        if not Survey.objects.filter(owner=demo_user, title="Satisfaction client (démo)").exists():
            survey = Survey.objects.create(
                owner=demo_user,
                title="Satisfaction client (démo)",
                description="Sondage d'exemple généré automatiquement pour tester l'application.",
                allow_anonymous=True,
            )
            q1 = Question.objects.create(
                survey=survey, text="Êtes-vous satisfait de notre service ?",
                question_type=Question.SINGLE, order=0, required=True,
            )
            c_oui = Choice.objects.create(question=q1, text="Oui", order=0)
            Choice.objects.create(question=q1, text="Non", order=1)

            q2 = Question.objects.create(
                survey=survey, text="Qu'est-ce qui vous a le plus plu ?",
                question_type=Question.TEXT, order=1, required=False,
                condition_question=q1, condition_choice=c_oui,
            )
            Question.objects.create(
                survey=survey, text="Quels canaux utilisez-vous ?",
                question_type=Question.MULTIPLE, order=2, required=True,
            )
            q3 = Question.objects.get(survey=survey, order=2)
            for label in ["E-mail", "Téléphone", "Chat en ligne"]:
                Choice.objects.create(question=q3, text=label)

            self.stdout.write(self.style.SUCCESS(
                f"Sondage de démonstration créé : {survey.get_absolute_url()}"
            ))
        else:
            self.stdout.write("Le sondage de démonstration existe déjà.")

        self.stdout.write(self.style.SUCCESS("\nTerminé. Connectez-vous avec demo / demo12345 (ou admin / admin1234 pour /admin/)."))
