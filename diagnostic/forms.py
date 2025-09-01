from django import forms
from django.core.management.base import BaseCommand
# Импортируем модели
from .models import *

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(label="Электронная почта", error_messages={"required": ("")},)
    
    first_name = forms.CharField(label="Имя",error_messages={"required": ("")},)
    last_name = forms.CharField(label="Фамилия",error_messages={"required": ("")},)
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        empty_label=None,
        label="Школа",
        error_messages={"required": ("")},
    )
    class_level = forms.ModelChoiceField(
        queryset=ClassLevel.objects.all(),
        empty_label=None,
        label="Класс",
        error_messages={"required": ("")},
    )
    class_letter = forms.CharField(
        max_length=1,
        label="Буква класса",
        error_messages={"required": ("")},
    )

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'school', 'class_level', 'class_letter')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Русификация подписей полей
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['school'].label = 'Школа'
        self.fields['class_level'].label = 'Класс'
        self.fields['class_letter'].label = 'Буква класса'

        # Присваиваем фильтры и метки полей
        self.fields['school'].queryset = School.objects.all()
        self.fields['class_level'].queryset = ClassLevel.objects.all()

    def clean_class_letter(self):
        class_letter = self.cleaned_data.get('class_letter', '').strip()
        if not class_letter or len(class_letter) > 1 or not class_letter.isalpha():
            raise forms.ValidationError('Необходимо ввести одну букву.')
        return class_letter

    def update_querysets(self):
        # Установим фильтрацию только после полной инициализации формы
        self.fields['school'].queryset = School.objects.all()
        self.fields['class_level'].queryset = ClassLevel.objects.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Опционально можем обновить дополнительную логику
        if commit:
            instance.save()
        return instance
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email


class TestForm(forms.Form):
    """
    Форма отображения вопросов и вариантов ответов для тестирования.
    Для каждого вопроса создается поле выбора варианта ответа.
    """

    def __init__(self, *args, **kwargs):
        self.questions = kwargs.pop('questions')
        super(TestForm, self).__init__(*args, **kwargs)

        # Добавляем поля формы динамически исходя из переданных вопросов
        for question in self.questions:
            choices = [(option.id, option.text) for option in question.answer_options.all()]
            field_name = f'question_{question.id}'
            self.fields[field_name] = forms.ChoiceField(
                label=question.text,
                widget=forms.RadioSelect,
                choices=choices,
                required=True
            )