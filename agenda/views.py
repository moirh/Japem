from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.models import User

from .models import Acuerdo, Recordatorio


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
