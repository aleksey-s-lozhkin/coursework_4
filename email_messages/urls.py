from django.urls import path

from . import views

app_name = 'email_messages'

urlpatterns = [
    path('', views.EmailMessageListView.as_view(), name='list'),
    path('<int:pk>/', views.EmailMessageDetailView.as_view(), name='detail'),
    path('create/', views.EmailMessageCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.EmailMessageUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.EmailMessageDeleteView.as_view(), name='delete'),
]
