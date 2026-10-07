from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("agenda/", include("agenda.urls")),
    path("donantes/", include("donantes.urls")),
    path("donativos/", include("donativos.urls")),
    path("distribucion/", include("distribucion.urls")),
    path("iaps/", include("iaps.urls")),
]

# En desarrollo Django sirve las imágenes subidas; en producción las sirve el servidor web
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)