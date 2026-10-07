"""Copia los usuarios del sistema original (tabla `users` de Laravel) a los
usuarios de Django (tabla `accounts_user`), con el MISMO id y la MISMA
contraseña, para que puedan entrar con la clave que ya usaban.

Uso:
    python manage.py importar_usuarios_laravel            -> solo muestra lo que haría
    python manage.py importar_usuarios_laravel --aplicar  -> guarda los cambios

Se puede correr varias veces: los que ya existen en Django solo se
actualizan (nombre, correo y rol) y su contraseña de Django NO se toca.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from accounts.models import User

ROLES_VALIDOS = {valor for valor, _ in User.Role.choices}


def _contrasena_django(hash_laravel):
    """'$2y$12$...' (Laravel) -> 'bcrypt$$2b$12$...' (formato de Django)."""
    if hash_laravel and hash_laravel[:4] in ("$2y$", "$2a$", "$2b$"):
        return "bcrypt$" + "$2b$" + hash_laravel[4:]
    return None  # sin contraseña válida: tendrá que restablecerse


def _fecha(valor):
    """Las fechas de Laravel vienen sin zona horaria; se toman como hora local."""
    if not valor:
        return timezone.now()
    return timezone.make_aware(valor) if timezone.is_naive(valor) else valor


class Command(BaseCommand):
    help = "Copia los usuarios de Laravel (tabla users) a Django con su mismo id y contraseña."

    def add_arguments(self, parser):
        parser.add_argument(
            "--aplicar", action="store_true",
            help="Guarda los cambios. Sin esta opción solo muestra lo que haría.",
        )

    def handle(self, *args, **opts):
        aplicar = opts["aplicar"]

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, username, role, email, password, created_at "
                "FROM users ORDER BY id"
            )
            filas = cursor.fetchall()

        if not filas:
            raise CommandError("La tabla `users` de Laravel está vacía o no existe.")

        plan, conflictos = [], []
        for id_, nombre, usuario, rol, correo, contrasena, creado in filas:
            rol = (rol or "").strip().lower()
            rol = rol if rol in ROLES_VALIDOS else User.Role.LECTOR
            por_id = User.objects.filter(pk=id_).first()
            por_usuario = User.objects.filter(username__iexact=usuario).first()

            if por_id and por_id.username.lower() == usuario.lower():
                accion = "actualizar"
            elif por_id:
                accion = "conflicto"
                conflictos.append(
                    f"El id {id_} ('{usuario}' en Laravel) ya lo tiene '{por_id.username}' en Django."
                )
            elif por_usuario:
                accion = "conflicto"
                conflictos.append(
                    f"'{usuario}' (id {id_} en Laravel) ya existe en Django con otro id ({por_usuario.pk})."
                )
            else:
                accion = "crear"
            plan.append((accion, id_, nombre, usuario, rol, correo, contrasena, creado))

        # --- Reporte ---
        self.stdout.write("")
        self.stdout.write(f"{'ACCIÓN':<12}{'ID':>4}  {'USUARIO':<20}{'ROL':<13}NOMBRE")
        self.stdout.write("-" * 75)
        for accion, id_, nombre, usuario, rol, *_ in plan:
            self.stdout.write(f"{accion.upper():<12}{id_:>4}  {usuario:<20}{rol:<13}{nombre}")
        self.stdout.write("-" * 75)
        crear = sum(1 for p in plan if p[0] == "crear")
        actualizar = sum(1 for p in plan if p[0] == "actualizar")
        self.stdout.write(f"Crear: {crear}   Actualizar: {actualizar}   Conflictos: {len(conflictos)}")

        if conflictos:
            self.stdout.write(self.style.ERROR("\nHay conflictos, no se guardó nada:"))
            for c in conflictos:
                self.stdout.write(self.style.ERROR(f"  - {c}"))
            return

        if not aplicar:
            self.stdout.write(self.style.WARNING(
                "\nModo prueba: no se guardó nada. Para guardar, agrega --aplicar"
            ))
            return

        with transaction.atomic():
            for accion, id_, nombre, usuario, rol, correo, contrasena, creado in plan:
                if accion == "actualizar":
                    User.objects.filter(pk=id_).update(name=nombre, email=correo or "", role=rol)
                    continue
                user = User(
                    id=id_, username=usuario, name=nombre, email=correo or "", role=rol,
                    is_active=True,
                    is_staff=(rol == User.Role.SUPERADMIN),
                    is_superuser=(rol == User.Role.SUPERADMIN),
                    date_joined=_fecha(creado),
                )
                encriptada = _contrasena_django(contrasena)
                if encriptada:
                    user.password = encriptada
                else:
                    user.set_unusable_password()
                user.save()

        self.stdout.write(self.style.SUCCESS(f"\nListo: {crear} creados y {actualizar} actualizados."))