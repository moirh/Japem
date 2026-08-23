from django.contrib import admin

from .models import CatalogoProducto, Donativo, Inventario


class InventarioInline(admin.TabularInline):
    model = Inventario
    extra = 0


@admin.register(Donativo)
class DonativoAdmin(admin.ModelAdmin):
    list_display = ("id", "donante", "fecha_donativo", "monto_total_deducible")
    list_select_related = ("donante",)
    inlines = [InventarioInline]


@admin.register(CatalogoProducto)
class CatalogoProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "unidad_medida", "precio_referencia")
    search_fields = ("nombre",)


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ("nombre_producto", "donativo", "cantidad", "cantidad_actual", "estado")
    list_filter = ("estado", "modalidad")
    search_fields = ("nombre_producto",)
