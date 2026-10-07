import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import can_edit_iaps

from .forms import IapForm
from .models import SEPARATOR, Iap


@login_required
def iap_list(request):
    iaps = Iap.objects.all()
    return render(
        request, "iaps/list.html", {"iaps": iaps, "can_edit": can_edit_iaps(request.user)}
    )


@login_required
def iap_form(request, pk=None):
    can_edit = can_edit_iaps(request.user)
    iap = get_object_or_404(Iap, pk=pk) if pk else None

    if request.method == "POST" and can_edit:
        form = IapForm(request.POST, instance=iap)
        if form.is_valid():
            form.save()
            iaps = Iap.objects.all()
            response = render(
                request, "iaps/_table.html", {"iaps": iaps, "can_edit": can_edit}
            )
            response["HX-Trigger"] = "closeModal"
            return response
    else:
        form = IapForm(instance=iap)

    if not can_edit:
        iaps = Iap.objects.all()
        return render(request, "iaps/_table.html", {"iaps": iaps, "can_edit": can_edit})

    return render(request, "iaps/_form.html", {"form": form, "iap": iap})


@login_required
def iap_delete(request, pk):
    can_edit = can_edit_iaps(request.user)
    if can_edit and request.method == "POST":
        get_object_or_404(Iap, pk=pk).delete()

    iaps = Iap.objects.all()
    return render(request, "iaps/_table.html", {"iaps": iaps, "can_edit": can_edit})


@login_required
def iap_detail(request, pk):
    iap = get_object_or_404(Iap, pk=pk)
    if request.htmx:
        # Ficha Técnica en modal (igual que el "Ver Detalles" de IapTable.tsx)
        tipos = [t.strip() for t in (iap.tipo_beneficiario or "").split(SEPARATOR) if t.strip()]
        return render(request, "iaps/_detail.html", {"iap": iap, "tipos_beneficiario": tipos})
    return render(request, "iaps/detail.html", {"iap": iap})


@login_required
@require_POST
def iap_importar(request):
    """Equivalente a IapController@importar: CSV con columnas
    nombre, estatus, rubro, clasificación, actividad, tipo_beneficiario,
    personas_beneficiadas, necesidad_complementaria, certificada,
    donataria, padrón (en ese orden, sin encabezado en la primera fila
    usable)."""
    if not can_edit_iaps(request.user):
        messages.error(request, "No tienes permisos para importar IAPs.")
        return redirect("iaps:list")

    archivo = request.FILES.get("archivo")
    if not archivo or not archivo.name.lower().endswith(".csv"):
        messages.error(request, "Por favor sube un archivo .csv")
        return redirect("iaps:list")

    try:
        decoded = io.TextIOWrapper(archivo.file, encoding="utf-8-sig", errors="replace")
        filas = list(csv.reader(decoded))
    except Exception as exc:
        messages.error(request, f"Error al leer el archivo: {exc}")
        return redirect("iaps:list")

    if not filas:
        messages.error(request, "El archivo está vacío.")
        return redirect("iaps:list")

    filas = filas[1:]  # descartar encabezados

    def valor(fila, indice, default=""):
        if indice < len(fila) and fila[indice] is not None:
            return fila[indice].strip()
        return default

    creadas = 0
    for fila in filas:
        if len(fila) < 3:
            continue

        personas_raw = valor(fila, 6, "0")
        Iap.objects.create(
            nombre_iap=valor(fila, 0),
            estatus=valor(fila, 1, "Activa") or "Activa",
            rubro=valor(fila, 2, "Salud") or "Salud",
            clasificacion=valor(fila, 3),
            actividad_asistencial=valor(fila, 4),
            tipo_beneficiario=valor(fila, 5),
            personas_beneficiadas=int(personas_raw) if personas_raw.isdigit() else 0,
            necesidad_complementaria=valor(fila, 7),
            es_certificada=valor(fila, 8, "0") == "1",
            tiene_donataria_autorizada=valor(fila, 9, "0") == "1",
            tiene_padron_beneficiarios=valor(fila, 10, "0") == "1",
            veces_donado=0,
        )
        creadas += 1

    messages.success(request, f"Se importaron {creadas} instituciones exitosamente.")
    return redirect("iaps:list")
