import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import can_publish_avisos

from .forms import AvisoForm
from .models import Acuerdo, Aviso, Recordatorio


@login_required
@require_POST
def acuerdo_create(request):
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    date = request.POST.get("date")
    shared_with = request.POST.getlist("shared_with")

    if not (title and description and date):
        messages.error(request, "Completa título, descripción y fecha para el acuerdo.")
        return redirect("home")

    acuerdo = Acuerdo.objects.create(
        user=request.user, title=title, description=description, date=date
    )
    if shared_with:
        acuerdo.compartidos.set(User.objects.filter(pk__in=shared_with))

    messages.success(request, "Acuerdo registrado.")
    return redirect("home")


@login_required
@require_POST
def acuerdo_toggle(request, pk):
    # Igual que AcuerdoController@update con done=true: marcarlo como hecho
    # lo elimina, no solo lo oculta.
    acuerdo = get_object_or_404(Acuerdo, pk=pk, user=request.user)
    acuerdo.delete()
    messages.success(request, "Acuerdo completado.")
    return redirect("home")


@login_required
@require_POST
def acuerdo_delete(request, pk):
    acuerdo = get_object_or_404(Acuerdo, pk=pk, user=request.user)
    acuerdo.delete()
    messages.success(request, "Acuerdo eliminado.")
    return redirect("home")


@login_required
@require_POST
def recordatorio_create(request):
    title = request.POST.get("title", "").strip()
    date = request.POST.get("date")

    if not (title and date):
        messages.error(request, "Completa título y fecha para el recordatorio.")
        return redirect("home")

    Recordatorio.objects.create(user=request.user, title=title, date=date)
    messages.success(request, "Recordatorio registrado.")
    return redirect("home")


@login_required
@require_POST
def recordatorio_toggle(request, pk):
    recordatorio = get_object_or_404(Recordatorio, pk=pk, user=request.user)
    recordatorio.delete()
    messages.success(request, "Recordatorio completado.")
    return redirect("home")


@login_required
@require_POST
def recordatorio_delete(request, pk):
    recordatorio = get_object_or_404(Recordatorio, pk=pk, user=request.user)
    recordatorio.delete()
    messages.success(request, "Recordatorio eliminado.")
    return redirect("home")

# Avisos de la Semana (card del Inicio que reemplaza al slider)

def _render_avisos(request, titulo=None):
    """Devuelve la card de avisos; con `titulo` cierra el modal y muestra la alerta."""
    response = render(request, "agenda/_avisos.html", {
        "avisos": Aviso.objects.select_related("autor")[:5],
        "puede_publicar_avisos": can_publish_avisos(request.user),
    })
    if titulo:
        response["HX-Trigger"] = json.dumps({
            "closeModal": True,
            "alertaExito": {"titulo": titulo, "texto": ""},
        })
    return response


@login_required
def aviso_form(request, pk=None):
    if not request.htmx:
        return redirect("home")
    if not can_publish_avisos(request.user):
        return HttpResponseForbidden("Solo admin y superadmin pueden publicar avisos.")

    aviso = get_object_or_404(Aviso, pk=pk) if pk else None
    imagen_anterior = aviso.imagen.name if aviso and aviso.imagen else None

    if request.method == "POST":
        form = AvisoForm(request.POST, request.FILES, instance=aviso)
        if form.is_valid():
            nuevo = form.save(commit=False)
            if not aviso:
                nuevo.autor = request.user
            if form.cleaned_data.get("quitar_imagen") and "imagen" not in request.FILES:
                nuevo.imagen = None
            nuevo.save()
            # Borra del disco la imagen anterior si se cambió o se quitó
            if imagen_anterior and imagen_anterior != (nuevo.imagen.name if nuevo.imagen else None):
                default_storage.delete(imagen_anterior)
            return _render_avisos(request, "¡Aviso actualizado!" if aviso else "¡Aviso publicado!")
    else:
        form = AvisoForm(instance=aviso)

    return render(request, "agenda/_aviso_form.html", {"form": form, "aviso": aviso})


@login_required
@require_POST
def aviso_delete(request, pk):
    if not can_publish_avisos(request.user):
        return HttpResponseForbidden("Solo admin y superadmin pueden eliminar avisos.")
    aviso = get_object_or_404(Aviso, pk=pk)
    if aviso.imagen:
        aviso.imagen.delete(save=False)
    aviso.delete()
    return _render_avisos(request, "Aviso eliminado")