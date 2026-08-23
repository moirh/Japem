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
