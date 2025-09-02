from django.db import models
from django.contrib.auth.models import User
from .models import *

class Question(models.Model):
    text = models.TextField()
    test_type = models.CharField(
        max_length=20,
        choices=[
            ('primary', 'Первичная диагностика'),
            ('interim', 'Промежуточная диагностика'),
            ('final', 'Итоговая диагностика')
        ]
    )

    def __str__(self):
        return self.text[:50]

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255, verbose_name="Вариант ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ?")

    def __str__(self):
        return self.option_text



