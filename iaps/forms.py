import re

from django import forms

from .models import SEPARATOR, Iap

INPUT_CLASSES = (
    "w-full px-3 py-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl "
    "text-japem-dark focus:outline-none focus:bg-white focus:border-japem-green transition"
)

ESTATUS_CHOICES = [
    ("Activa", "Activa"),
    ("Inactiva", "Inactiva"),
    ("Suspendida", "Suspendida"),
    ("En Proceso", "En Proceso"),
]

RUBRO_CHOICES = [
    ("Ancianos", "Ancianos"),
    ("Desarrollo Social", "Desarrollo Social"),
    ("Educación", "Educación"),
    ("Médico", "Médico"),
    ("Niñas, Niños y Adolescentes", "Niñas, Niños y Adolescentes"),
    ("Personas con Discapacidad", "Personas con Discapacidad"),
    ("No Proporcionado", "No Proporcionado"),
]

CLASIFICACIONES = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "C4", "D"]

ACTIVIDADES = [
    "ESTABLECIMIENTO DE ASISTENCIA SOCIAL PERMAMENTE",
    "AGRICULTURA SOSTENIBLE",
    "ALBERGUE TEMPORAL",
    "BANCO DE ALIMENTOS",
    "CENTRO DE APOYO A LOCUTORES",
    "CENTRO DE ATENCIÓN A VÍCTIMAS",
    "CENTRO DE ATENCIÓN SOCIAL COMUNITARIA",
    "CENTRO DE DESARROLLO COMUNITARIO",
    "ENTREGA DE BECAS",
    "ENTREGA DE DESPENSAS",
    "GRUPO DE AYUDA MUTUA",
    "PREVENCIÓN DEL CONSUMO NO TERAPÉUTICO DE SUSTANCIAS PSICOACTIVAS",
    "PROGRAMAS DE VIVIENDA Y MEJORAMIENTO URBANO",
    "REFUGIO DE SERES SINTIENTES",
    "SEGUNDO PISO",
    "TALLER ARTÍSTICO Y CULTURAL",
    "TALLER DE CAPACITACIÓN LABORAL",
    "TALLERES DE FORTALECIMIENTO DE LA AUTONOMÍA ECONÓMICA DE LAS MUJERES",
    "TALLERES DE ORIENTACIÓN SOCIAL",
    "TALLERES SOBRE EMPRENDIMIENTO SOCIAL",
    "TERAPIA PSICOLÓGICA",
    "ESCUELA DE EDUCACIÓN PRESCOLAR",
    "ESCUELA DE EDUCACIÓN SUPERIOR",
    "COMUNIDAD EDUCATIVA",
    "ESCUELA DE EDUCACIÓN BÁSICA",
    "HOSPICIOS Y CUIDADOS PALIATIVOS",
    "ATENCIÓN MÉDICA DE ESPECILIDAD",
    "CENTRO DE ATENCIÓN INTEGRAL PARA ENFERMEDAD RENAL CRÓNICA",
    "CLÍNICA Y DISPENSARIO MÉDICO",
    "CONSULTORIO MÉDICO",
    "DISPENSARIO MÉDICO",
    "HOSPITAL DE SEGUNDO NIVEL",
    "PROMOCIÓN A LA SALUD",
    "SERVICIOS DE MEDICINA ALTERNATIVA",
    "CENTRO DE ATENCIÓN PARA ADICCIONES",
    "CASA CUNA",
    "CASA HOGAR",
    "INTERNADO",
    "COMEDOR COMUNITARIO",
    "COMEDOR INFANTIL",
    "ATENCIÓN INSTITUCIONAL",
    "LUDOTECA PARA NIÑOS CON CÁNCER",
    "REFUGIO PARA MUJERES VICTIMAS DE VIOLENCIA",
    "SALUD VISUAL",
    "TALLER DE MÚSICA",
    "TALLER PREVENCIÓN DE VIOLENCIA",
    "TALLER PREVENCIÓN DE VIOLENCIA Y SALUD",
    "APOYOS Y AYUDAS TÉCNICAS PARA LA INCLUSIÓN",
    "CENTRO DE REHABILITACIÓN",
    "CENTROS DE INCLUSIÓN EDUCATIVA O LABORAL",
    "ESTABLECIMIENTO DE ASISTENCIA SOCIAL PERMAMENTE PARA PERSONAS CON DISCAPACIDAD",
    "TERAPIAS DE REHABILITACIÓN",
    "NO PROPORCIONADO",
]


def _parse_poblacion(texto):
    fijos = re.search(r"Fijos:\s*(\d+)", texto)
    temp = re.search(r"Temporales:\s*(\d+)", texto)
    flot = re.search(r"Flotantes:\s*(\d+)", texto)
    return (
        int(fijos.group(1)) if fijos else None,
        int(temp.group(1)) if temp else None,
        int(flot.group(1)) if flot else None,
    )


class PipeMultipleChoiceField(forms.MultipleChoiceField):
    """Selección múltiple que se guarda/lee como un solo string separado por
    '|', igual que `toggleMultiSelect` en el frontend original."""

    def prepare_value(self, value):
        if isinstance(value, str):
            return value.split(SEPARATOR) if value else []
        return value or []

    def clean(self, value):
        cleaned = super().clean(value)
        return SEPARATOR.join(cleaned)


class IapForm(forms.ModelForm):
    clasificacion = PipeMultipleChoiceField(
        choices=[(c, c) for c in CLASIFICACIONES],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Clasificación (múltiple)",
    )
    actividad_asistencial = PipeMultipleChoiceField(
        choices=[(a, a) for a in ACTIVIDADES],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Actividades específicas (múltiple)",
    )
    cantidad_fijos = forms.IntegerField(
        label="Cant. Fijos", required=False, min_value=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES}),
    )
    cantidad_temporales = forms.IntegerField(
        label="Cant. Temporales", required=False, min_value=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES}),
    )
    cantidad_flotantes = forms.IntegerField(
        label="Cant. Flotantes", required=False, min_value=0,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES}),
    )

    class Meta:
        model = Iap
        fields = [
            "nombre_iap",
            "estatus",
            "clasificacion",
            "rubro",
            "actividad_asistencial",
            "necesidad_complementaria",
            "es_certificada",
            "tiene_donataria_autorizada",
            "tiene_padron_beneficiarios",
        ]
        widgets = {
            "nombre_iap": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "estatus": forms.Select(choices=ESTATUS_CHOICES, attrs={"class": INPUT_CLASSES}),
            "rubro": forms.Select(choices=RUBRO_CHOICES, attrs={"class": INPUT_CLASSES}),
            "necesidad_complementaria": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "Ej. Juguetes, ropa..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            fijos, temp, flot = _parse_poblacion(self.instance.tipo_beneficiario or "")
            self.fields["cantidad_fijos"].initial = fijos
            self.fields["cantidad_temporales"].initial = temp
            self.fields["cantidad_flotantes"].initial = flot

    def save(self, commit=True):
        iap = super().save(commit=False)

        detalles = []
        total = 0
        for etiqueta, campo in [
            ("Fijos", "cantidad_fijos"),
            ("Temporales", "cantidad_temporales"),
            ("Flotantes", "cantidad_flotantes"),
        ]:
            valor = self.cleaned_data.get(campo) or 0
            if valor > 0:
                detalles.append(f"{etiqueta}: {valor}")
                total += valor

        iap.tipo_beneficiario = SEPARATOR.join(detalles)
        iap.personas_beneficiadas = total

        if commit:
            iap.save()
        return iap
