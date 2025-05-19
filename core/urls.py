from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('account/', include('account.urls')),  # Autentifikatsiya va profil
    path('', include('roulette.urls')),  # O‘yin funksiyalari
]


