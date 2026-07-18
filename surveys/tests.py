from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Answer, Choice, Question, Response, Survey

User = get_user_model()


class SurveyModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='CorrectHorseBattery9!')

    def test_is_active_and_status_label(self):
        survey = Survey.objects.create(owner=self.user, title='Test')
        self.assertTrue(survey.is_active)
        self.assertEqual(survey.status_label, "Actif")

        survey.is_closed = True
        survey.save()
        self.assertFalse(survey.is_active)

    def test_expired_survey_is_inactive(self):
        survey = Survey.objects.create(
            owner=self.user, title='Expiré', expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(survey.is_active)
        self.assertTrue(survey.is_expired)


class SurveyBuilderViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bob', password='CorrectHorseBattery9!')
        self.client.login(username='bob', password='CorrectHorseBattery9!')

    def test_create_survey_with_conditional_question(self):
        data = {
            'title': 'Satisfaction', 'description': '', 'expires_at': '', 'allow_anonymous': 'on',
            'q_text': ['Satisfait ?', 'Pourquoi pas ?'],
            'q_type': ['single', 'text'],
            'q_required': ['1', '0'],
            'q_choices': ['Oui\nNon', ''],
            'q_condition_index': ['', '0'],
            'q_condition_choice_text': ['', 'Non'],
        }
        resp = self.client.post('/sondages/nouveau/', data, follow=True)
        self.assertEqual(resp.status_code, 200)
        survey = Survey.objects.get(title='Satisfaction')
        self.assertEqual(survey.questions.count(), 2)
        q2 = survey.questions.get(order=1)
        self.assertIsNotNone(q2.condition_question_id)
        self.assertEqual(q2.condition_choice.text, 'Non')

    def test_only_owner_can_see_results(self):
        survey = Survey.objects.create(owner=self.user, title='Privé')
        other = User.objects.create_user(username='eve', password='CorrectHorseBattery9!')
        self.client.logout()
        self.client.login(username='eve', password='CorrectHorseBattery9!')
        resp = self.client.get(f'/sondages/{survey.pk}/resultats/')
        self.assertEqual(resp.status_code, 404)


class SurveyFillTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='carla', password='CorrectHorseBattery9!')
        self.survey = Survey.objects.create(owner=self.owner, title='Public', allow_anonymous=True)
        self.q1 = Question.objects.create(survey=self.survey, text='Q1', question_type=Question.SINGLE, order=0)
        self.c1 = Choice.objects.create(question=self.q1, text='A')
        Choice.objects.create(question=self.q1, text='B')

    def test_anonymous_can_submit_response(self):
        resp = self.client.post(self.survey.get_absolute_url(), {f'answer_{self.q1.id}': str(self.c1.id)}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Response.objects.filter(survey=self.survey).count(), 1)
        answer = Answer.objects.get(response__survey=self.survey, question=self.q1)
        self.assertIn(self.c1, answer.choices.all())

    def test_required_question_blocks_empty_submission(self):
        self.q1.required = True
        self.q1.save()
        resp = self.client.post(self.survey.get_absolute_url(), {}, follow=True)
        self.assertEqual(Response.objects.filter(survey=self.survey).count(), 0)
        self.assertContains(resp, "obligatoire")

    def test_closed_survey_rejects_submissions(self):
        self.survey.is_closed = True
        self.survey.save()
        resp = self.client.get(self.survey.get_absolute_url())
        self.assertContains(resp, "n'est plus ouvert")
