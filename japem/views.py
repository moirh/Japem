from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from accounts.permissions import can_publish_avisos
from agenda.models import Acuerdo, Aviso, Recordatorio
from donativos.models import Donativo


@login_required
def home(request):
    """Panel de inicio: equivalente a Home.tsx + DashboardController@index."""
    user = request.user
    today = timezone.now().date()

    # Igual que el original: al entrar se borran los vencidos del usuario.
    Acuerdo.objects.filter(user=user, date__lt=today).delete()
    Recordatorio.objects.filter(user=user, date__lt=today).delete()

    acuerdos = (
        Acuerdo.objects.filter(Q(user=user) | Q(compartidos=user))
        .distinct()
        .order_by("date")
    )
    recordatorios = Recordatorio.objects.filter(user=user).order_by("date")

        # Tarjeta "Donativos del mes": entradas con fecha de donativo en el mes actual
    resumen_mes = Donativo.objects.filter(
        fecha_donativo__year=today.year, fecha_donativo__month=today.month
    ).aggregate(total=Count("id"), monto=Sum("monto_total_deducible"))
    donativos_mes = resumen_mes["total"]
    monto_mes = resumen_mes["monto"] or 0

    calendar_events = [
        {"date": a.date.isoformat(), "title": a.title, "type": "acuerdo"} for a in acuerdos
    ] + [
        {"date": r.date.isoformat(), "title": r.title, "type": "recordatorio"}
        for r in recordatorios
    ]

    todos = sorted(list(acuerdos) + list(recordatorios), key=lambda e: e.date)
    proximo = next((e for e in todos if e.date >= today), todos[0] if todos else None)

    usuarios = User.objects.exclude(pk=user.pk).order_by("name")

    return render(
        request,
        "home.html",
        {
            "acuerdos": acuerdos,
            "recordatorios": recordatorios,
            "donativos_mes": donativos_mes,
            "monto_mes": monto_mes,
            "avisos": Aviso.objects.select_related("autor")[:5],
            "puede_publicar_avisos": can_publish_avisos(user),
            "calendar_events": calendar_events,
            "proximo": proximo,
            "usuarios": usuarios,
            "today": today,
        },
    )
