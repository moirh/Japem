import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

ACCESO_DENEGADO = "No tienes permisos para acceder al directorio de usuarios."

from .forms import ChangePasswordForm, ProfileForm, UserForm
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        error = "Credenciales incorrectas. Verifique usuario y contraseña."

    return render(request, "accounts/login.html", {"error": error})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


def _can_view_users(user):
    return user.role in (User.Role.ADMIN, User.Role.SUPERADMIN)


def _can_manage_users(user):
    """Solo el superadmin puede crear o eliminar usuarios, igual que
    SettingsController (canCreateUser/canDeleteUser en el frontend)."""
    return user.role == User.Role.SUPERADMIN


@login_required
def profile_view(request):
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user)
        password_form = ChangePasswordForm(request.POST, user=request.user)
        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            new_password = password_form.cleaned_data.get("new_password")
            if new_password:
                request.user.set_password(new_password)
                request.user.save(update_fields=["password"])
                # Sin esto, cambiar la propia contraseña cerraría la sesión.
                update_session_auth_hash(request, request.user)
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("accounts:profile")
    else:
        profile_form = ProfileForm(instance=request.user)
        password_form = ChangePasswordForm(user=request.user)

    return render(
        request,
        "accounts/profile.html",
        {"profile_form": profile_form, "password_form": password_form},
    )


@login_required
def user_list(request):
    if not _can_view_users(request.user):
        messages.error(request, ACCESO_DENEGADO)
        return redirect("home")

    users = User.objects.order_by("id")
    return render(
        request,
        "accounts/user_list.html",
        {"users": users, "can_manage": _can_manage_users(request.user)},
    )


@login_required
def user_form(request, pk=None):
    if not _can_view_users(request.user):
        messages.error(request, ACCESO_DENEGADO)
        return redirect("home")

    user_obj = get_object_or_404(User, pk=pk) if pk else None

    if not user_obj and not _can_manage_users(request.user):
        messages.error(request, "Solo el superadmin puede crear usuarios.")
        return redirect("accounts:user_list")

    if request.method == "POST":
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            users = User.objects.order_by("id")
            response = render(
                request,
                "accounts/_user_table.html",
                {"users": users, "can_manage": _can_manage_users(request.user)},
            )
            response["HX-Trigger"] = "closeModal"
            return response
    else:
        form = UserForm(instance=user_obj)

    return render(request, "accounts/_user_form.html", {"form": form, "user_obj": user_obj})


@login_required
@user_passes_test(_can_view_users)
@require_POST
def user_delete(request, pk):
    # Igual que SettingsController@deleteUser: solo superadmin, y nadie
    # puede eliminarse a sí mismo. El botón ya está oculto en esos casos;
    # esto es defensa en profundidad.
    if _can_manage_users(request.user) and request.user.pk != pk:
        get_object_or_404(User, pk=pk).delete()

    users = User.objects.order_by("id")
    return render(
        request,
        "accounts/_user_table.html",
        {"users": users, "can_manage": _can_manage_users(request.user)},
    )

# =====================================================================
# Configuración del Sistema (modal del engrane) — migrado de SettingsModal.tsx
# =====================================================================

def _con_alerta(response, titulo, texto=""):
    """Muestra el SweetAlert de éxito del base.html (HX-Trigger alertaExito)."""
    response["HX-Trigger"] = json.dumps({"alertaExito": {"titulo": titulo, "texto": texto}})
    return response


def _render_perfil(request, profile_form=None, password_form=None):
    return render(request, "accounts/_settings_perfil.html", {
        "profile_form": profile_form or ProfileForm(instance=request.user),
        "password_form": password_form or ChangePasswordForm(user=request.user),
    })


def _render_usuarios(request, form=None, user_obj=None):
    return render(request, "accounts/_settings_usuarios.html", {
        "users": User.objects.order_by("id"),
        "can_manage": _can_manage_users(request.user),
        "form": form,
        "user_obj": user_obj,
    })


@login_required
def settings_modal(request):
    if not request.htmx:
        return redirect("accounts:profile")
    return render(request, "accounts/_settings.html", {
        "profile_form": ProfileForm(instance=request.user),
        "password_form": ChangePasswordForm(user=request.user),
        "can_view_users": _can_view_users(request.user),
    })


@login_required
def settings_perfil(request):
    if not request.htmx:
        return redirect("accounts:profile")

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user)
        password_form = ChangePasswordForm(request.POST, user=request.user)
        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            new_password = password_form.cleaned_data.get("new_password")
            if new_password:
                request.user.set_password(new_password)
                request.user.save(update_fields=["password"])
                update_session_auth_hash(request, request.user)
            return _con_alerta(
                _render_perfil(request),
                "¡Perfil Actualizado!",
                "Tus datos se han guardado correctamente.",
            )
        return _render_perfil(request, profile_form, password_form)

    return _render_perfil(request)


@login_required
def settings_usuarios(request):
    if not request.htmx:
        return redirect("accounts:user_list")
    if not _can_view_users(request.user):
        return _render_perfil(request)
    return _render_usuarios(request)


@login_required
def settings_user_form(request, pk=None):
    if not request.htmx:
        return redirect("accounts:user_list")
    if not _can_view_users(request.user):
        return _render_perfil(request)

    user_obj = get_object_or_404(User, pk=pk) if pk else None
    if not user_obj and not _can_manage_users(request.user):
        # Solo el superadmin puede crear usuarios
        return _render_usuarios(request)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            titulo = "¡Usuario Actualizado!" if user_obj else "¡Usuario Creado!"
            return _con_alerta(_render_usuarios(request), titulo)
    else:
        form = UserForm(instance=user_obj)

    return _render_usuarios(request, form=form, user_obj=user_obj)


@login_required
@require_POST
def settings_user_delete(request, pk):
    if not request.htmx:
        return redirect("accounts:user_list")
    # Solo superadmin, y nadie puede eliminarse a sí mismo
    if _can_manage_users(request.user) and request.user.pk != pk:
        get_object_or_404(User, pk=pk).delete()
        return _con_alerta(_render_usuarios(request), "Eliminado")
    return _render_usuarios(request)
