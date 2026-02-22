from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 999-99-99'}),
        label='Телефон'
    )
    country = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Выберите страну'),
            ('RU', 'Россия'),
            ('BY', 'Беларусь'),
            ('KZ', 'Казахстан'),
            ('UA', 'Украина'),
            ('AM', 'Армения'),
            ('GE', 'Грузия'),
            ('other', 'Другая'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Страна'
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('email', 'phone', 'country', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone = self.cleaned_data.get('phone', '')
        user.country = self.cleaned_data.get('country', '')
        user.is_email_verified = False
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Форма входа в систему"""
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )


class UserUpdateForm(forms.ModelForm):
    """Форма для обновления данных пользователя (без email)"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'country']  # email убрали
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите фамилию'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 999-99-99'
            }),
            'country': forms.Select(attrs={'class': 'form-control'}),
        }