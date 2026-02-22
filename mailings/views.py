from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db import models

from .forms import MailingForm
from .models import Mailing, MailingAttempt
from users.mixins import OwnerOrManagerMixin


class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок"""
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        # Обновляем статус для всех рассылок в queryset
        if self.request.user.is_manager or self.request.user.is_superuser:
            queryset = Mailing.objects.all().select_related('owner', 'message').prefetch_related('clients')
        else:
            queryset = Mailing.objects.filter(owner=self.request.user).select_related('message').prefetch_related(
                'clients')

        # Обновляем статус для каждой рассылки
        for mailing in queryset:
            mailing.update_status()

        return queryset


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о рассылке"""
    model = Mailing
    template_name = 'mailings/mailing_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        """
        Переопределяем get_object для вызова update_status()
        при каждом просмотре рассылки
        """
        obj = super().get_object(queryset)
        # Обновляем статус при просмотре
        obj.update_status()
        return obj

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        mailing = self.get_object()
        if not (request.user.is_manager or request.user.is_superuser or mailing.owner == request.user):
            messages.error(request, 'У вас нет прав для просмотра этой рассылки.')
            return redirect('mailings:list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attempts'] = MailingAttempt.objects.filter(mailing=self.object)[:10]
        context['success_count'] = MailingAttempt.objects.filter(mailing=self.object, status='success').count()
        context['failed_count'] = MailingAttempt.objects.filter(mailing=self.object, status='failed').count()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        # Явно вызываем валидацию модели
        try:
            form.instance.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

        messages.success(self.request, 'Рассылка успешно создана.')
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        mailing = self.get_object()
        if mailing.owner != request.user:
            messages.error(request, 'Вы можете редактировать только свои рассылки.')
            return redirect('mailings:list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Явно вызываем валидацию модели
        try:
            form.instance.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

        messages.success(self.request, 'Рассылка успешно обновлена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('mailings:detail', kwargs={'pk': self.object.pk})


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рассылки"""
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        mailing = self.get_object()
        if mailing.owner != request.user:
            messages.error(request, 'Вы можете удалять только свои рассылки.')
            return redirect('mailings:list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка успешно удалена.')
        return super().delete(request, *args, **kwargs)


class MailingDisableView(LoginRequiredMixin, View):
    """Отключение рассылки менеджером"""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_manager or request.user.is_superuser):
            messages.error(request, 'У вас нет прав для отключения рассылок.')
            return redirect('mailings:list')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = Mailing.STATUS_DISABLED
        mailing.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Рассылка "{mailing.message.subject}" отключена.')
        return redirect('mailings:detail', pk=pk)


class MailingStatsView(LoginRequiredMixin, DetailView):
    """Статистика по конкретной рассылке (детальная)"""
    model = Mailing
    template_name = 'mailings/mailing_stats_detail.html'  # Изменено имя шаблона
    context_object_name = 'mailing'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        mailing = self.get_object()
        if not (request.user.is_manager or request.user.is_superuser or mailing.owner == request.user):
            messages.error(request, 'У вас нет прав для просмотра статистики этой рассылки.')
            return redirect('mailings:list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = MailingAttempt.objects.filter(mailing=self.object)

        # Основная статистика
        context['total_attempts'] = attempts.count()
        context['success_attempts'] = attempts.filter(status='success').count()
        context['failed_attempts'] = attempts.filter(status='failed').count()
        context['success_rate'] = (
            (context['success_attempts'] / context['total_attempts'] * 100)
            if context['total_attempts'] > 0 else 0
        )

        # Статистика по клиентам
        client_stats = []
        for client in self.object.clients.all():
            client_attempts = attempts.filter(client=client)
            client_stats.append({
                'client': client,
                'total': client_attempts.count(),
                'success': client_attempts.filter(status='success').count(),
                'failed': client_attempts.filter(status='failed').count(),
                'last_attempt': client_attempts.order_by('-attempted_at').first()
            })
        context['client_stats'] = client_stats

        # Последние 50 попыток
        context['recent_attempts'] = attempts.order_by('-attempted_at')[:50]

        return context


class MailingStatsListView(LoginRequiredMixin, ListView):
    """Общая статистика по всем рассылкам пользователя"""
    model = Mailing
    template_name = 'mailings/mailing_stats_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_manager or self.request.user.is_superuser:
            return Mailing.objects.all().select_related('message', 'owner').prefetch_related('attempts', 'clients')
        else:
            return Mailing.objects.filter(owner=self.request.user).select_related('message').prefetch_related(
                'attempts', 'clients')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общая статистика
        if self.request.user.is_manager or self.request.user.is_superuser:
            attempts = MailingAttempt.objects.all()
        else:
            attempts = MailingAttempt.objects.filter(mailing__owner=self.request.user)

        context['total_attempts'] = attempts.count()
        context['success_attempts'] = attempts.filter(status='success').count()
        context['failed_attempts'] = attempts.filter(status='failed').count()
        context['success_rate'] = (
            (context['success_attempts'] / context['total_attempts'] * 100)
            if context['total_attempts'] > 0 else 0
        )

        # Статистика по месяцам с правильным процентом
        from django.db.models.functions import TruncMonth
        from django.db.models import Count, Q

        monthly_stats_raw = attempts.annotate(
            month=TruncMonth('attempted_at')
        ).values('month').annotate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed'))
        ).order_by('month')

        # Добавляем процент к каждому месяцу
        monthly_stats = []
        for stat in monthly_stats_raw:
            stat['percentage'] = (stat['success'] / stat['total'] * 100) if stat['total'] > 0 else 0
            monthly_stats.append(stat)

        context['monthly_stats'] = monthly_stats

        # Статистика по рассылкам
        mailing_stats = []
        for mailing in context['mailings']:
            mailing_attempts = mailing.attempts.all()
            total = mailing_attempts.count()
            success = mailing_attempts.filter(status='success').count()
            failed = mailing_attempts.filter(status='failed').count()

            mailing_stats.append({
                'mailing': mailing,
                'total_attempts': total,
                'success_attempts': success,
                'failed_attempts': failed,
                'success_rate': (success / total * 100) if total > 0 else 0
            })

        context['mailing_stats'] = mailing_stats

        return context


class MailingSendView(LoginRequiredMixin, View):
    """Ручной запуск рассылки"""

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)

        # Проверка прав доступа
        if not (request.user.is_manager or request.user.is_superuser or mailing.owner == request.user):
            messages.error(request, 'У вас нет прав для запуска этой рассылки.')
            return redirect('mailings:detail', pk=pk)

        # Проверка статуса рассылки
        if mailing.status != Mailing.STATUS_STARTED:
            messages.error(request, 'Можно запускать только активные рассылки (статус "Запущена").')
            return redirect('mailings:detail', pk=pk)

        # Проверка времени
        now = timezone.now()
        if not (mailing.start_time <= now <= mailing.end_time):
            messages.error(request, 'Рассылку можно запустить только в период между start_time и end_time')
            return redirect('mailings:detail', pk=pk)

        # Отправка писем клиентам
        success_count = 0
        failed_count = 0

        for client in mailing.clients.all():
            try:
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                status = 'success'
                server_response = 'OK'
                success_count += 1
            except Exception as e:
                status = 'failed'
                server_response = str(e)
                failed_count += 1

            # Создание записи о попытке
            MailingAttempt.objects.create(
                mailing=mailing,
                client=client,
                status=status,
                server_response=server_response
            )

        messages.success(request, f'Рассылка отправлена. Успешно: {success_count}, Ошибок: {failed_count}')
        return redirect('mailings:detail', pk=pk)