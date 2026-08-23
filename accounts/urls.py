from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("perfil/", views.profile_view, name="profile"),
    path("usuarios/", views.user_list, name="user_list"),
    path("usuarios/nuevo/", views.user_form, name="user_create"),
    path("usuarios/<int:pk>/editar/", views.user_form, name="user_update"),
    path("usuarios/<int:pk>/eliminar/", views.user_delete, name="user_delete"),
]
