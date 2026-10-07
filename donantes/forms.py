from django import forms

from .models import Donante

INPUT_CLASSES = (
    "w-full px-4 py-2.5 border border-[#c0c6b6] rounded-lg text-sm bg-white text-[#353131] "
    "focus:ring-4 focus:ring-[#719c44]/20 focus:border-[#719c44] outline-none transition-all"
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
