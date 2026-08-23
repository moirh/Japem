from django import forms

from .models import Donante

INPUT_CLASSES = (
    "w-full px-3 py-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl "
    "text-japem-dark focus:outline-none focus:bg-white focus:border-japem-green transition"
)


class DonanteForm(forms.ModelForm):
    class Meta:
        model = Donante
        fields = [
            "razon_social",
            "rfc",
            "regimen_fiscal",
            "direccion",
            "cp",
            "contacto",
            "email",
            "telefono",
            "telefono_secundario",
            "estatus",
        ]
        widgets = {"direccion": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {INPUT_CLASSES}".strip()
