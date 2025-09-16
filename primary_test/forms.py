from django import forms
from django.core.management.base import BaseCommand
from django.forms import ModelChoiceField, BaseModelFormSet, RadioSelect, ValidationError, modelformset_factory
from django import forms
from diagnostic.models import *
from .models import *

class PrimaryDiagnosticForm(forms.Form):
    def __init__(self, questions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = questions or []
        for idx, q in enumerate(self.questions):
            field_name = f'question_{q.id}'
            choices = [(opt.id, opt.option_text) for opt in q.options.all()]
            self.fields[field_name] = forms.ChoiceField(
                label=q.text,
                widget=forms.RadioSelect(attrs={'class': 'custom-control-input'}),
                choices=choices,
                required=True
            )

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

class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['question', 'option_text', 'is_selected']
        widgets = {
            'is_selected': forms.CheckboxInput(),
        }