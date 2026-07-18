from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, FormView

from .forms import LoginForm, RegisterForm
from django.conf import settings


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = '/'

    def form_valid(self, form):
        response = super().form_valid(form)
        auth_login(self.request, self.object, backend='accounts.backends.EmailOrUsernameModelBackend')
        messages.success(self.request, f"Bienvenue {self.object.username} ! Votre compte a été créé.")
        return redirect('surveys:dashboard')


def _lockout_key(identifier):
    return f"login_attempts:{identifier.lower()}"


@method_decorator([csrf_protect, never_cache], name='dispatch')
class LoginView(FormView):
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('surveys:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        identifier = request.POST.get('username', '').strip()
        key = _lockout_key(identifier) if identifier else None
        if key:
            attempts = cache.get(key, 0)
            if attempts >= settings.LOGIN_MAX_ATTEMPTS:
                messages.error(
                    request,
                    "Trop de tentatives de connexion. Réessayez dans quelques minutes."
                )
                return self.render_to_response(self.get_context_data(form=self.get_form()))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        identifier = self.request.POST.get('username', '').strip()
        if identifier:
            cache.delete(_lockout_key(identifier))
        user = form.get_user()
        auth_login(self.request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
        if form.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            self.request.session.set_expiry(0)
        messages.success(self.request, f"Content de vous revoir, {user.username} !")
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        return redirect(next_url or 'surveys:dashboard')

    def form_invalid(self, form):
        identifier = self.request.POST.get('username', '').strip()
        if identifier:
            key = _lockout_key(identifier)
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, timeout=settings.LOGIN_LOCKOUT_SECONDS)
        return super().form_invalid(form)


def logout_view(request):
    auth_logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('surveys:home')
