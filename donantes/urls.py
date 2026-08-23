from django.urls import path

from . import views

app_name = "donantes"

urlpatterns = [
    path("", views.donante_list, name="list"),
    path("nuevo/", views.donante_form, name="create"),
    path("<int:pk>/editar/", views.donante_form, name="update"),
    path("<int:pk>/eliminar/", views.donante_delete, name="delete"),
]
