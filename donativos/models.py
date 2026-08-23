from django.db import models
from django.utils import timezone

from donantes.models import Donante


class CatalogoProducto(models.Model):
    """Migrado de create_catalogo_productos_table."""

    nombre = models.CharField(max_length=255, unique=True)
    categoria = models.CharField(max_length=255, blank=True, null=True)
    clave_sat = models.CharField(max_length=255, blank=True, null=True, default="01010101")
    unidad_medida = models.CharField(max_length=255, blank=True, null=True)
    precio_referencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalogo_productos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Donativo(models.Model):
    """Migrado de create_donativos_table y app/Models/Donativo.php."""

    donante = models.ForeignKey(
        Donante, on_delete=models.CASCADE, related_name="donativos", db_column="donante_id"
    )
    fecha_donativo = models.DateField()
    monto_total_deducible = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donativos"
        ordering = ["-fecha_donativo"]

    def __str__(self):
        return f"Donativo #{self.pk} - {self.donante.razon_social}"


class Inventario(models.Model):
    """Migrado de create_inventarios_table + migraciones posteriores y app/Models/Inventario.php."""

    donativo = models.ForeignKey(
        Donativo, on_delete=models.CASCADE, related_name="inventarios", db_column="donativo_id"
    )
    catalogo_producto = models.ForeignKey(
        CatalogoProducto,
        on_delete=models.CASCADE,
        related_name="inventarios",
        db_column="catalogo_producto_id",
        null=True,
        blank=True,
    )
    categoria_producto = models.CharField(max_length=255)
    nombre_producto = models.CharField(max_length=255)
    clave_sat = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=50, default="Nuevo")
    fecha_caducidad = models.DateField(blank=True, null=True)
    modalidad = models.CharField(max_length=255, blank=True, null=True)
    clave_unidad = models.CharField(max_length=255, blank=True, null=True)
    cantidad = models.IntegerField()
    cantidad_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    precio_unitario_deducible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_deducible_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventarios"

    def __str__(self):
        return self.nombre_producto

    @property
    def dias_en_almacen(self):
        fecha_ingreso = self.donativo.fecha_donativo if self.donativo_id else self.created_at.date()
        return (timezone.now().date() - fecha_ingreso).days

    @property
    def semaforo_rotacion(self):
        dias = self.dias_en_almacen
        if dias >= 25:
            return "critico"
        if dias >= 15:
            return "atencion"
        return "fresco"
