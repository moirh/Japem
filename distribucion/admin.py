from django.contrib import admin

from .models import Asignacion, DetalleAsignacion


class DetalleAsignacionInline(admin.TabularInline):
    model = DetalleAsignacion
    extra = 0


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ("id", "iap", "estatus", "fecha_asignacion", "fecha_entrega_real")
    list_filter = ("estatus",)
    inlines = [DetalleAsignacionInline]
