from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error, permission_denied, bad_request

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('', include('roulette.urls')),
]

# Media fayllarni xizmat qilish
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Xato handlerlari
handler404 = page_not_found  # 404 xatosi
handler500 = server_error    # 500 xatosi
handler403 = permission_denied  # 403 xatosi
handler400 = bad_request      # 400 xatosi