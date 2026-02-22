from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from users.models import User  # Импортируем вашу модель User


class Command(BaseCommand):
    help = 'Создает группы и назначает права'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Показать что будет сделано без реальных изменений')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # === Группа менеджеров ===
        managers_group, created = Group.objects.get_or_create(name='Managers')

        self.stdout.write(f"\nГруппа 'Managers': {'создана' if created else 'уже существует'}")

        # Получаем все нужные права
        permission_codenames = [
            'can_view_all_clients',
            'can_view_all_mailings',
            'can_block_users',
            'can_disable_mailings',
        ]

        # Находим существующие права
        permissions = Permission.objects.filter(codename__in=permission_codenames)

        self.stdout.write(f"   Найдено прав: {permissions.count()}")
        for perm in permissions:
            self.stdout.write(f"     • {perm.codename} - {perm.name}")

        if not dry_run:
            # Назначаем права группе
            managers_group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('   Права назначены группе Managers'))
        else:
            self.stdout.write(self.style.WARNING('   Режим просмотра - права НЕ назначены'))

        # === Группа обычных пользователей (опционально) ===
        users_group, created = Group.objects.get_or_create(name='Regular Users')
        self.stdout.write(f"\nГруппа 'Regular Users': {'создана' if created else 'уже существует'}")

        if created and not dry_run:

            pass

        # === Статистика ===
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("ИТОГ:"))
        self.stdout.write(f"   Группа Managers: {managers_group.permissions.count()} прав")
        self.stdout.write(f"   Группа Regular Users: {users_group.permissions.count()} прав")
        self.stdout.write(f"   Всего пользователей в группах: {User.objects.filter(groups__isnull=False).count()}")
        self.stdout.write("=" * 50)
