from django.urls import path

from . import views

app_name = "agenda"

urlpatterns = [
    path("acuerdos/nuevo/", views.acuerdo_create, name="acuerdo_create"),
    path("acuerdos/<int:pk>/completar/", views.acuerdo_toggle, name="acuerdo_toggle"),
    path("acuerdos/<int:pk>/eliminar/", views.acuerdo_delete, name="acuerdo_delete"),
    path("recordatorios/nuevo/", views.recordatorio_create, name="recordatorio_create"),
    path("recordatorios/<int:pk>/completar/", views.recordatorio_toggle, name="recordatorio_toggle"),
    path("recordatorios/<int:pk>/eliminar/", views.recordatorio_delete, name="recordatorio_delete"),
    path("avisos/nuevo/", views.aviso_form, name="aviso_create"),
    path("avisos/<int:pk>/editar/", views.aviso_form, name="aviso_update"),
    path("avisos/<int:pk>/eliminar/", views.aviso_delete, name="aviso_delete"),
]
