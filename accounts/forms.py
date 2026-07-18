from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()

INPUT_CLASSES = 'form-control form-control-lg'


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'vous@exemple.com', 'autocomplete': 'email'}),
        help_text="Nous ne partagerons jamais votre e-mail."
    )
    first_name = forms.CharField(
        required=False, max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Prénom (optionnel)'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': INPUT_CLASSES, 'placeholder': "Nom d'utilisateur", 'autocomplete': 'username', 'autofocus': True
        })
        self.fields['password1'].widget.attrs.update({
            'class': INPUT_CLASSES, 'placeholder': 'Mot de passe', 'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': INPUT_CLASSES, 'placeholder': 'Confirmer le mot de passe', 'autocomplete': 'new-password'
        })
        for name in ('username', 'password1', 'password2'):
            self.fields[name].help_text = None

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte existe déjà avec cet e-mail.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nom d'utilisateur ou e-mail",
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES, 'placeholder': "Nom d'utilisateur ou e-mail",
            'autocomplete': 'username', 'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES, 'placeholder': 'Mot de passe', 'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(label="Se souvenir de moi", required=False)

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "Identifiants incorrects. Vérifiez votre nom d'utilisateur/e-mail et votre mot de passe.",
        'inactive': "Ce compte est désactivé.",
    }
