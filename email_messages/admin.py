from django.contrib import admin

from .models import EmailMessage


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    """Админ-панель для модели сообщения"""

    list_display = ('subject', 'owner', 'created_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('subject', 'body')
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'
