from django.contrib import admin

from .models import Mailing, MailingAttempt


class MailingAttemptInline(admin.TabularInline):
    """Inline для отображения попыток рассылки на странице рассылки"""

    model = MailingAttempt
    extra = 0
    readonly_fields = ('client', 'status', 'server_response', 'attempted_at')
    can_delete = False
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админ-панель для модели рассылки"""

    list_display = (
        'id',
        'message',
        'get_status_display',
        'owner',
        'get_clients_count',
        'start_time',
        'end_time',
        'created_at',
    )
    list_filter = ('frequency', 'start_time', 'end_time', 'created_at', 'owner')
    search_fields = ('message__subject',)
    filter_horizontal = ('clients',)
    raw_id_fields = ('owner', 'message')
    date_hierarchy = 'created_at'
    inlines = [MailingAttemptInline]
    readonly_fields = ('get_status_display',)

    def get_clients_count(self, obj):
        """Количество клиентов в рассылке"""
        return obj.clients.count()

    get_clients_count.short_description = 'Клиентов'

    def get_status_display(self, obj):
        """Отображение статуса"""
        return obj.status_display

    get_status_display.short_description = 'Статус'

    fieldsets = (
        (None, {'fields': ('message', 'clients', 'owner')}),
        ('Время отправки', {'fields': ('start_time', 'end_time')}),
        ('Статус', {'fields': ('get_status_display',), 'classes': ('collapse',)}),
    )

    def get_frequency_display(self, obj):
        return dict(Mailing.FREQUENCY_CHOICES).get(obj.frequency, '—')
    get_frequency_display.short_description = 'Периодичность'


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админ-панель для модели попыток рассылки"""

    list_display = ('mailing', 'client', 'status', 'attempted_at')
    list_filter = ('status', 'attempted_at')
    search_fields = ('mailing__message__subject', 'client__email')
    date_hierarchy = 'attempted_at'
    readonly_fields = ('attempted_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
