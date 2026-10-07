import csv
import io
import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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

# Importar CSV de Donantes (botón "Importar CSV" de DonantesTable.tsx)

COLUMNAS_CSV = [
    "razon_social", "rfc", "regimen_fiscal", "direccion", "cp",
    "contacto", "email", "telefono", "telefono_secundario", "estatus",
]
# Largo máximo de cada columna en la tabla `donantes`
LARGO_MAX = {"telefono_secundario": 20, "estatus": 20}


def _normalizar(texto):
    """'Razón Social' -> 'razon_social' (sin acentos, minúsculas, con _)."""
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return "_".join(texto.strip().lower().replace("-", " ").split())


def _normalizar_estatus(valor):
    v = _normalizar(valor)
    if v.startswith("perm"):
        return Donante.Estatus.PERMANENTE
    if v.startswith("unica") or v.startswith("una"):
        return Donante.Estatus.UNICA_VEZ
    return Donante.Estatus.EVENTUAL


def _leer_csv(archivo):
    """Lee el CSV aceptando UTF-8 o Latin-1 (Excel) y separador , o ;"""
    crudo = archivo.read()
    for codificacion in ("utf-8-sig", "latin-1"):
        try:
            texto = crudo.decode(codificacion)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialecto = csv.Sniffer().sniff(texto[:2048], delimiters=",;")
    except csv.Error:
        dialecto = csv.excel
    return list(csv.reader(io.StringIO(texto), dialecto))


@login_required
@require_POST
def donante_importar(request):
    """CSV con encabezados en la primera fila. Columnas (en cualquier orden):
    razon_social (obligatoria), rfc, regimen_fiscal, direccion, cp, contacto,
    email, telefono, telefono_secundario, estatus.
    Se omiten filas sin razón social y donantes que ya existen (mismo RFC o
    misma razón social), para no duplicar si se sube dos veces el archivo."""
    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para importar donantes.")
        return redirect("donantes:list")

    archivo = request.FILES.get("archivo")
    if not archivo or not archivo.name.lower().endswith(".csv"):
        messages.error(request, "Formato incorrecto. Por favor sube un archivo .CSV")
        return redirect("donantes:list")

    try:
        filas = _leer_csv(archivo)
    except Exception:
        messages.error(request, "No se pudo procesar el archivo.")
        return redirect("donantes:list")

    if len(filas) < 2:
        messages.error(request, "El archivo está vacío o solo tiene encabezados.")
        return redirect("donantes:list")

    encabezados = [_normalizar(h) for h in filas[0]]
    if "razon_social" not in encabezados:
        messages.error(
            request,
            "La primera fila debe tener los encabezados: " + ", ".join(COLUMNAS_CSV),
        )
        return redirect("donantes:list")
    indice = {col: encabezados.index(col) for col in COLUMNAS_CSV if col in encabezados}

    rfcs = set(Donante.objects.exclude(rfc__isnull=True).exclude(rfc="").values_list("rfc", flat=True))
    nombres = set(Donante.objects.values_list("razon_social", flat=True))

    creados, omitidos = 0, 0
    with transaction.atomic():
        for fila in filas[1:]:
            datos = {}
            for col, i in indice.items():
                valor = fila[i].strip() if i < len(fila) else ""
                datos[col] = valor[: LARGO_MAX.get(col, 255)]

            razon = datos.get("razon_social", "").upper()
            rfc = datos.get("rfc", "").upper()
            if not razon or razon in nombres or (rfc and rfc in rfcs):
                omitidos += 1
                continue

            Donante.objects.create(
                razon_social=razon,
                rfc=rfc or None,
                regimen_fiscal=datos.get("regimen_fiscal") or None,
                direccion=datos.get("direccion") or None,
                cp=datos.get("cp") or None,
                contacto=datos.get("contacto", ""),
                email=datos.get("email") or None,
                telefono=datos.get("telefono") or None,
                telefono_secundario=datos.get("telefono_secundario") or None,
                estatus=_normalizar_estatus(datos.get("estatus", "")),
            )
            nombres.add(razon)
            if rfc:
                rfcs.add(rfc)
            creados += 1

    texto = f"Se importaron {creados} donante{'s' if creados != 1 else ''} exitosamente."
    if omitidos:
        texto += f" Se omitieron {omitidos} (sin razón social o ya registrados)."
    messages.success(request, texto)
    return redirect("donantes:list")


@login_required
def donante_plantilla(request):
    """Descarga un CSV de ejemplo con los encabezados correctos."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="plantilla_donantes.csv"'
    response.write("\ufeff")  # BOM para que Excel respete los acentos
    escritor = csv.writer(response)
    escritor.writerow(COLUMNAS_CSV)
    escritor.writerow([
        "Empresa Ejemplo S.A. de C.V.", "EEJ010101AAA", "601 - General de Ley Personas Morales",
        "Av. Reforma 123, CDMX", "06600", "Juan Pérez", "contacto@ejemplo.com",
        "5555555555", "", "Eventual",
    ])
    return response