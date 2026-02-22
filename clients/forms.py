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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        # Проверяем, есть ли у текущего пользователя клиент с таким email
        if email and self.instance.pk:
            # При редактировании исключаем текущего клиента из проверки
            if Client.objects.filter(email=email, owner=self.instance.owner).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f'У вас уже есть клиент с email {email}')
        elif email and not self.instance.pk:
            # При создании проверяем наличие
            if Client.objects.filter(email=email, owner=self.initial.get('owner')).exists():
                raise ValidationError(f'У вас уже есть клиент с email {email}')

        return cleaned_data
