from django import forms

from .models import User

# Mismo estilo de inputs que SettingsModal.tsx
INPUT_CLASSES = (
    "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#353131] "
    "outline-none focus:bg-white focus:ring-2 focus:ring-[#719c44]/20 focus:border-[#719c44] transition-all"
)
PASSWORD_ATTRS = {"class": INPUT_CLASSES, "placeholder": "••••••••"}

# Orden de los roles igual que en el formulario del original
ORDEN_ROLES = ["lector", "editor", "donativos", "asistencial", "admin", "superadmin"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
        }


class ChangePasswordForm(forms.Form):
    """Ambos campos son opcionales: si se dejan en blanco, el perfil se
    guarda sin tocar la contraseña (igual que SettingsModal.tsx, que solo
    llama a changePassword si currentPass y newPass tienen valor)."""

    current_password = forms.CharField(
        label="Contraseña actual", required=False,
        widget=forms.PasswordInput(attrs=PASSWORD_ATTRS),
    )
    new_password = forms.CharField(
        label="Nueva contraseña", required=False, min_length=6,
        widget=forms.PasswordInput(attrs=PASSWORD_ATTRS),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        current = cleaned.get("current_password")
        new = cleaned.get("new_password")
        if current or new:
            if not (current and new):
                raise forms.ValidationError(
                    "Completa contraseña actual y nueva contraseña para cambiarla."
                )
            if not self.user.check_password(current):
                raise forms.ValidationError("La contraseña actual es incorrecta.")
        return cleaned


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}),
    )

    class Meta:
        model = User
        fields = ["name", "username", "email", "role"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "username": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
            "role": forms.RadioSelect(attrs={"class": "hidden"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password"].required = True
        choices = dict(self.fields["role"].choices)
        self.fields["role"].choices = [(r, choices[r]) for r in ORDEN_ROLES if r in choices]

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user