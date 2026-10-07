from django import forms
from django.core.files.uploadedfile import UploadedFile

from .models import Aviso

INPUT_CLASSES = (
    "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#353131] "
    "outline-none focus:bg-white focus:ring-2 focus:ring-[#719c44]/20 focus:border-[#719c44] transition-all"
)
MAX_IMAGEN_MB = 5


class AvisoForm(forms.ModelForm):
    """Formulario de los Avisos de la Semana (Inicio)."""

    quitar_imagen = forms.BooleanField(required=False)

    class Meta:
        model = Aviso
        fields = ["categoria", "titulo", "fecha", "contenido", "imagen"]
        widgets = {
            "categoria": forms.RadioSelect(attrs={"class": "hidden"}),
            "titulo": forms.TextInput(attrs={
                "class": INPUT_CLASSES, "placeholder": "Ej. Colecta de invierno 2026",
            }),
            "fecha": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}, format="%Y-%m-%d"),
            "contenido": forms.Textarea(attrs={
                "class": INPUT_CLASSES + " resize-none", "rows": 5,
                "placeholder": "Escribe aquí la noticia, evento o aviso...",
            }),
        }

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if isinstance(imagen, UploadedFile) and imagen.size > MAX_IMAGEN_MB * 1024 * 1024:
            raise forms.ValidationError(f"La imagen no debe pesar más de {MAX_IMAGEN_MB} MB.")
        return imagen