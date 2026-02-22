# clients/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    """Список клиентов"""

    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_manager or self.request.user.is_superuser:
            # Менеджеры видят всех клиентов
            return Client.objects.all().select_related('owner')
        else:
            # Обычные пользователи видят только своих клиентов
            return Client.objects.filter(owner=self.request.user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о клиенте"""

    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        client = self.get_object()
        if not (request.user.is_manager or request.user.is_superuser or client.owner == request.user):
            messages.error(request, 'У вас нет прав для просмотра этого клиента.')
            return redirect('clients:list')
        return super().dispatch(request, *args, **kwargs)


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание клиента"""

    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
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

    def get_success_url(self):
        messages.success(self.request, 'Клиент успешно обновлен.')
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
        messages.success(request, 'Клиент успешно удален.')
        return super().delete(request, *args, **kwargs)
