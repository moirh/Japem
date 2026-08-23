from django.urls import path

from . import views

app_name = "donativos"

urlpatterns = [
    path("", views.donativo_list, name="list"),
    path("nuevo/", views.donativo_create, name="crear"),
    path("inventario/", views.inventario_list, name="inventario"),
    path("<int:pk>/", views.donativo_detail, name="detalle"),
    path("<int:pk>/precios/", views.donativo_update_precios, name="actualizar_precios"),
    path("items/<int:pk>/devolver/", views.inventario_item_devolver, name="devolver_item"),
]
