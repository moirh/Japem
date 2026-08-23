from django.urls import path

from . import views

app_name = "iaps"

urlpatterns = [
    path("", views.iap_list, name="list"),
    path("nuevo/", views.iap_form, name="create"),
    path("<int:pk>/editar/", views.iap_form, name="update"),
    path("<int:pk>/eliminar/", views.iap_delete, name="delete"),
    path("<int:pk>/", views.iap_detail, name="detail"),
    path("importar/", views.iap_importar, name="importar"),
]
