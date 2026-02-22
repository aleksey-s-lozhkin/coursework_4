from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from mailings.models import Mailing, MailingAttempt


class Command(BaseCommand):
    help = 'Отправляет запланированные рассылки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mailing-id',
            type=int,
            help='ID конкретной рассылки для отправки'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет отправлено без реальной отправки'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно отправить даже если не в периоде'
        )

    def handle(self, *args, **options):
        mailing_id = options.get('mailing_id')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        now = timezone.now()

        # Получаем рассылки для обработки
        if mailing_id:
            mailings = Mailing.objects.filter(pk=mailing_id)
            if not mailings.exists():
                self.stdout.write(
                    self.style.ERROR(f'Рассылка с ID {mailing_id} не найдена')
                )
                return
        else:
            # Активные рассылки в периоде отправки
            mailings = Mailing.objects.filter(
                status=Mailing.STATUS_STARTED,
                start_time__lte=now,
                end_time__gte=now
            )

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"Найдено рассылок для обработки: {mailings.count()}")
        self.stdout.write(f"Время запуска: {now.strftime('%d.%m.%Y %H:%M:%S')}")
        self.stdout.write(f"{'=' * 60}\n")

        total_sent = 0
        total_failed = 0

        for mailing in mailings:
            self.stdout.write(f"\n📧 Рассылка: {mailing.name}")
            self.stdout.write(f"   ID: {mailing.id}")
            self.stdout.write(f"   Владелец: {mailing.owner.email}")
            self.stdout.write(f"   Тема: {mailing.message.subject}")
            self.stdout.write(
                f"   Период: {mailing.start_time.strftime('%d.%m.%Y %H:%M')} - {mailing.end_time.strftime('%d.%m.%Y %H:%M')}")

            # Проверка периода (если не force)
            if not force and not (mailing.start_time <= now <= mailing.end_time):
                self.stdout.write(
                    self.style.WARNING(f"   Рассылка вне периода отправки (пропускаем)")
                )
                continue

            # Проверка статуса
            if mailing.status != Mailing.STATUS_STARTED and not force:
                self.stdout.write(
                    self.style.WARNING(f"   Рассылка не в статусе 'Запущена' (пропускаем)")
                )
                continue

            clients = mailing.clients.all()
            self.stdout.write(f"   Клиентов: {clients.count()}")

            if dry_run:
                self.stdout.write(self.style.WARNING(f"   РЕЖИМ ПРОСМОТРА: будет отправлено {clients.count()} писем"))
                continue

            # Отправка писем
            mailing_sent = 0
            mailing_failed = 0

            for client in clients:
                try:
                    # Проверяем, не отправляли ли уже сегодня (защита от дублей)
                    today = timezone.now().date()
                    already_sent = MailingAttempt.objects.filter(
                        mailing=mailing,
                        client=client,
                        attempted_at__date=today,
                        status='success'
                    ).exists()

                    if already_sent:
                        self.stdout.write(f"     ⏭️ {client.email} - уже отправлено сегодня")
                        continue

                    if not dry_run:
                        send_mail(
                            subject=mailing.message.subject,
                            message=mailing.message.body,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[client.email],
                            fail_silently=False,
                        )

                    status = 'success'
                    response = 'OK'
                    mailing_sent += 1
                    total_sent += 1

                except Exception as e:
                    status = 'failed'
                    response = str(e)
                    mailing_failed += 1
                    total_failed += 1

                # Создаем запись о попытке (кроме dry-run)
                if not dry_run:
                    MailingAttempt.objects.create(
                        mailing=mailing,
                        client=client,
                        status=status,
                        server_response=response
                    )

            # Итог по рассылке
            self.stdout.write(f"   Результат: {mailing_sent} успешно, {mailing_failed} ошибок")

            # Обновляем статус рассылки если все клиенты обработаны
            if not dry_run and mailing_sent + mailing_failed > 0:
                mailing.update_status()

        # Общий итог
        self.stdout.write(f"\n{'=' * 60}")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"РЕЖИМ ПРОСМОТРА ЗАВЕРШЕН\n"
                f"   Будет отправлено: {total_sent} писем\n"
                f"   Будет ошибок: {total_failed}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"ОТПРАВКА ЗАВЕРШЕНА\n"
                f"   Успешно отправлено: {total_sent}\n"
                f"   Ошибок: {total_failed}"
            ))
        self.stdout.write(f"{'=' * 60}")