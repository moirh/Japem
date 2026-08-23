from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario de la aplicación. Migrado de app/Models/User.php (Laravel)."""

    class Role(models.TextChoices):
        SUPERADMIN = "superadmin", "Superadmin"
        ADMIN = "admin", "Admin"
        DONATIVOS = "donativos", "Donativos"
        ASISTENCIAL = "asistencial", "Asistencial"
        EDITOR = "editor", "Editor"
        LECTOR = "lector", "Lector"

    name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EDITOR)

    def __str__(self):
        return self.username
