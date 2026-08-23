from django.db import models


class Donante(models.Model):
    """Migrado de database/migrations/..._create_donantes_table.php y app/Models/Donante.php."""

    class Estatus(models.TextChoices):
        PERMANENTE = "Permanente", "Permanente"
        EVENTUAL = "Eventual", "Eventual"
        UNICA_VEZ = "Unica vez", "Única vez"

    razon_social = models.CharField(max_length=255)
    rfc = models.CharField(max_length=255, blank=True, null=True)
    regimen_fiscal = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    cp = models.CharField(max_length=255, blank=True, null=True)
    contacto = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=255, blank=True, null=True)
    telefono_secundario = models.CharField(max_length=20, blank=True, null=True)
    estatus = models.CharField(max_length=20, choices=Estatus.choices, default=Estatus.EVENTUAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donantes"
        ordering = ["razon_social"]

    def save(self, *args, **kwargs):
        # Los mutadores de Eloquent guardaban estos campos en mayúsculas.
        self.razon_social = self.razon_social.upper()
        if self.rfc:
            self.rfc = self.rfc.upper()
        if self.direccion:
            self.direccion = self.direccion.upper()
        self.contacto = self.contacto.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.razon_social
