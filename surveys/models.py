import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Survey(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='surveys')
    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField("Date d'expiration", null=True, blank=True)
    is_closed = models.BooleanField("Clôturé manuellement", default=False)
    allow_anonymous = models.BooleanField("Autoriser les réponses sans compte", default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return bool(self.expires_at and timezone.now() >= self.expires_at)

    @property
    def is_active(self):
        return not self.is_closed and not self.is_expired

    @property
    def status_label(self):
        if self.is_closed:
            return "Clos (fermé manuellement)"
        if self.is_expired:
            return "Clos (expiré)"
        return "Actif"

    def get_absolute_url(self):
        return reverse('surveys:detail', args=[str(self.share_token)])

    def get_results_url(self):
        return reverse('surveys:results', args=[self.pk])

    @property
    def response_count(self):
        return self.responses.count()


class Question(models.Model):
    SINGLE = 'single'
    MULTIPLE = 'multiple'
    TEXT = 'text'
    TYPE_CHOICES = [
        (SINGLE, 'Choix unique'),
        (MULTIPLE, 'Choix multiple'),
        (TEXT, 'Texte libre'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField("Question", max_length=500)
    question_type = models.CharField("Type", max_length=10, choices=TYPE_CHOICES, default=SINGLE)
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField("Obligatoire", default=True)

    # Logique conditionnelle : cette question ne s'affiche que si
    # `condition_question` a été répondue avec `condition_choice`.
    condition_question = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependents'
    )
    condition_choice = models.ForeignKey(
        'Choice', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text

    @property
    def is_choice_type(self):
        return self.question_type in (self.SINGLE, self.MULTIPLE)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField("Choix", max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Réponse #{self.pk} — {self.survey.title}"


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text_answer = models.TextField(blank=True)
    choices = models.ManyToManyField(Choice, blank=True, related_name='answers')

    def __str__(self):
        return f"Réponse à: {self.question.text}"

    def display_value(self):
        if self.question.question_type == Question.TEXT:
            return self.text_answer
        return ", ".join(c.text for c in self.choices.all())
