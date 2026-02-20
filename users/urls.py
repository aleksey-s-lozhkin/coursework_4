from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Корень
    path('', views.RootRedirectView.as_view(), name='root'),

    # Главная
    path('home/', views.HomeView.as_view(), name='home'),

    # Аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),

    # Восстановление пароля
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]