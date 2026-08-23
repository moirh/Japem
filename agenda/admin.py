from django.contrib import admin

from .models import Acuerdo, Recordatorio


@admin.register(Acuerdo)
class AcuerdoAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "date", "done")
    list_filter = ("done",)
    search_fields = ("title",)


@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "date", "done")
    list_filter = ("done",)
    search_fields = ("title",)
