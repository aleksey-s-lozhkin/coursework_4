from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache  # Убрали cache_page
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.core.cache import cache  # ИСПРАВЛЕНО!

from .forms import ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    """Список клиентов с кешированием"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        cache_key = f'clients_queryset_{self.request.user.id}_{self.request.user.is_manager}'

        cached_queryset = cache.get(cache_key)
        if cached_queryset is not None and settings.CACHE_ENABLE:
            return cached_queryset

        if self.request.user.is_manager or self.request.user.is_superuser:
            queryset = Client.objects.all().select_related('owner')
        else:
            queryset = Client.objects.filter(owner=self.request.user)

        if settings.CACHE_ENABLE:
            cache.set(cache_key, queryset, 60 * 5)

        return queryset


class ClientDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о клиенте с кешированием"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_object(self, queryset=None):
        cache_key = f'client_detail_{self.kwargs.get("pk")}'
        cached_client = cache.get(cache_key)

        if cached_client and settings.CACHE_ENABLE:
            return cached_client

        client = super().get_object(queryset)

        if settings.CACHE_ENABLE:
            cache.set(cache_key, client, 60 * 5)

        return client

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        client = self.get_object()
        if not (request.user.is_manager or request.user.is_superuser or client.owner == request.user):
            messages.error(request, 'У вас нет прав для просмотра этого клиента.')
            return redirect('clients:list')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(never_cache, name='dispatch')
class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание клиента"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user

        if settings.CACHE_ENABLE:
            cache.delete(f'clients_queryset_{self.request.user.id}_True')
            cache.delete(f'clients_queryset_{self.request.user.id}_False')
            cache.delete(f'home_stats_{self.request.user.id}_True')
            cache.delete(f'home_stats_{self.request.user.id}_False')

        messages.success(self.request, 'Клиент успешно создан.')
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование клиента"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        client = self.get_object()
        if client.owner != request.user:
            messages.error(request, 'Вы можете редактировать только своих клиентов.')
            return redirect('clients:list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if settings.CACHE_ENABLE:
            cache.delete(f'clients_queryset_{self.request.user.id}_True')
            cache.delete(f'clients_queryset_{self.request.user.id}_False')
            cache.delete(f'client_detail_{self.object.pk}')

        messages.success(self.request, 'Клиент успешно обновлен.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clients:detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление клиента"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        client = self.get_object()
        if client.owner != request.user:
            messages.error(request, 'Вы можете удалять только своих клиентов.')
            return redirect('clients:list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if settings.CACHE_ENABLE:
            cache.delete(f'clients_queryset_{request.user.id}_True')
            cache.delete(f'clients_queryset_{request.user.id}_False')
            cache.delete(f'client_detail_{self.get_object().pk}')

        messages.success(request, 'Клиент успешно удален.')
        return super().delete(request, *args, **kwargs)