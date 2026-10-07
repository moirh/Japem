from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import can_edit_donativos
from donativos.models import Inventario

from .models import Asignacion, DetalleAsignacion
from .services import sugerir_iaps
from .vale import generar_vale_pdf


@login_required
def asignar_view(request):
    """Pantalla de distribución: elegir un lote de inventario y ver las IAPs
    sugeridas para recibirlo. Equivalente a EntregasView.tsx.

    A diferencia del frontend original (que operaba sobre el resumen
    agrupado por producto), aquí se trabaja directamente sobre lotes
    individuales de Inventario: es el nivel al que en realidad apunta
    DetalleAsignacion.inventario_id y al que se le descuenta cantidad_actual,
    así que evita la ambigüedad que tenía la pantalla original (ver README).
    """
    lotes = (
        Inventario.objects.filter(cantidad_actual__gt=0)
        .select_related("catalogo_producto")
        .order_by("categoria_producto", "nombre_producto")
    )

    grupos = {}
    for lote in lotes:
        grupos.setdefault(lote.categoria_producto or "Otros", []).append(lote)

    return render(
        request,
        "distribucion/asignar.html",
        {"grupos": dict(sorted(grupos.items())), "can_edit": can_edit_donativos(request.user)},
    )


@login_required
def sugerencias_partial(request, inventario_id):
    item = get_object_or_404(Inventario, pk=inventario_id)
    sugerencias = sugerir_iaps(item)
    return render(
        request,
        "distribucion/_sugerencias.html",
        {"item": item, "sugerencias": sugerencias, "can_edit": can_edit_donativos(request.user)},
    )


@login_required
@require_POST
def asignar_confirmar(request):
    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para asignar entregas.")
        return redirect("distribucion:asignar")

    inventario_id = request.POST.get("inventario_id")
    iap_id = request.POST.get("iap_id")
    cantidad_raw = request.POST.get("cantidad", "0")

    inventario = get_object_or_404(Inventario, pk=inventario_id)

    try:
        cantidad = int(cantidad_raw)
    except ValueError:
        cantidad = 0

    if cantidad <= 0:
        messages.error(request, "Ingresa una cantidad mayor a 0.")
    elif cantidad > inventario.cantidad_actual:
        messages.error(
            request,
            f"Stock insuficiente para '{inventario.nombre_producto}'. "
            f"Disponible: {inventario.cantidad_actual}.",
        )
    else:
        with transaction.atomic():
            asignacion = Asignacion.objects.create(
                iap_id=iap_id, fecha_asignacion=timezone.now()
            )
            DetalleAsignacion.objects.create(
                asignacion=asignacion, inventario=inventario, cantidad=cantidad
            )
        messages.success(
            request,
            f"Se asignaron {cantidad} unidades de {inventario.nombre_producto}. "
            "Queda pendiente de entrega física en la Mesa de Control.",
        )

    return redirect("distribucion:asignar")


@login_required
def mesa_control(request):
    """Historial de asignaciones (pendientes + entregadas). Equivalente a
    EntregaController@historial, aplanado por renglón de detalle."""
    asignaciones = (
        Asignacion.objects.select_related("iap")
        .prefetch_related("detalles__inventario")
        .all()
    )
    filas = [
        {"asignacion": asignacion, "detalle": detalle}
        for asignacion in asignaciones
        for detalle in asignacion.detalles.all()
    ]
    return render(
        request,
        "distribucion/mesa_control.html",
        {"filas": filas, "can_edit": can_edit_donativos(request.user)},
    )


@login_required
def entregar_form(request, pk):
    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para confirmar entregas.")
        return redirect("distribucion:mesa_control")

    asignacion = get_object_or_404(Asignacion.objects.select_related("iap"), pk=pk)
    return render(
        request, "distribucion/_entregar_form.html", {"asignacion": asignacion}
    )


@login_required
@require_POST
def entregar_confirmar(request, pk):
    """Confirma la salida física de almacén: descuenta cantidad_actual de
    cada lote, marca la asignación como entregada y suma el contador de la
    IAP. Equivalente a EntregaController@procesarEntrega."""
    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para confirmar entregas.")
        return redirect("distribucion:mesa_control")

    responsable = request.POST.get("responsable_entrega", "").strip()
    lugar = request.POST.get("lugar_entrega", "").strip()

    if not responsable or not lugar:
        messages.error(request, "Selecciona responsable y lugar de entrega.")
        return redirect("distribucion:mesa_control")

    asignacion = get_object_or_404(Asignacion, pk=pk)

    if asignacion.estatus == Asignacion.Estatus.ENTREGADO:
        messages.error(request, "Esta asignación ya fue entregada anteriormente.")
        return redirect("distribucion:mesa_control")

    detalles = list(asignacion.detalles.select_related("inventario"))
    if not detalles:
        messages.error(request, "La asignación no tiene detalles de productos.")
        return redirect("distribucion:mesa_control")

    for detalle in detalles:
        if detalle.inventario.cantidad_actual < detalle.cantidad:
            messages.error(
                request,
                f"Stock insuficiente para {detalle.inventario.nombre_producto}. "
                f"Quedan: {detalle.inventario.cantidad_actual}.",
            )
            return redirect("distribucion:mesa_control")

    with transaction.atomic():
        for detalle in detalles:
            Inventario.objects.filter(pk=detalle.inventario_id).update(
                cantidad_actual=F("cantidad_actual") - detalle.cantidad
            )
            detalle.estatus = "entregado"
            detalle.fecha_entrega = timezone.now()
            detalle.save(update_fields=["estatus", "fecha_entrega"])

        asignacion.estatus = Asignacion.Estatus.ENTREGADO
        asignacion.responsable_entrega = responsable
        asignacion.lugar_entrega = lugar
        asignacion.fecha_entrega_real = timezone.now()
        asignacion.save(
            update_fields=[
                "estatus",
                "responsable_entrega",
                "lugar_entrega",
                "fecha_entrega_real",
            ]
        )

        asignacion.iap.veces_donado = F("veces_donado") + 1
        asignacion.iap.save(update_fields=["veces_donado"])

    messages.success(request, "Entrega confirmada. Inventario actualizado.")
    return redirect("distribucion:mesa_control")

@login_required
def entrega_detalle(request, pk):
    """Modal "Detalles de Entrega" (botón Ver Detalles de Entrega.tsx)."""
    if not request.htmx:
        return redirect("distribucion:mesa_control")
    asignacion = get_object_or_404(Asignacion.objects.select_related("iap"), pk=pk)
    return render(request, "distribucion/_entrega_detalle.html", {"asignacion": asignacion})


@login_required
def entrega_vale(request, pk):
    """Vale de Salida de Almacén en PDF (botón "Vale" de Entrega.tsx)."""
    asignacion = get_object_or_404(Asignacion.objects.select_related("iap"), pk=pk)
    if asignacion.estatus == Asignacion.Estatus.PENDIENTE:
        messages.error(request, "El vale solo está disponible para entregas confirmadas.")
        return redirect("distribucion:mesa_control")

    response = HttpResponse(generar_vale_pdf(asignacion), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="vale_entrega_{asignacion.pk:06d}.pdf"'
    return response
