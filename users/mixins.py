from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy


class ManagerRequiredMixin(UserPassesTestMixin):
    """Только для менеджеров"""

    def test_func(self):
        return (self.request.user.groups.filter(name='Managers').exists() or
                self.request.user.is_superuser)

    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав для доступа к этой странице.')
        return redirect('users:home')


class OwnerOrManagerMixin(UserPassesTestMixin):
    """Проверка: владелец объекта или менеджер"""
    def test_func(self):
        obj = self.get_object()
        is_manager = (self.request.user.groups.filter(name='Managers').exists() or
                     self.request.user.is_superuser)
        return is_manager or obj.owner == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав для просмотра этого объекта.')
        return redirect('users:home')


class OwnerOnlyMixin(UserPassesTestMixin):
    """Только владелец объекта"""

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, 'Вы можете редактировать только свои объекты.')
        return redirect('users:home')
