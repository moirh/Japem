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

        # Configuración del Sistema (modal del engrane)
    path("configuracion/", views.settings_modal, name="settings"),
    path("configuracion/perfil/", views.settings_perfil, name="settings_perfil"),
    path("configuracion/usuarios/", views.settings_usuarios, name="settings_usuarios"),
    path("configuracion/usuarios/nuevo/", views.settings_user_form, name="settings_user_create"),
    path("configuracion/usuarios/<int:pk>/editar/", views.settings_user_form, name="settings_user_update"),
    path("configuracion/usuarios/<int:pk>/eliminar/", views.settings_user_delete, name="settings_user_delete"),
]
