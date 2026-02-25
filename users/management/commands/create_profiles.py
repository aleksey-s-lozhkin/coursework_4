from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает профили для пользователей, у которых их нет'

    def handle(self, *args, **options):
        users_without_profile = []
        profiles_created = 0

        for user in User.objects.all():
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                profiles_created += 1
                users_without_profile.append(user.email)

        self.stdout.write(self.style.SUCCESS(f'Создано профилей: {profiles_created}'))
        if users_without_profile:
            self.stdout.write('Пользователи:')
            for email in users_without_profile:
                self.stdout.write(f'  - {email}')
