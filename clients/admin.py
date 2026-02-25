from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Админ-панель для модели клиента"""

    list_display = ('email', 'full_name', 'owner', 'created_at', 'get_mailings_count')
    list_filter = ('created_at', 'owner')
    search_fields = ('email', 'full_name', 'comment')
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'

    def get_mailings_count(self, obj):
        """Количество рассылок для клиента"""
        return obj.mailings.count()

    get_mailings_count.short_description = 'Рассылок'
