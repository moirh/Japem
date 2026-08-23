from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from agenda.models import Acuerdo, Recordatorio
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

    donativos_mes = Donativo.objects.filter(
        created_at__year=today.year, created_at__month=today.month
    ).count()

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
            "calendar_events": calendar_events,
            "proximo": proximo,
            "usuarios": usuarios,
            "today": today,
        },
    )
