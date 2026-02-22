# mailings/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from clients.models import Client
from email_messages.models import EmailMessage


class Mailing(models.Model):
    """Модель рассылки"""

    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_COMPLETED = 'completed'
    STATUS_DISABLED = 'disabled'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
        (STATUS_DISABLED, 'Отключена'),
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name='Название рассылки',
        help_text='Введите название для идентификации рассылки'
    )

    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name='Периодичность',
        default='daily',  # Значение по умолчанию
        help_text='Как часто отправлять рассылку'
    )

    start_time = models.DateTimeField(verbose_name='Дата и время начала отправки')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания отправки')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name='Статус'
    )

    message = models.ForeignKey(
        EmailMessage,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Сообщение'
    )
    clients = models.ManyToManyField(
        Client,
        related_name='mailings',
        verbose_name='Клиенты'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Владелец'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-created_at']
        permissions = [
            ('can_disable_mailing', 'Может отключать рассылки'),
        ]

    def __str__(self):
        return self.name

    def get_calculated_status(self):
        """
        Вычисляет актуальный статус на основе текущего времени
        """
        now = timezone.now()

        # Если рассылка отключена менеджером, статус не меняется
        if self.status == self.STATUS_DISABLED:
            return self.STATUS_DISABLED

        if now < self.start_time:
            return self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            return self.STATUS_STARTED
        else:  # now > self.end_time
            return self.STATUS_COMPLETED

    def update_status(self):
        """
        Обновляет статус в базе данных на основе текущего времени
        """
        calculated_status = self.get_calculated_status()

        # Если статус изменился, обновляем его в базе
        if self.status != calculated_status:
            self.status = calculated_status
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    @property
    def status_display(self):
        """Отображение статуса на русском языке"""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')

    def get_frequency_display(self):
        """Отображение периодичности на русском языке"""
        return dict(self.FREQUENCY_CHOICES).get(self.frequency, 'Не указана')

    def clean(self):
        """Валидация на уровне модели (вызывается только при создании/обновлении)"""
        # Проверяем только если объект новый или изменяется
        if self.pk is None or self._state.adding:
            if self.start_time and self.start_time < timezone.now():
                raise ValidationError({'start_time': 'Дата начала не может быть в прошлом.'})

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Дата окончания должна быть позже даты начала.')

    def save(self, *args, **kwargs):
        """Убираем вызов clean() из save, чтобы не вызывать валидацию при чтении"""
        # Не вызываем clean() здесь!
        super().save(*args, **kwargs)


class MailingAttempt(models.Model):
    """Модель попытки рассылки"""
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Не успешно'),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts', verbose_name='Рассылка')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='attempts', verbose_name='Клиент')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус')
    server_response = models.TextField(verbose_name='Ответ сервера', blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.mailing} - {self.client} - {self.get_status_display()}"

    def clear_cache(self):
        """Очищает кеш, связанный с рассылкой"""
        if hasattr(settings, 'CACHE_ENABLE') and settings.CACHE_ENABLE:
            cache.delete(f'mailing_detail_{self.pk}')
            cache.delete(f'mailing_attempts_{self.pk}')

    def save(self, *args, **kwargs):
        self.clear_cache()  # Очищаем кеш при сохранении
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.clear_cache()
        super().delete(*args, **kwargs)