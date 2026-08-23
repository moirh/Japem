from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from accounts.permissions import can_edit_donativos

from .forms import DonanteForm
from .models import Donante


@login_required
def donante_list(request):
    donantes = Donante.objects.all()
    return render(
        request,
        "donantes/list.html",
        {"donantes": donantes, "can_edit": can_edit_donativos(request.user)},
    )


@login_required
def donante_form(request, pk=None):
    can_edit = can_edit_donativos(request.user)
    donante = get_object_or_404(Donante, pk=pk) if pk else None

    if request.method == "POST" and can_edit:
        form = DonanteForm(request.POST, instance=donante)
        if form.is_valid():
            form.save()
            donantes = Donante.objects.all()
            response = render(
                request, "donantes/_table.html", {"donantes": donantes, "can_edit": can_edit}
            )
            response["HX-Trigger"] = "closeModal"
            return response
    else:
        form = DonanteForm(instance=donante)

    if not can_edit:
        donantes = Donante.objects.all()
        return render(
            request, "donantes/_table.html", {"donantes": donantes, "can_edit": can_edit}
        )

    return render(request, "donantes/_form.html", {"form": form, "donante": donante})


@login_required
def donante_delete(request, pk):
    can_edit = can_edit_donativos(request.user)
    if can_edit and request.method == "POST":
        get_object_or_404(Donante, pk=pk).delete()

    donantes = Donante.objects.all()
    return render(
        request, "donantes/_table.html", {"donantes": donantes, "can_edit": can_edit}
    )
