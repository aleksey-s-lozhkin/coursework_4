from django.conf import settings
from django.db import models


class Client(models.Model):
    """Модель клиента (получателя рассылки)"""

    email = models.EmailField(verbose_name='Email')
    full_name = models.CharField(max_length=255, verbose_name='Ф.И.О.')
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clients', verbose_name='Владелец'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        unique_together = ['email', 'owner']

    def __str__(self):
        return f"{self.full_name} ({self.email})"
