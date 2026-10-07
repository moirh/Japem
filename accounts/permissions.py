"""Reglas de permisos por rol, replicando los `allowedRoles`/`isReadOnly`
que el frontend original calculaba en cada componente (DonantesTable,
DonativosTable, EntregasView, Entrega, IapTable). En Django se aplican en
dos puntos: se ocultan los controles de edición en el template (igual que
antes), y además se bloquea la acción en el servidor si alguien la invoca
de todos modos — el frontend original solo hacía lo primero."""

DONATIVOS_ROLES = {"admin", "superadmin", "editor", "donativos"}
IAP_ROLES = {"admin", "superadmin", "editor", "asistencial"}
AVISOS_ROLES = {"admin", "superadmin"}

def can_edit_donativos(user):
    """Donantes, Donativos, Distribución y Entregas: mismos roles que
    `allowedRoles` en DonantesTable/DonativosTable/EntregasView/Entrega.tsx."""
    return user.is_authenticated and user.role in DONATIVOS_ROLES


def can_edit_iaps(user):
    """IAPs: mismos roles que `allowedRoles` en IapTable.tsx."""
    return user.is_authenticated and user.role in IAP_ROLES

def can_publish_avisos(user):
    """Avisos de la Semana (Inicio): solo admin y superadmin publican."""
    return user.is_authenticated and user.role in AVISOS_ROLES
