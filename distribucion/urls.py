from django.urls import path

from . import views

app_name = "distribucion"

urlpatterns = [
    path("", views.asignar_view, name="asignar"),
    path("sugerencias/<int:inventario_id>/", views.sugerencias_partial, name="sugerencias"),
    path("confirmar/", views.asignar_confirmar, name="asignar_confirmar"),
    path("entregas/", views.mesa_control, name="mesa_control"),
    path("entregas/<int:pk>/formulario/", views.entregar_form, name="entregar_form"),
    path("entregas/<int:pk>/confirmar/", views.entregar_confirmar, name="entregar_confirmar"),
    path("entregas/<int:pk>/detalle/", views.entrega_detalle, name="entrega_detalle"),
    path("entregas/<int:pk>/vale/", views.entrega_vale, name="entrega_vale"),
]
