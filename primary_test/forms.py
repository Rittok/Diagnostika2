from django import forms
from django.core.management.base import BaseCommand
from django.forms import ModelChoiceField, BaseModelFormSet, modelformset_factory
# Импортируем модели
from .models import *

class AnswerForm(ModelChoiceField):
    def clean(self, value):
        cleaned_value = super().clean(value)
        try:
            return AnswerOption.objects.get(id=value)
        except AnswerOption.DoesNotExist:
            raise ValidationError("Некорректный ответ.")

class TestForm(BaseModelFormSet):
    def __init__(self, data=None, files=None, queryset=None, prefix=None, initial=None, questions=None):
        super().__init__(data=data, files=files, queryset=queryset, prefix=prefix, initial=initial)
        if questions:
            self.form_kwargs.update({'questions': questions})

    @property
    def empty_form(self):
        if hasattr(self, '_empty_form'):
            return self._empty_form
        self._empty_form = self.form_class(**self.get_empty_form_kwargs())
        return self._empty_form

    def add_fields(self, form, index):
        question = self.form_kwargs['questions'][index]
        form.fields[f'q_{question.id}'] = AnswerForm(
            widget=RadioSelect(),
            queryset=AnswerOption.objects.filter(question=question),
            required=True,
            label=question.text
        )

TestFormSet = modelformset_factory(AnswerOption, fields=(), extra=0, can_delete=False, formset=TestForm)