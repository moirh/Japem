from django.db import models

# Los campos de selección múltiple (clasificación, actividad asistencial) se
# guardan como un solo string con este separador, igual que en el frontend
# React original (constante SEPARATOR en IapTable.tsx).
SEPARATOR = "|"


class Iap(models.Model):
    """Institución de Asistencia Privada. Migrado de create_iaps_table y
    app/Models/Iap.php."""

    nombre_iap = models.CharField(max_length=255)
    # La migración de Laravel pone "Activo" por defecto a nivel de columna,
    # pero tanto el formulario de alta como la importación CSV del frontend
    # siempre mandan "Activa" explícitamente — en la práctica ninguna IAP
    # creada por la app termina con "Activo". Se usa aquí el valor que la
    # aplicación realmente escribe, no el default inerte de la migración.
    estatus = models.CharField(max_length=20, default="Activa")
    rubro = models.CharField(max_length=255, blank=True, null=True)
    actividad_asistencial = models.TextField(blank=True, null=True)
    clasificacion = models.CharField(max_length=255, blank=True, null=True)
    tipo_beneficiario = models.CharField(max_length=255, blank=True, null=True)
    personas_beneficiadas = models.IntegerField(default=0)
    necesidad_primaria = models.CharField(max_length=255, blank=True, null=True)
    necesidad_complementaria = models.CharField(max_length=255, blank=True, null=True)
    es_certificada = models.BooleanField(default=False)
    tiene_donataria_autorizada = models.BooleanField(default=False)
    tiene_padron_beneficiarios = models.BooleanField(default=False)
    veces_donado = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "iaps"
        ordering = ["nombre_iap"]
        verbose_name = "IAP"
        verbose_name_plural = "IAPs"

    def save(self, *args, **kwargs):
        self.nombre_iap = self.nombre_iap.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_iap

    @property
    def clasificacion_list(self):
        return [c for c in (self.clasificacion or "").split(SEPARATOR) if c]

    @property
    def actividad_list(self):
        return [a for a in (self.actividad_asistencial or "").split(SEPARATOR) if a]
