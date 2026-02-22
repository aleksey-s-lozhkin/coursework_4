from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import EmailMessageForm
from .models import EmailMessage


class EmailMessageListView(LoginRequiredMixin, ListView):
    """Список сообщений"""

    model = EmailMessage
    template_name = 'email_messages/emailmessage_list.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return EmailMessage.objects.filter(owner=self.request.user)


class EmailMessageDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о сообщении"""

    model = EmailMessage
    template_name = 'email_messages/emailmessage_detail.html'
    context_object_name = 'message'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        message = self.get_object()
        if message.owner != request.user:
            messages.error(request, 'У вас нет прав для просмотра этого сообщения.')
            return redirect('email_messages:list')
        return super().dispatch(request, *args, **kwargs)


class EmailMessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения"""

    model = EmailMessage
    form_class = EmailMessageForm
    template_name = 'email_messages/emailmessage_form.html'
    success_url = reverse_lazy('email_messages:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Сообщение успешно создано.')
        return super().form_valid(form)


class EmailMessageUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сообщения"""

    model = EmailMessage
    form_class = EmailMessageForm
    template_name = 'email_messages/emailmessage_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        message = self.get_object()
        if message.owner != request.user:
            messages.error(request, 'Вы можете редактировать только свои сообщения.')
            return redirect('email_messages:list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, 'Сообщение успешно обновлено.')
        return reverse('email_messages:detail', kwargs={'pk': self.object.pk})


class EmailMessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения"""

    model = EmailMessage
    template_name = 'email_messages/emailmessage_confirm_delete.html'
    success_url = reverse_lazy('email_messages:list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        message = self.get_object()
        if message.owner != request.user:
            messages.error(request, 'Вы можете удалять только свои сообщения.')
            return redirect('email_messages:list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Сообщение успешно удалено.')
        return super().delete(request, *args, **kwargs)
