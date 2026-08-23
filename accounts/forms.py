from django import forms

from .models import User

INPUT_CLASSES = (
    "w-full px-3 py-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl "
    "text-japem-dark focus:outline-none focus:bg-white focus:border-japem-green transition"
)


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
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}),
    )
    new_password = forms.CharField(
        label="Nueva contraseña", required=False, min_length=6,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}),
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

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
