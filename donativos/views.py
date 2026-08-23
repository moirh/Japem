from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import can_edit_donativos

from .forms import DetalleFormSet, DonativoForm
from .models import CatalogoProducto, Donativo, Inventario


@login_required
def donativo_list(request):
    donativos = (
        Donativo.objects.select_related("donante")
        .prefetch_related("inventarios")
        .all()
    )
    return render(
        request,
        "donativos/donativo_list.html",
        {"donativos": donativos, "can_edit": can_edit_donativos(request.user)},
    )


def _guardar_donativo(cabecera, detalles):
    """Equivalente a DonativoController@store: crea el donativo y sus renglones
    de inventario dentro de una transacción, dando de alta productos nuevos
    en el catálogo cuando no existen todavía."""
    with transaction.atomic():
        donativo = Donativo.objects.create(
            donante=cabecera["donante"],
            fecha_donativo=cabecera["fecha_donativo"],
            observaciones=cabecera.get("observaciones") or "",
        )

        total_deducible = Decimal("0")

        for detalle in detalles:
            nombre = detalle["nombre_producto"].strip().upper()
            cantidad = detalle["cantidad"]
            precio_deducible = detalle.get("precio_unitario_deducible") or Decimal("0")
            precio_venta = detalle.get("precio_venta_unitario") or Decimal("0")
            subtotal_deducible = cantidad * precio_deducible
            total_deducible += subtotal_deducible

            catalogo, _creado = CatalogoProducto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "categoria": detalle["categoria_producto"],
                    "clave_sat": detalle.get("clave_sat") or "01010101",
                    "unidad_medida": detalle["clave_unidad"],
                    "precio_referencia": precio_deducible,
                },
            )

            Inventario.objects.create(
                donativo=donativo,
                catalogo_producto=catalogo,
                nombre_producto=nombre,
                categoria_producto=catalogo.categoria or detalle["categoria_producto"],
                clave_sat=detalle.get("clave_sat") or "01010101",
                estado=detalle["estado"],
                modalidad=detalle.get("modalidad") or "",
                clave_unidad=catalogo.unidad_medida or detalle["clave_unidad"],
                fecha_caducidad=detalle.get("fecha_caducidad"),
                cantidad=cantidad,
                cantidad_actual=cantidad,
                precio_unitario_deducible=precio_deducible,
                monto_deducible_total=subtotal_deducible,
                precio_venta_unitario=precio_venta,
                precio_venta_total=cantidad * precio_venta,
            )

        donativo.monto_total_deducible = total_deducible
        donativo.save(update_fields=["monto_total_deducible"])

    return donativo


@login_required
def donativo_create(request):
    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para registrar donativos.")
        return redirect("donativos:list")

    if request.method == "POST":
        form = DonativoForm(request.POST)
        formset = DetalleFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            detalles = [f.cleaned_data for f in formset if f.cleaned_data]
            if not detalles:
                messages.error(request, "Debes agregar al menos un producto.")
            else:
                donativo = _guardar_donativo(form.cleaned_data, detalles)
                messages.success(request, "La entrada se registró correctamente.")
                return redirect("donativos:detalle", pk=donativo.pk)
    else:
        form = DonativoForm(initial={"fecha_donativo": timezone.now().date()})
        formset = DetalleFormSet()

    catalogo = CatalogoProducto.objects.all().order_by("nombre")
    return render(
        request,
        "donativos/donativo_form.html",
        {"form": form, "formset": formset, "catalogo": catalogo},
    )


@login_required
def donativo_detail(request, pk):
    donativo = get_object_or_404(
        Donativo.objects.select_related("donante").prefetch_related("inventarios"),
        pk=pk,
    )
    return render(
        request,
        "donativos/donativo_detail.html",
        {"donativo": donativo, "can_edit": can_edit_donativos(request.user)},
    )


@login_required
@require_POST
def donativo_update_precios(request, pk):
    """Equivalente a InventarioController@updatePrices, acotado a los renglones
    de un donativo específico (que es como lo usa la pantalla de detalle)."""
    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para actualizar precios.")
        return redirect("donativos:detalle", pk=pk)

    donativo = get_object_or_404(Donativo, pk=pk)
    for item in donativo.inventarios.all():
        campo = f"precio_venta_unitario_{item.pk}"
        if campo not in request.POST:
            continue
        valor = request.POST.get(campo) or "0"
        try:
            precio = Decimal(valor)
        except Exception:
            continue
        item.precio_venta_unitario = precio
        item.precio_venta_total = item.cantidad_actual * precio
        item.save(update_fields=["precio_venta_unitario", "precio_venta_total"])

    messages.success(request, "Precios de recuperación actualizados correctamente.")
    return redirect("donativos:detalle", pk=pk)


@login_required
@require_POST
def inventario_item_devolver(request, pk):
    """Retira unidades de un lote por daño/devolución, restando de
    cantidad_actual (el stock vivo que consume Inventario)."""
    item = get_object_or_404(Inventario, pk=pk)

    if not can_edit_donativos(request.user):
        messages.error(request, "No tienes permisos para registrar devoluciones.")
        return redirect("donativos:detalle", pk=item.donativo_id)

    try:
        cantidad = int(request.POST.get("cantidad", 0))
    except ValueError:
        cantidad = 0

    if cantidad <= 0 or cantidad > item.cantidad_actual:
        messages.error(request, "Cantidad inválida para la devolución.")
    else:
        item.cantidad_actual -= cantidad
        item.save(update_fields=["cantidad_actual"])
        messages.success(
            request, f"Se retiraron {cantidad} unidades de {item.nombre_producto}."
        )

    return redirect("donativos:detalle", pk=item.donativo_id)


@login_required
def inventario_list(request):
    """Resumen de stock agrupado por producto, equivalente a
    InventarioController@index del backend Laravel."""
    search = request.GET.get("search", "").strip()

    qs = Inventario.objects.annotate(
        nombre=Coalesce("catalogo_producto__nombre", "nombre_producto"),
    )

    if search:
        qs = qs.filter(
            Q(catalogo_producto__nombre__icontains=search)
            | Q(nombre_producto__icontains=search)
        )

    resumen = (
        qs.values("nombre")
        .annotate(
            categoria_producto=Max("catalogo_producto__categoria"),
            unidad_medida=Max("catalogo_producto__unidad_medida"),
            estado=Max("estado"),
            fecha_caducidad=Min("fecha_caducidad"),
            cantidad_actual=Sum("cantidad_actual"),
            precio_total=Sum("monto_deducible_total"),
        )
        .filter(cantidad_actual__gt=0)
        .order_by("nombre")
    )

    return render(
        request,
        "donativos/inventario_list.html",
        {"resumen": resumen, "search": search},
    )
