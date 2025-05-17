from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('account/', include('account.urls')),  # Autentifikatsiya va profil
    path('', include('roulette.urls')),  # O‘yin funksiyalari
]