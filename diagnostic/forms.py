from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Подтверждение пароля'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают!")
        return confirm_password

class LoginForm(forms.Form):
    username = forms.CharField(label="Имя пользователя")
    password = forms.CharField(widget=forms.PasswordInput(), label="Пароль")

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user', )