from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import *

class RegistrationForm(forms.Form):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label="Имя", error_messages={"required": ""})
    last_name = forms.CharField(label="Фамилия", error_messages={"required": ""})
    school = forms.ModelChoiceField(queryset=School.objects.all(), empty_label=None, label="Школа", error_messages={"required": ""})
    class_level = forms.ModelChoiceField(queryset=ClassLevel.objects.all(), empty_label=None, label="Класс", error_messages={"required": ""})
    class_letter = forms.CharField(max_length=1, label="Буква класса", error_messages={"required": ""})

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже занят.")
        return email

    def save(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data['email']
        first_name = cleaned_data['first_name']
        last_name = cleaned_data['last_name']
        school = cleaned_data['school']
        class_level = cleaned_data['class_level']
        class_letter = cleaned_data['class_letter']

        # Создаем активного пользователя без пароля
        new_user = User.objects.create_user(username=email, email=email, is_active=True)
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        # Создаем профиль пользователя
        profile = UserProfile.objects.create(
            user=new_user,
            first_name=first_name,
            last_name=last_name,
            school=school,
            class_level=class_level,
            class_letter=class_letter
        )

        return new_user

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Почта", widget=forms.EmailInput(attrs={'placeholder': 'Введите вашу почту'}))
    
