from django.core.exceptions import ValidationError
from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    """Форма для создания/редактирования клиента"""

    class Meta:
        model = Client
        fields = ('email', 'full_name', 'comment')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_email(self):
        """Очистка и валидация email"""
        email = self.cleaned_data.get('email')
        if email:
            # Приводим email к нижнему регистру
            email = email.lower().strip()
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        if email:
            # Получаем владельца
            if self.instance.pk:
                owner = self.instance.owner
            else:
                owner = self.initial.get('owner')

            if owner:
                # Проверяем существование клиента с таким email
                existing = Client.objects.filter(
                    email__iexact=email,
                    owner=owner
                )

                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)

                if existing.exists():
                    raise ValidationError(f'У вас уже есть клиент с email {email}')

        return cleaned_data