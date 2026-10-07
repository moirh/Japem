from decimal import Decimal

from django import forms

from donantes.models import Donante

INPUT_CLASSES = (
    "w-full p-2.5 border border-[#c0c6b6] rounded-lg text-sm bg-white text-[#353131] "
    "focus:ring-2 focus:ring-[#719c44] outline-none transition-all"
)

CATEGORIA_CHOICES = [("", "-- Seleccionar --")] + [
    (c, c) for c in ["Alimentos", "Medicamentos", "Ropa", "Juguetes", "Mantenimiento", "Otros"]
]

ESTADO_CHOICES = [("Nuevo", "Nuevo"), ("Buen Estado", "Buen Estado")]

MODALIDAD_CHOICES = [("", "-- Seleccionar --")] + [
    (m, m)
    for m in [
        "Redondeo directo IAP",
        "Servicio directo Japem",
        "Recurso directo IAP",
        "Especie directo IAP",
        "Talento directo IAP",
        "Redondeo vía Japem",
        "Servicio vía Japem",
        "Recurso vía Japem",
        "Especie vía Japem",
        "Talento vía Japem",
    ]
]

UNIDAD_CHOICES = [
    (u, u)
    for u in [
        "PZA", "KG", "CAJA", "BOLSA", "PAQUETE", "KIT", "TARIMA",
        "PERSONAS", "PROYECTO", "LITRO", "BIDÓN", "ROLLO", "ANIMAL", "PAR",
    ]
]


def _widget(extra_class="", **attrs):
    attrs["class"] = f"{INPUT_CLASSES} {extra_class}".strip()
    return attrs


class DonativoForm(forms.Form):
    donante = forms.ModelChoiceField(
        queryset=Donante.objects.all(),
        label="Seleccionar Donante",
        widget=forms.Select(attrs=_widget()),
    )
    fecha_donativo = forms.DateField(
        label="Fecha Recepción",
        widget=forms.DateInput(attrs=_widget(type="date"), format="%Y-%m-%d"),
    )
    observaciones = forms.CharField(
        label="Notas / Observaciones",
        required=False,
        widget=forms.TextInput(attrs=_widget(placeholder="Ej. Entregado por chofer...")),
    )


class DetalleForm(forms.Form):
    categoria_producto = forms.ChoiceField(
        label="Categoría",
        choices=CATEGORIA_CHOICES,
        widget=forms.Select(attrs=_widget("categoria-input")),
    )
    nombre_producto = forms.CharField(
        label="Producto Específico",
        max_length=255,
        widget=forms.TextInput(
            attrs=_widget(
                "nombre-producto-input",
                list="catalogo-productos",
                placeholder="Buscar o escribir un producto nuevo...",
            )
        ),
    )
    clave_sat = forms.CharField(
        label="Clave SAT",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs=_widget("clave-sat-input", placeholder="Ej. 10101502")),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=ESTADO_CHOICES,
        initial="Nuevo",
        widget=forms.Select(attrs=_widget()),
    )
    fecha_caducidad = forms.DateField(
        label="Caducidad",
        required=False,
        widget=forms.DateInput(attrs=_widget(type="date"), format="%Y-%m-%d"),
    )
    modalidad = forms.ChoiceField(
        label="Modalidad",
        choices=MODALIDAD_CHOICES,
        required=False,
        widget=forms.Select(attrs=_widget()),
    )
    clave_unidad = forms.ChoiceField(
        label="Unidad de Medida",
        choices=UNIDAD_CHOICES,
        initial="PZA",
        widget=forms.Select(attrs=_widget("unidad-input")),
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        widget=forms.NumberInput(attrs=_widget(min=1)),
    )
    precio_unitario_deducible = forms.DecimalField(
        label="P. Unitario Deducible",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0"),
        widget=forms.NumberInput(attrs=_widget(step="0.01")),
    )
    precio_venta_unitario = forms.DecimalField(
        label="P. Venta",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=Decimal("0"),
        widget=forms.NumberInput(attrs=_widget(step="0.01")),
    )


DetalleFormSet = forms.formset_factory(DetalleForm, extra=1, can_delete=False)
