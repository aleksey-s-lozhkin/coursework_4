import secrets

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Менеджер для создания пользователей с email в качестве идентификатора"""

    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_manager', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Модель пользователя"""

    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=35, verbose_name='Телефон', blank=True, null=True)
    avatar = models.ImageField(upload_to='users/avatar/%Y/%m', verbose_name='Аватар', blank=True, null=True)
    country = models.CharField(max_length=10, verbose_name='Страна', blank=True, null=True)

    # Поля для подтверждения email
    is_email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)

    # Роль пользователя (менеджер или обычный пользователь)
    is_manager = models.BooleanField(default=False, verbose_name='Менеджер')

    # Поле для авторизации
    USERNAME_FIELD = 'email'
    # Обязательные поля при createsuperuser
    REQUIRED_FIELDS = []
    # Используем кастомный менеджер
    objects = UserManager()

    class Meta:
        """Метаданные модели User"""
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['email']
        permissions = [
            ('can_view_all_clients', 'Может просматривать всех клиентов'),
            ('can_view_all_mailings', 'Может просматривать все рассылки'),
            ('can_block_users', 'Может блокировать пользователей'),
            ('can_disable_mailings', 'Может отключать рассылки'),
        ]

        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_manager']),
        ]

    def __str__(self):
        return self.email

    @property
    def is_manager_by_group(self):
        """Проверка через группы"""
        return self.groups.filter(name='Managers').exists()

    @property
    def is_manager_combined(self):
        """Комбинированная проверка: группа ИЛИ старое поле ИЛИ суперпользователь"""
        return self.is_manager_by_group or self.is_manager or self.is_superuser

    @property
    def manager_type(self):
        """Тип менеджера (для отладки)"""
        if self.is_superuser:
            return 'superuser'
        elif self.is_manager_by_group:
            return 'group_manager'
        elif self.is_manager:
            return 'legacy_manager'
        return None

    def generate_verification_token(self):
        """Генерация токена для подтверждения email"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.token_created_at = timezone.now()
        self.save()
        return self.email_verification_token

    def verify_email(self, token):
        """Проверка токена и подтверждение email"""
        if (
                self.email_verification_token == token
                and self.token_created_at
                and (timezone.now() - self.token_created_at).days < 1
        ):
            self.is_email_verified = True
            self.email_verification_token = None
            self.token_created_at = None
            self.save()
            return True
        return False

class Profile(models.Model):
    """Профиль пользователя без поля avatar"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='О себе'
    )
    location = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Город'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='Телефон'
    )

    def __str__(self):
        return f'Профиль пользователя {self.user.email}'

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля при регистрации пользователя"""
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Автоматическое сохранение профиля при сохранении пользователя"""
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
