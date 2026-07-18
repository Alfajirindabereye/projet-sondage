from django import forms
from .models import Survey

INPUT_CLASSES = 'form-control'


class SurveyMetaForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description', 'expires_at', 'allow_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Ex: Satisfaction client 2026'}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASSES, 'rows': 3, 'placeholder': 'Décrivez brièvement votre sondage…'}),
            'expires_at': forms.DateTimeInput(attrs={'class': INPUT_CLASSES, 'type': 'datetime-local'}),
            'allow_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'allow_anonymous': "Autoriser les réponses sans compte",
            'expires_at': "Expiration automatique (optionnel)",
        }
