from django.conf import settings
from django.db import models


class Acuerdo(models.Model):
    """Migrado de create_acuerdos_table + add_done_to_acuerdos_table +
    create_acuerdo_user_table y app/Models/Acuerdo.php.

    A diferencia de Recordatorio, un acuerdo se puede compartir con otros
    usuarios (tabla pivote acuerdo_user) que también lo verán en su panel,
    aunque solo el dueño (`user`) puede editarlo/eliminarlo."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="acuerdos",
        db_column="user_id",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    done = models.BooleanField(default=False)
    compartidos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="AcuerdoUser",
        related_name="acuerdos_compartidos",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acuerdos"
        ordering = ["date"]

    def __str__(self):
        return self.title


class AcuerdoUser(models.Model):
    """Tabla pivote acuerdo_user: con quién se comparte un Acuerdo."""

    acuerdo = models.ForeignKey(Acuerdo, on_delete=models.CASCADE, db_column="acuerdo_id")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acuerdo_user"


class Recordatorio(models.Model):
    """Migrado de create_recordatorios_table y app/Models/Recordatorio.php.
    Personal: no se comparte con otros usuarios."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recordatorios",
        db_column="user_id",
    )
    title = models.CharField(max_length=255)
    date = models.DateField()
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recordatorios"
        ordering = ["date"]

    def __str__(self):
        return self.title
