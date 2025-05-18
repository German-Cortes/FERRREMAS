from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static  # ✅ necesario para servir archivos media en desarrollo

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalogo.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# ✅ Esta línea permite servir imágenes desde /media/ en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
