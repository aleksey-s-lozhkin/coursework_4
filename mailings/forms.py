from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from clients.models import Client
from email_messages.models import EmailMessage
from .models import Mailing


class MailingForm(forms.ModelForm):
    """Форма для создания/редактирования рассылки"""

    class Meta:
        model = Mailing
        fields = ('name', 'message', 'clients', 'frequency', 'start_time', 'end_time')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название рассылки'
            }),
            'message': forms.Select(attrs={
                'class': 'form-select',
            }),
            'clients': forms.CheckboxSelectMultiple(),
            'frequency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
        }
        labels = {
            'name': 'Название рассылки',
            'message': 'Сообщение',
            'clients': 'Получатели',
            'frequency': 'Периодичность',
            'start_time': 'Дата и время начала',
            'end_time': 'Дата и время окончания',
        }
        help_texts = {
            'name': 'Укажите название для идентификации рассылки',
            'clients': 'Отметьте клиентов, которые получат это письмо',
            'frequency': 'Как часто отправлять рассылку',
            'start_time': 'Формат: ГГГГ-ММ-ДД ЧЧ:ММ. Не может быть в прошлом.',
            'end_time': 'Формат: ГГГГ-ММ-ДД ЧЧ:ММ. Должно быть позже даты начала.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['clients'].queryset = Client.objects.filter(owner=user)
            self.fields['message'].queryset = EmailMessage.objects.filter(owner=user)

        self.fields['frequency'].empty_label = "Выберите периодичность"

    def clean_start_time(self):
        """Валидация: start_time не может быть в прошлом"""
        start_time = self.cleaned_data.get('start_time')

        if start_time:
            if self.instance.pk:
                if start_time != self.instance.start_time and start_time < timezone.now():
                    raise ValidationError('Дата начала не может быть в прошлом.')
            else:
                if start_time < timezone.now():
                    raise ValidationError('Дата начала не может быть в прошлом.')

        return start_time

    def clean(self):
        """Валидация: start_time должен быть раньше end_time"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Дата окончания должна быть позже даты начала.')

        return cleaned_data