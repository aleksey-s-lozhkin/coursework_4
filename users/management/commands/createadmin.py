from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создает администратора по умолчанию'

    def handle(self, *args, **options):
        User = get_user_model()

        # Проверяем, существует ли уже такой пользователь
        if User.objects.filter(email="admin@admin.com").exists():
            self.stdout.write(self.style.WARNING('Пользователь уже существует!'))
            return

        user = User.objects.create(
            email="admin@admin.com",
            first_name='admin',
            last_name='admin',
            is_staff=True,
            is_superuser=True,
        )

        user.set_password("admin")
        user.save()

        self.stdout.write(self.style.SUCCESS(f'Администратор создан: {user.email} / пароль: admin'))
