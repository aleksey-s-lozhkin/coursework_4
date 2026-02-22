from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('clients/', include('clients.urls')),
    path('mailings/', include('mailings.urls')),
    path('messages/', include('email_messages.urls')),
]
