from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('account/', include('account.urls')),  # Autentifikatsiya va profil
    path('', include('roulette.urls')),  # O‘yin funksiyalari
]


# Faqat DEBUG True holatda static va media fayllarni server qilish uchun
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

