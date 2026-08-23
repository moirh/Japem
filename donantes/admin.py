from django.contrib import admin

from .models import Donante


@admin.register(Donante)
class DonanteAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rfc", "contacto", "estatus")
    search_fields = ("razon_social", "rfc", "contacto")
    list_filter = ("estatus",)
