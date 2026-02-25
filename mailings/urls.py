from django.urls import path

from . import views

app_name = 'mailings'

urlpatterns = [
    path('', views.MailingListView.as_view(), name='list'),
    path('<int:pk>/', views.MailingDetailView.as_view(), name='detail'),
    path('create/', views.MailingCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.MailingUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MailingDeleteView.as_view(), name='delete'),
    path('<int:pk>/disable/', views.MailingDisableView.as_view(), name='disable'),
    path('<int:pk>/stats/', views.MailingStatsView.as_view(), name='stats'),
    path('<int:pk>/send/', views.MailingSendView.as_view(), name='send'),
    path('stats/', views.MailingStatsListView.as_view(), name='stats_list'),
]
