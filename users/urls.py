from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Корень
    path('', views.RootRedirectView.as_view(), name='root'),
    # Главная
    path('home/', views.HomeView.as_view(), name='home'),

    # Профиль пользователя
    path('profile/', views.ProfileView.as_view(), name='profile'),  # ДОБАВЛЕНО!
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),

    # Аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),

    # Сброс пароля
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'password-reset/<uidb64>/<token>/',
        views.CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Управление пользователями (для менеджеров)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/block/', views.UserBlockView.as_view(), name='user_block'),
]