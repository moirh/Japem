from django.contrib import admin

from .models import Iap


@admin.register(Iap)
class IapAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_iap",
        "estatus",
        "clasificacion",
        "es_certificada",
        "tiene_donataria_autorizada",
        "tiene_padron_beneficiarios",
        "veces_donado",
    )
    list_filter = ("estatus", "clasificacion", "es_certificada")
    search_fields = ("nombre_iap",)
