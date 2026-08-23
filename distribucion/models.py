from django.db import models

from donativos.models import Inventario
from iaps.models import Iap


class Asignacion(models.Model):
    """Cabecera de una distribución a una IAP. Migrado de
    create_asignaciones_tables + add_delivery_cols_to_asignaciones y
    app/Models/Asignacion.php."""

    class Estatus(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ENTREGADO = "entregado", "Entregado"

    iap = models.ForeignKey(
        Iap, on_delete=models.CASCADE, related_name="asignaciones", db_column="iap_id"
    )
    estatus = models.CharField(
        max_length=20, choices=Estatus.choices, default=Estatus.PENDIENTE
    )
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    responsable_entrega = models.CharField(max_length=255, blank=True, null=True)
    lugar_entrega = models.CharField(max_length=255, blank=True, null=True)
    fecha_entrega_real = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "asignaciones"
        ordering = ["-id"]

    def __str__(self):
        return f"Asignación #{self.pk} - {self.iap.nombre_iap}"


class DetalleAsignacion(models.Model):
    """Producto asignado dentro de una Asignacion. Migrado de
    create_asignaciones_tables + add_tracking_columns_to_detalle_asignaciones
    y app/Models/DetalleAsignacion.php.

    Nota: la tabla original también tiene columnas `iap_id` y
    `producto_nombre` (agregadas en una migración posterior) que ningún
    controlador activo llega a leer ni escribir; se omiten aquí a propósito
    por ser datos muertos."""

    asignacion = models.ForeignKey(
        Asignacion,
        on_delete=models.CASCADE,
        related_name="detalles",
        db_column="asignacion_id",
    )
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name="detalle_asignaciones",
        db_column="inventario_id",
    )
    cantidad = models.IntegerField()
    estatus = models.CharField(max_length=20, default="pendiente")
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "detalle_asignaciones"

    def __str__(self):
        return f"{self.inventario.nombre_producto} x{self.cantidad}"
