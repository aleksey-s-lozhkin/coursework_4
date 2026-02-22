from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import Group
from django.views import View
from django.views.generic import ListView, RedirectView, TemplateView, UpdateView

from clients.models import Client
from mailings.models import Mailing, MailingAttempt

from .forms import LoginForm, RegistrationForm, UserUpdateForm
from .mixins import ManagerRequiredMixin
from .models import User, Profile


class RootRedirectView(RedirectView):
    """Корень сайта - перенаправляет в зависимости от статуса"""

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse_lazy('users:home')
        return reverse_lazy('users:login')


@method_decorator(vary_on_cookie, name='dispatch')
class HomeView(LoginRequiredMixin, TemplateView):
    """Главная страница = личный кабинет"""
    template_name = 'home.html'
    login_url = reverse_lazy('users:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user

        # КЛЮЧ КЭША - определяем здесь!
        cache_key = f'home_stats_data_{self.request.user.id}_{self.request.user.is_manager}'

        # Пробуем получить данные из кэша
        cached_data = cache.get(cache_key)
        if cached_data and settings.CACHE_ENABLE:
            context.update(cached_data)
            return context

        now = timezone.now()

        if self.request.user.is_manager or self.request.user.is_superuser:

            # Для менеджера: статистика по ВСЕМ данным
            all_mailings = Mailing.objects.all()
            all_attempts = MailingAttempt.objects.all()

            context['total_mailings'] = all_mailings.count()
            active_mailings = [m for m in all_mailings if m.status == 'started']
            context['active_mailings'] = len(active_mailings)
            context['total_clients'] = Client.objects.count()
            context['total_users'] = User.objects.filter(is_manager=False).exclude(is_superuser=True).count()

            context['total_attempts'] = all_attempts.count()
            context['success_attempts'] = all_attempts.filter(status='success').count()
            context['failed_attempts'] = all_attempts.filter(status='failed').count()
            context['success_rate'] = (
                (context['success_attempts'] / context['total_attempts'] * 100)
                if context['total_attempts'] > 0 else 0
            )
        else:

            # Для обычного пользователя: статистика ТОЛЬКО ЕГО данных
            user_mailings = Mailing.objects.filter(owner=self.request.user)
            user_clients = Client.objects.filter(owner=self.request.user)
            user_attempts = MailingAttempt.objects.filter(mailing__owner=self.request.user)

            context['total_mailings'] = user_mailings.count()
            active_mailings = [m for m in user_mailings if m.status == 'started']
            context['active_mailings'] = len(active_mailings)
            context['total_clients'] = user_clients.count()

            context['total_attempts'] = user_attempts.count()
            context['success_attempts'] = user_attempts.filter(status='success').count()
            context['failed_attempts'] = user_attempts.filter(status='failed').count()
            context['success_rate'] = (
                (context['success_attempts'] / context['total_attempts'] * 100)
                if context['total_attempts'] > 0 else 0
            )

        # Сохраняем данные в кэш на 5 минут
        if settings.CACHE_ENABLE:
            cache.set(cache_key, {
                'total_mailings': context['total_mailings'],
                'active_mailings': context['active_mailings'],
                'total_clients': context['total_clients'],
                'total_users': context.get('total_users', 0),
                'total_attempts': context['total_attempts'],
                'success_attempts': context['success_attempts'],
                'failed_attempts': context['failed_attempts'],
                'success_rate': context['success_rate'],
            }, 60 * 5)

        return context


class UserListView(ManagerRequiredMixin, ListView):
    def get_queryset(self):
        # Исключаем менеджеров и суперпользователей
        managers = Group.objects.get(name='Managers')
        return User.objects.exclude(groups=managers).exclude(is_superuser=True)


class UserBlockView(ManagerRequiredMixin, View):
    """Блокировка/разблокировка пользователя (только для менеджеров)"""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_manager=False)
        user.is_active = not user.is_active
        user.save()
        status = 'разблокирован' if user.is_active else 'заблокирован'
        messages.success(request, f'Пользователь {user.email} {status}.')
        return redirect('users:user_list')


# Остальные представления (регистрация, логин и т.д.)
class RegisterView(View):
    """Регистрация нового пользователя"""
    template_name = 'users/register.html'
    form_class = RegistrationForm

    def get(self, request):
        """Обработка GET запроса - отображение формы регистрации"""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Обработка POST запроса - сохранение формы"""
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()

            token = user.generate_verification_token()
            current_site = get_current_site(request)

            # Контекст для шаблонов
            context = {
                'user': user,
                'domain': current_site.domain,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http',
            }

            # HTML версия письма
            html_message = render_to_string('users/registration/email_verification.html', context)

            # Текстовая версия письма
            text_message = render_to_string('users/registration/email_verification.txt', context)

            # Отправляем мультиформатное письмо
            email = EmailMultiAlternatives(
                subject='Подтвердите ваш email',
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            return render(request, 'users/verify_email_sent.html', {'email': user.email})

        return render(request, self.template_name, {'form': form})


class VerifyEmailView(View):
    """Подтверждение email по ссылке из письма"""

    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)
            if user.verify_email(token):
                messages.success(request, 'Email успешно подтвержден! Теперь вы можете войти.')
                return redirect('users:login')
            else:
                return render(
                    request,
                    'users/verify_email_failed.html',
                    {'message': 'Срок действия ссылки истек. Пожалуйста, запросите подтверждение заново.'},
                )
        except User.DoesNotExist:
            return render(
                request, 'users/verify_email_failed.html', {'message': 'Недействительный токен подтверждения.'}
            )


class CustomLoginView(LoginView):
    """Страница входа"""
    template_name = 'users/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('users:home')

    def form_valid(self, form):
        user = form.get_user()

        # Проверка, не заблокирован ли пользователь
        if not user.is_active:
            messages.error(self.request, 'Ваш аккаунт заблокирован. Обратитесь к администратору.')
            return self.form_invalid(form)

        # Проверка подтверждения email
        if not user.is_email_verified:
            messages.error(self.request, 'Пожалуйста, подтвердите ваш email перед входом.')
            return self.form_invalid(form)

        messages.success(self.request, f'Добро пожаловать, {user.email}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Выход из системы"""

    next_page = reverse_lazy('users:login')

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'Вы успешно вышли из системы.')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    """Представление для запроса сброса пароля."""

    template_name = 'users/registration/password_reset.html'
    email_template_name = 'users/registration/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Представление для отображения сообщения об отправке письма для сброса пароля."""

    template_name = 'users/registration/password_reset_done.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Представление для ввода нового пароля."""

    template_name = 'users/registration/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Представление для отображения сообщения об успешном сбросе пароля."""

    template_name = 'users/registration/password_reset_complete.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:home')
        return super().dispatch(request, *args, **kwargs)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Контроллер для редактирования профиля пользователя"""
    model = User
    form_class = UserUpdateForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        """Возвращает текущего пользователя"""
        return self.request.user

    def get_context_data(self, **kwargs):
        """Добавляем user в контекст для отображения email"""
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user  # явно передаем пользователя
        return context

    def form_valid(self, form):
        """Сохраняет форму при успешной валидации"""
        form.save()

        if settings.CACHE_ENABLE:
            cache.delete(f'profile_view_{self.request.user.id}')
            cache.delete(f'home_stats_{self.request.user.id}_True')
            cache.delete(f'home_stats_{self.request.user.id}_False')

        messages.success(self.request, 'Профиль успешно обновлен!')
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Возвращает ошибки при невалидной форме"""
        messages.error(
            self.request,
            'Пожалуйста, исправьте ошибки в форме.'
        )
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(cache_page(60 * 5), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class ProfileView(LoginRequiredMixin, DetailView):
    """Контроллер для просмотра профиля пользователя"""
    model = Profile
    template_name = 'users/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        """Возвращает профиль текущего пользователя, создает если нет"""
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            # Создаем профиль, если его нет
            return Profile.objects.create(user=self.request.user)
