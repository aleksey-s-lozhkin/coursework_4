from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'phone', 'country', 'is_email_verified', 'is_manager', 'is_staff', 'is_active')
    list_filter = ('is_email_verified', 'is_manager', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone', 'avatar', 'country')}),
        ('Email verification', {'fields': ('is_email_verified', 'email_verification_token', 'token_created_at')}),
        ('Roles', {'fields': ('is_manager',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'phone',
                    'country',
                    'is_manager',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)


admin.site.register(User, CustomUserAdmin)
