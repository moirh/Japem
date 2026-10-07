"""Context processors globales de JAPEM.

header_notifications: notificaciones de la campana del encabezado.
Migrado de cargarNotificaciones() en Header.tsx:
  1. Rotación crítica (danger): productos con 25+ días en almacén.
  2. Recordatorios pendientes (warning) del usuario.
  3. Acuerdos activos (info): propios y compartidos conmigo.
Ordenadas por severidad: danger -> warning -> info.
"""
from datetime import timedelta

from django.db.models import Min, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateformat import format as date_format


def _fecha_corta(fecha):
    # Igual que toLocaleDateString("es-MX", {day: "numeric", month: "short"}) -> "8 oct"
    return date_format(fecha, "j b")


def header_notifications(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    # Las peticiones htmx devuelven fragmentos, no usan el encabezado
    if getattr(request, "htmx", False):
        return {}

    from agenda.models import Acuerdo, Recordatorio
    from donativos.models import Inventario

    hoy = timezone.localdate()
    notificaciones = []

    # 1. Rotación crítica (lote más antiguo con stock, agrupado por producto)
    criticos = (
        Inventario.objects.filter(
            cantidad_actual__gt=0,
            donativo__fecha_donativo__lte=hoy - timedelta(days=25),
        )
        .annotate(nombre=Coalesce("catalogo_producto__nombre", "nombre_producto"))
        .values("nombre")
        .annotate(fecha_ingreso=Min("donativo__fecha_donativo"), stock=Sum("cantidad_actual"))
        .order_by("fecha_ingreso")
    )
    for item in criticos:
        dias = (hoy - item["fecha_ingreso"]).days
        notificaciones.append({
            "type": "danger",
            "icon": "package",
            "title": f"Rotación Crítica: {item['nombre']}",
            "content": f"Lleva {dias} días en almacén. Requiere salida prioritaria.",
            "time": "Alerta Stock",
        })

    # 2. Recordatorios pendientes
    for rec in Recordatorio.objects.filter(user=user, done=False, date__gte=hoy).order_by("date"):
        fecha = _fecha_corta(rec.date)
        notificaciones.append({
            "type": "warning",
            "icon": "calendar",
            "title": f"Recordatorio: {rec.title}",
            "content": f"Tienes este pendiente programado para el {fecha}.",
            "time": fecha,
        })

    # 3. Acuerdos activos (míos o compartidos conmigo)
    acuerdos = (
        Acuerdo.objects.filter(Q(user=user) | Q(compartidos=user), date__gte=hoy)
        .distinct()
        .order_by("date")
    )
    for acu in acuerdos:
        notificaciones.append({
            "type": "info",
            "icon": "calendar",
            "title": f"Acuerdo: {acu.title}",
            "content": acu.description or "Sin descripción adicional.",
            "time": f"Vence: {_fecha_corta(acu.date)}",
        })

    return {"header_notifications": notificaciones}